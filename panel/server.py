#!/usr/bin/env python3
"""
MYTHOS Lounge — control panel backend (stdlib only).

Serves the panel UI and manages agent "launches":
  - connectors  : editable command templates = "hook any AI"
  - launch      : spawn a connector command (target + prompt) as a tracked process
  - monitor     : stream each launch's log, halt it, or inject an interrupt prompt

Processes are spawned in their own session (process group) so halt kills children too.
Everything is local: binds 127.0.0.1 only. No external deps, no database — logs + json on disk.
"""
import argparse, json, os, re, shlex, signal, socket, subprocess, threading, time, uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.expanduser("~/.mythos-lounge")
LOGS = os.path.join(BASE, "logs")
CONNECTORS_FILE = os.path.join(BASE, "connectors.json")
LAUNCHES_FILE = os.path.join(BASE, "launches.json")

os.makedirs(LOGS, exist_ok=True)

# launch_id -> {meta..., "proc": Popen|None, "log": path, "stdin_ok": bool}
LAUNCHES = {}
LOCK = threading.Lock()

KNOWN_CLIS = ["claude", "grok", "kimi", "aider", "llm", "ollama", "codex", "gemini"]

DEFAULT_CONNECTORS = [
    {
        "name": "claude-code · one-shot (-p)",
        "command": "claude -p {prompt}",
        "cwd": "~/targets/{name}",
    },
    {
        "name": "claude-code · interactive",
        "command": "claude",
        "cwd": "~/targets/{name}",
    },
]


def load_connectors():
    if os.path.exists(CONNECTORS_FILE):
        try:
            with open(CONNECTORS_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    save_connectors(DEFAULT_CONNECTORS)
    return list(DEFAULT_CONNECTORS)


def save_connectors(conns):
    with open(CONNECTORS_FILE, "w") as f:
        json.dump(conns, f, indent=2)


def detect_clis():
    found = []
    path_dirs = os.environ.get("PATH", "").split(os.pathsep)
    for cli in KNOWN_CLIS:
        for d in path_dirs:
            p = os.path.join(d, cli)
            if os.path.isfile(p) and os.access(p, os.X_OK):
                found.append(cli)
                break
    return found


def expand(path, name):
    path = (path or "~").replace("{name}", name or "")
    return os.path.abspath(os.path.expanduser(path))


# ---- authorized scope (per target) --------------------------------------
# Scope is the one hard gate in the doctrine: the agent may only test what is
# written in ~/targets/<name>/STATE/SCOPE.md. The panel reads/writes that file
# so the authorization is explicit in the UI before anything launches.
def scope_path(name):
    name = (name or "").strip()
    if not name:
        return None
    root = os.path.abspath(os.path.expanduser(os.path.join("~/targets", name)))
    return os.path.join(root, "STATE", "SCOPE.md")


def read_scope(name):
    p = scope_path(name)
    if not p or not os.path.exists(p):
        return ""
    try:
        with open(p, encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


def write_scope(name, text):
    p = scope_path(name)
    if not p:
        return None
    os.makedirs(os.path.dirname(p), exist_ok=True)
    text = text or ""
    with open(p, "w", encoding="utf-8") as f:
        f.write(text if text.endswith("\n") else text + "\n")
    return p


# auto-approve: the operator only runs this against their own assets, so a
# target put into Launch is treated as pre-approved. If it has no real scope
# yet (empty, or still the unfilled newtarget template), write the self-owned
# default so it is "allowed" instantly.
SERVER_DEFAULT_SCOPE = (
    "# AUTHORIZED SCOPE — self-owned assets only (auto-approved on launch)\n"
    "# Operator attests ownership of this target. Full-depth testing of MY OWN\n"
    "# asset. Anything I do not own is NEVER in scope.\n\n"
    "IN SCOPE: my domains/subdomains/paths and every environment I run\n"
    "  (local/dev/staging/prod), my APIs/services/auth/sessions/tokens, the\n"
    "  infrastructure I administer, localhost/*.test, and my own test accounts.\n"
    "VULN CLASSES: all of them — authz/IDOR/BOLA, injection, XSS/CSRF, SSRF/RCE,\n"
    "  logic/race/parser-diff, infra & secret disclosure. Chain to the ceiling.\n"
    "OUT OF SCOPE (hard): anything I do NOT own, shared/multi-tenant systems I am\n"
    "  not the sole tenant of, destructive actions on real production data.\n"
    "RULES: probe not assert; one minimal PoC per finding; never leave a\n"
    "  destructive primitive armed.\n"
)


def is_placeholder_scope(text):
    t = (text or "")
    if not t.strip():
        return True
    return ("- [ ]" in t) or ("What's not written here is not scoped" in t)


def ensure_scope(name, target=None):
    """Return the scope path, writing the self-owned default if none real yet.
    When a concrete target (URL/host) is given, name it in the scope so the
    agent has an actual in-scope asset to ground on (not just a generic scope)."""
    p = scope_path(name)
    if not p:
        return None
    if is_placeholder_scope(read_scope(name)):
        txt = SERVER_DEFAULT_SCOPE
        t = (target or "").strip()
        if t:
            txt = ("# PRIMARY TARGET (self-owned): " + t + "\n"
                   "# In scope: this asset and all its subdomains, paths and environments.\n\n") + txt
        return write_scope(name, txt)
    return p


# ======================================================================
# MYTHOS project integration — targets, STATE files, file tree, journal,
# doctrine, and project actions (newtarget/mtarget/resume/lounge).
# All file access is sandboxed to ALLOWED_ROOTS (realpath-checked) so the
# panel can never read/write outside the project trees.
# ======================================================================
HOME_DIR = os.path.expanduser("~")
TARGETS_DIR = os.path.realpath(os.path.join(HOME_DIR, "targets"))
MYTHOS_BIN = os.path.join(HOME_DIR, ".kimi-code", "mythos")
LOUNGE_DIR = os.path.join(TARGETS_DIR, "_shared", "lounge")
ACTIVE_FILE = os.path.join(MYTHOS_BIN, "active_target")
STATE_FILES = ["SCOPE.md", "TARGET_MODEL.md", "LEADS.md", "CHAIN_LEDGER.md",
               "GAP_PLAN.md", "DEADENDS.md", "RESUME.md", "CHECKPOINT.md",
               "INTERRUPT.md", "JOURNAL.ndjson"]
TARGET_SUBDIRS = ["STATE", "notes", "evidence", "recon", "results", "reports", "scripts"]

ALLOWED_ROOTS = [os.path.realpath(os.path.expanduser(p)) for p in (
    TARGETS_DIR,
    os.path.join(HOME_DIR, ".claude"),
    os.path.join(HOME_DIR, ".kimi-code"),
    os.path.join(HOME_DIR, ".grok"),
)]

DOCTRINE_FILES = [
    ("core contract (CLAUDE.md)", "~/.claude/CLAUDE.md"),
    ("hooks settings.json",       "~/.claude/settings.json"),
    ("CRITICAL_HUNTER",           "~/.grok/rules/CRITICAL_HUNTER.md"),
    ("HUNTER_V5",                 "~/.grok/rules/HUNTER_V5.md"),
    ("TRAPS",                     "~/targets/_shared/TRAPS.md"),
    ("TOOLS",                     "~/targets/_shared/TOOLS.md"),
    ("source-first method",       "~/targets/_shared/HUNTING_METHODOLOGY_SOURCE_FIRST.md"),
]
MAX_READ = 1024 * 1024  # 1 MiB cap on file reads


def safe_path(p):
    """Realpath of p, but only if it lands inside an allowed project root."""
    if not p:
        return None
    rp = os.path.realpath(os.path.expanduser(p))
    for root in ALLOWED_ROOTS:
        if rp == root or rp.startswith(root + os.sep):
            return rp
    return None


def list_targets():
    out = []
    try:
        for n in sorted(os.listdir(TARGETS_DIR)):
            if n == "_shared":
                continue
            if os.path.isdir(os.path.join(TARGETS_DIR, n)):
                out.append(n)
    except Exception:
        pass
    return out


def active_target():
    try:
        with open(ACTIVE_FILE) as f:
            return f.read().strip()
    except Exception:
        return ""


def read_file_api(p):
    rp = safe_path(p)
    if not rp or not os.path.isfile(rp):
        return {"error": "not found or outside project"}, 404
    try:
        size = os.path.getsize(rp)
        with open(rp, encoding="utf-8", errors="replace") as f:
            data = f.read(MAX_READ)
        return {"path": rp, "content": data,
                "truncated": size > MAX_READ, "size": size}, 200
    except Exception as e:
        return {"error": str(e)}, 500


def write_file_api(p, content):
    rp = safe_path(p)
    if not rp:
        return {"error": "path outside project — refused"}, 403
    if os.path.isdir(rp):
        return {"error": "is a directory"}, 400
    try:
        os.makedirs(os.path.dirname(rp), exist_ok=True)
        with open(rp, "w", encoding="utf-8") as f:
            f.write(content if content is not None else "")
        return {"ok": True, "path": rp}, 200
    except Exception as e:
        return {"error": str(e)}, 500


def list_tree(p):
    rp = safe_path(p)
    if not rp or not os.path.isdir(rp):
        return {"error": "not a dir or outside project"}, 404
    entries = []
    try:
        for n in sorted(os.listdir(rp)):
            full = os.path.join(rp, n)
            d = os.path.isdir(full)
            entries.append({"name": n, "path": full, "dir": d,
                            "size": 0 if d else os.path.getsize(full)})
    except Exception as e:
        return {"error": str(e)}, 500
    entries.sort(key=lambda e: (not e["dir"], e["name"].lower()))
    return {"path": rp, "entries": entries}, 200


def read_journal(target, n=300):
    if not target:
        return {"lines": []}, 200
    p = os.path.join(TARGETS_DIR, target, "STATE", "JOURNAL.ndjson")
    if not os.path.isfile(p):
        return {"lines": [], "note": "no journal yet"}, 200
    try:
        with open(p, encoding="utf-8", errors="replace") as f:
            raw = f.readlines()[-n:]
        out = []
        for ln in raw:
            ln = ln.strip()
            if not ln:
                continue
            try:
                out.append(json.loads(ln))
            except Exception:
                out.append({"raw": ln})
        return {"lines": out}, 200
    except Exception as e:
        return {"error": str(e)}, 500


# ---- leads / findings (parsed from LEADS.md + CHAIN_LEDGER.md) -----------
STATUS_RE = re.compile(r"\[STATUS:\s*([^\]]+)\]", re.I)
SEV_RE = re.compile(r"\b(CRITICAL|HIGH|MEDIUM|MED|LOW|INFO|INFORMATIONAL)\b")


def _status_class(s):
    s = (s or "").upper()
    if "NEGATIVE" in s or "DEAD" in s:
        return "dead"
    if "BLOCK" in s:
        return "blocked"
    if "DONE" in s or "PROVEN" in s or "CONFIRM" in s:
        return "confirmed"
    if "TODO" in s or "WIP" in s or "TEST" in s:
        return "testing"
    if "PARK" in s:
        return "parked"
    return "open"


def _clean_row(st):
    cells = [c.strip() for c in st.strip().strip("|").split("|")]
    out = []
    for c in cells:
        if not c or c.isdigit():
            continue
        c = STATUS_RE.sub("", c).strip()
        if c:
            out.append(c)
    return " · ".join(out)


def parse_leads(target):
    if not target:
        return {"findings": [], "chain": {}}
    base = os.path.join(TARGETS_DIR, target, "STATE")
    findings, section, last = [], "", None
    lp = os.path.join(base, "LEADS.md")
    if os.path.isfile(lp):
        try:
            with open(lp, encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
        except Exception:
            lines = []
        for raw in lines:
            st = raw.rstrip("\n").strip()
            low = st.lower()
            if st.startswith("#"):
                last = None
                if low.startswith("## queue"):
                    section = "queue"
                elif low.startswith("## confirm"):
                    section = "confirmed"
                elif low.startswith("## parked"):
                    section = "parked"
                elif low.startswith("## dead"):
                    section = "dead"
                elif low.startswith("## coverage"):
                    section = "coverage"
                else:
                    section = "other"
                continue
            if section == "coverage":
                continue
            if not st:
                last = None
                continue
            if st.startswith("|"):
                bare = "".join(ch for ch in st if ch not in "|-: ")
                if not bare:                      # separator row
                    continue
                if low.startswith("| #") or low.startswith("|#"):
                    continue                      # header row
                text = _clean_row(st)
                if not text:
                    continue
                m = STATUS_RE.search(st)
                sev = SEV_RE.search(text)
                last = {"text": text,
                        "status": _status_class(m.group(1) if m else ("dead" if section == "dead" else "open")),
                        "raw_status": (m.group(1).strip() if m else section),
                        "sev": (sev.group(1).upper() if sev else ""), "where": section}
                findings.append(last)
            elif st.startswith("-"):
                t = st[1:].strip()
                if not t:
                    continue
                m = STATUS_RE.search(t)
                t2 = STATUS_RE.sub("", t).strip()
                default = {"dead": "dead", "parked": "parked",
                           "confirmed": "confirmed"}.get(section, "open")
                sev = SEV_RE.search(t2)
                last = {"text": t2,
                        "status": _status_class(m.group(1) if m else default),
                        "raw_status": (m.group(1).strip() if m else section),
                        "sev": (sev.group(1).upper() if sev else ""), "where": section}
                findings.append(last)
            elif last is not None:                # continuation line
                last["text"] = (last["text"] + " " + st).strip()
    chain = {}
    cp = os.path.join(base, "CHAIN_LEDGER.md")
    if os.path.isfile(cp):
        try:
            txt = open(cp, encoding="utf-8", errors="replace").read()
        except Exception:
            txt = ""
        m = re.search(r"##\s*Active chain[:\s]*(.+)", txt)
        if m:
            chain["active"] = m.group(1).strip()[:200]
        for key, lab in (("Floor", "floor"), ("Ceiling", "ceiling"),
                         ("Missing", "missing"), ("Current rung", "rung")):
            m = re.search(r"\*\*\s*" + re.escape(key) + r"[^*]*\*\*[:\s]*(.*)", txt)
            if m and m.group(1).strip():
                chain[lab] = m.group(1).strip()[:300]
    return {"findings": findings, "chain": chain}


def list_doctrine():
    files = []
    for label, p in DOCTRINE_FILES:
        rp = os.path.realpath(os.path.expanduser(p))
        files.append({"label": label, "path": rp, "exists": os.path.isfile(rp)})
    skills = []
    sd = os.path.realpath(os.path.expanduser("~/.claude/skills"))
    try:
        for n in sorted(os.listdir(sd)):
            full = os.path.join(sd, n)
            if os.path.isdir(full):
                # prefer a SKILL.md if present
                sk = os.path.join(full, "SKILL.md")
                skills.append({"name": n, "path": sk if os.path.isfile(sk) else full,
                               "dir": full})
    except Exception:
        pass
    return {"files": files, "skills": skills, "skills_dir": sd}


def run_mythos(script, *args, timeout=60):
    path = os.path.join(MYTHOS_BIN, script)
    if not os.path.exists(path):
        return {"error": f"missing {script}"}, 404
    try:
        r = subprocess.run(["bash", path, *args], capture_output=True,
                           text=True, timeout=timeout)
        return {"ok": True, "code": r.returncode,
                "out": (r.stdout or "") + (r.stderr or "")}, 200
    except Exception as e:
        return {"error": str(e)}, 500


def do_action(body):
    action = (body.get("action") or "").strip()
    target = (body.get("name") or body.get("target") or "").strip()
    if action in ("new", "activate", "resume", "delete",
                  "lounge-install", "lounge-stop") and not target:
        return {"error": "need a target name"}, 400
    if action == "new":
        return run_mythos("newtarget.sh", target)
    if action == "activate":
        return run_mythos("mtarget.sh", target)
    if action == "resume":
        return run_mythos("resume.sh", target, timeout=90)
    if action == "delete":
        full = safe_path(os.path.join(TARGETS_DIR, target))
        if (not full or os.path.dirname(full) != TARGETS_DIR
                or os.path.basename(full) == "_shared"):
            return {"error": "refused (only a target dir may be deleted)"}, 403
        try:
            import shutil
            shutil.rmtree(full)
            return {"ok": True}, 200
        except Exception as e:
            return {"error": str(e)}, 500
    if action in ("lounge-install", "lounge-stop"):
        s = "install.sh" if action == "lounge-install" else "stop.sh"
        path = os.path.join(LOUNGE_DIR, s)
        if not os.path.exists(path):
            return {"error": f"missing lounge/{s}"}, 404
        cmd = ["bash", path, "--program", target]
        if action == "lounge-install":
            cmd += ["--seats", "2"]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            return {"ok": True, "code": r.returncode,
                    "out": (r.stdout or "") + (r.stderr or "")}, 200
        except Exception as e:
            return {"error": str(e)}, 500
    return {"error": f"unknown action: {action}"}, 400


def subst(template, mapping):
    out = template
    for k, v in mapping.items():
        out = out.replace("{" + k + "}", shlex.quote(str(v)))
    return out


def persist_launches():
    with LOCK:
        data = []
        for lid, l in LAUNCHES.items():
            data.append({k: l[k] for k in
                         ("id", "name", "connector", "target", "prompt", "cwd", "started")})
        try:
            with open(LAUNCHES_FILE, "w") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass


def launch_status(l):
    proc = l.get("proc")
    if proc is None:
        return "detached"
    code = proc.poll()
    if code is None:
        return "running"
    return f"exited {code}"


def do_launch(body):
    conns = {c["name"]: c for c in load_connectors()}
    cname = body.get("connector", "")
    conn = conns.get(cname)
    if not conn:
        return {"error": f"unknown connector: {cname}"}, 400

    name = (body.get("name") or "").strip()
    target = (body.get("target") or "").strip()
    prompt = (body.get("prompt") or "").strip()
    scope = body.get("scope")
    scaffold = bool(body.get("scaffold"))
    if not prompt and not target:
        return {"error": "need at least a prompt or a target"}, 400

    cwd = expand(conn.get("cwd", "~"), name)
    os.makedirs(cwd, exist_ok=True) if "/targets/" in cwd else None

    # optional: scaffold a target dir via the mythos helper (best effort)
    if scaffold and name:
        newtarget = os.path.expanduser("~/.kimi-code/mythos/newtarget.sh")
        if os.path.exists(newtarget):
            try:
                subprocess.run(["bash", newtarget, name], timeout=30,
                               capture_output=True)
            except Exception:
                pass

    # persist the authorized scope AFTER scaffolding. Auto-approve: if the user
    # gave a real scope use it, otherwise write the self-owned default so the
    # target is "allowed" the instant it is launched.
    if name:
        try:
            if scope is not None and scope.strip() and not is_placeholder_scope(scope):
                write_scope(name, scope)
            else:
                ensure_scope(name, target)
        except Exception:
            pass

    mapping = {"prompt": prompt, "target": target, "cwd": cwd, "name": name}
    cmd = subst(conn["command"], mapping)

    # write the interrupt target so the file-as-brain side can see injected prompts
    try:
        state_dir = os.path.join(cwd, "STATE")
        os.makedirs(state_dir, exist_ok=True)
    except Exception:
        state_dir = cwd

    lid = uuid.uuid4().hex[:12]
    logpath = os.path.join(LOGS, lid + ".log")
    logf = open(logpath, "wb")
    header = (f"$ (cwd={cwd})\n$ {cmd}\n{'-'*60}\n").encode()
    logf.write(header); logf.flush()

    try:
        proc = subprocess.Popen(
            ["bash", "-lc", cmd],
            cwd=cwd if os.path.isdir(cwd) else os.path.expanduser("~"),
            stdout=logf, stderr=subprocess.STDOUT,
            stdin=subprocess.PIPE,
            start_new_session=True,
        )
    except Exception as e:
        logf.close()
        return {"error": f"spawn failed: {e}"}, 500

    rec = {
        "id": lid, "name": name or "(unnamed)", "connector": cname,
        "target": target, "prompt": prompt, "cwd": cwd, "state_dir": state_dir,
        "started": time.strftime("%Y-%m-%d %H:%M:%S"),
        "proc": proc, "log": logpath, "logf": logf, "stdin_ok": True,
    }
    with LOCK:
        LAUNCHES[lid] = rec
    persist_launches()
    return {"id": lid}, 200


def do_halt(lid):
    l = LAUNCHES.get(lid)
    if not l or not l.get("proc"):
        return {"error": "no such running launch"}, 404
    proc = l["proc"]
    if proc.poll() is not None:
        return {"ok": True, "note": "already exited"}, 200
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    except Exception:
        try:
            proc.terminate()
        except Exception:
            pass

    def hard_kill():
        time.sleep(3)
        if proc.poll() is None:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except Exception:
                pass
    threading.Thread(target=hard_kill, daemon=True).start()
    return {"ok": True}, 200


def do_interrupt(lid, text):
    l = LAUNCHES.get(lid)
    if not l:
        return {"error": "no such launch"}, 404
    text = (text or "").strip()
    if not text:
        return {"error": "empty prompt"}, 400

    # 1) file-as-brain: append to STATE/INTERRUPT.md in the target
    try:
        f = os.path.join(l.get("state_dir") or l["cwd"], "INTERRUPT.md")
        with open(f, "a") as fh:
            fh.write(f"\n## interrupt {time.strftime('%H:%M:%S')}\n{text}\n")
    except Exception:
        pass

    # 2) live stdin, if the process reads it
    proc = l.get("proc")
    delivered_stdin = False
    if proc and proc.poll() is None and l.get("stdin_ok") and proc.stdin:
        try:
            proc.stdin.write((text + "\n").encode())
            proc.stdin.flush()
            delivered_stdin = True
        except Exception:
            l["stdin_ok"] = False
    return {"ok": True, "stdin": delivered_stdin}, 200


def read_log(lid, offset):
    l = LAUNCHES.get(lid)
    if not l:
        return {"error": "no such launch"}, 404
    path = l["log"]
    size = os.path.getsize(path) if os.path.exists(path) else 0
    data = ""
    if size > offset:
        with open(path, "rb") as f:
            f.seek(offset)
            data = f.read().decode("utf-8", "replace")
    return {"data": data, "offset": size, "status": launch_status(l)}, 200


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body).encode()
        elif isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        # never cache: the panel is served on a fixed localhost URL, so a stale
        # cached index.html (e.g. an older build) would otherwise load forever.
        self.send_header("Cache-Control", "no-store, must-revalidate")
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        n = int(self.headers.get("Content-Length", 0) or 0)
        if not n:
            return {}
        try:
            return json.loads(self.rfile.read(n) or b"{}")
        except Exception:
            return {}

    def log_message(self, *a):
        pass  # quiet

    def do_GET(self):
        p = self.path.split("?")[0]
        if p == "/" or p == "/index.html":
            with open(os.path.join(HERE, "index.html"), "rb") as f:
                return self._send(200, f.read().decode(), "text/html; charset=utf-8")
        if p == "/api/state":
            with LOCK:
                launches = [{
                    "id": l["id"], "name": l["name"], "connector": l["connector"],
                    "target": l["target"], "prompt": l["prompt"], "cwd": l["cwd"],
                    "started": l["started"], "status": launch_status(l),
                } for l in reversed(list(LAUNCHES.values()))]
            return self._send(200, {
                "connectors": load_connectors(),
                "launches": launches,
                "detected": detect_clis(),
            })
        if p == "/api/log":
            from urllib.parse import parse_qs, urlparse
            q = parse_qs(urlparse(self.path).query)
            lid = (q.get("id") or [""])[0]
            offset = int((q.get("offset") or ["0"])[0])
            out, code = read_log(lid, offset)
            return self._send(code, out)
        if p == "/api/scope":
            from urllib.parse import parse_qs, urlparse
            q = parse_qs(urlparse(self.path).query)
            name = (q.get("name") or [""])[0]
            return self._send(200, {
                "name": name,
                "scope": read_scope(name),
                "path": scope_path(name) or "",
            })
        if p == "/api/targets":
            return self._send(200, {
                "targets": list_targets(),
                "active": active_target(),
                "state_files": STATE_FILES,
                "subdirs": TARGET_SUBDIRS,
                "targets_dir": TARGETS_DIR,
            })
        if p == "/api/file":
            from urllib.parse import parse_qs, urlparse
            q = parse_qs(urlparse(self.path).query)
            out, code = read_file_api((q.get("path") or [""])[0])
            return self._send(code, out)
        if p == "/api/tree":
            from urllib.parse import parse_qs, urlparse
            q = parse_qs(urlparse(self.path).query)
            out, code = list_tree((q.get("path") or [""])[0])
            return self._send(code, out)
        if p == "/api/journal":
            from urllib.parse import parse_qs, urlparse
            q = parse_qs(urlparse(self.path).query)
            out, code = read_journal((q.get("target") or [""])[0])
            return self._send(code, out)
        if p == "/api/doctrine":
            return self._send(200, list_doctrine())
        if p == "/api/leads":
            from urllib.parse import parse_qs, urlparse
            q = parse_qs(urlparse(self.path).query)
            return self._send(200, parse_leads((q.get("target") or [""])[0]))
        return self._send(404, {"error": "not found"})

    def do_POST(self):
        p = self.path.split("?")[0]
        body = self._body()
        if p == "/api/connectors":
            conns = body.get("connectors", [])
            save_connectors(conns)
            return self._send(200, {"ok": True, "count": len(conns)})
        if p == "/api/scope":
            name = (body.get("name") or "").strip()
            if not name:
                return self._send(400, {"error": "need a target name to save scope"})
            path = write_scope(name, body.get("scope", ""))
            return self._send(200, {"ok": True, "path": path or ""})
        if p == "/api/launch":
            out, code = do_launch(body)
            return self._send(code, out)
        if p == "/api/halt":
            out, code = do_halt(body.get("id", ""))
            return self._send(code, out)
        if p == "/api/interrupt":
            out, code = do_interrupt(body.get("id", ""), body.get("prompt", ""))
            return self._send(code, out)
        if p == "/api/file":
            out, code = write_file_api(body.get("path", ""), body.get("content", ""))
            return self._send(code, out)
        if p == "/api/action":
            out, code = do_action(body)
            return self._send(code, out)
        return self._send(404, {"error": "not found"})


class V6Server(ThreadingHTTPServer):
    address_family = socket.AF_INET6


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=int(os.environ.get("MYTHOS_PANEL_PORT", 8765)))
    ap.add_argument("--host", default="")  # "" = dual loopback (127.0.0.1 + ::1)
    args = ap.parse_args()
    load_connectors()

    servers = []
    if args.host:
        servers.append(ThreadingHTTPServer((args.host, args.port), Handler))
    else:
        # Browsers resolve "localhost" to ::1 first; bind BOTH loopback families
        # so the panel answers whichever the browser picks (fixes "loading forever").
        servers.append(ThreadingHTTPServer(("127.0.0.1", args.port), Handler))
        try:
            servers.append(V6Server(("::1", args.port), Handler))
        except OSError as e:
            print(f"(note: IPv6 loopback unavailable: {e})")

    for s in servers:
        threading.Thread(target=s.serve_forever, daemon=True).start()
    bound = ", ".join(f"http://{'127.0.0.1' if s.address_family==socket.AF_INET else '[::1]'}:{args.port}"
                      for s in servers) if not args.host else f"http://{args.host}:{args.port}"
    print(f"MYTHOS Lounge panel  ->  {bound}")
    print(f"state dir: {BASE}")
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        print("\nshutting down")
        for s in servers:
            s.shutdown()


if __name__ == "__main__":
    main()
