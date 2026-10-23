#!/usr/bin/env python3
"""
MYTHOS hook shared library — common helpers for the bug-hunting hook set.

Edition-agnostic: every path is resolved relative to THIS file's directory (so the
same byte-identical copy works whether it lives under ~/.kimi-code/mythos/ or
~/.claude/mythos/) or under ~/targets/<prog>/STATE/. No network, no third-party deps.

Hook I/O contract (Claude Code / Kimi Code):
  stdin  -> JSON {"hook_event_name","session_id","cwd","tool_name","tool_input":{...},
                  "tool_response":{...}}
  PreToolUse / Stop block : write reason to stderr, exit 2.
  PostToolUse advisory    : write ONE line to stdout, exit 0 (never blocks).
  Any parse/IO error      : fail OPEN (exit 0, allow) — a hook never breaks the hunt.

sys.exit(2) raises SystemExit, which is NOT an Exception, so an `except Exception`
fail-open wrapper in a caller will not swallow a deliberate block. (Mirrors
pretooluse_guard.py.)
"""
import json, os, re, sys, hashlib, datetime

HOME = os.path.expanduser("~")
HOOK_DIR = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------- payload
def read_payload():
    """Parse the hook JSON from stdin. None on any failure (caller fails open)."""
    try:
        return json.load(sys.stdin)
    except Exception:
        return None


def tool_and_input(d):
    tool = (d.get("tool_name") or d.get("toolName")
            or (d.get("tool") or {}).get("name") or "")
    ti = d.get("tool_input") or d.get("toolInput") or {}
    if not isinstance(ti, dict):
        ti = {}
    return tool, ti


def command_of(ti):
    return ti.get("command") or ""


def event_of(d):
    return d.get("hook_event_name") or d.get("hookEventName") or ""


def session_of(d):
    return d.get("session_id") or d.get("sessionId") or "nosession"


def response_text(d):
    """Best-effort flat text of the tool result."""
    tr = d.get("tool_response") or d.get("toolResponse") or d.get("result")
    if isinstance(tr, dict):
        for k in ("stdout", "stderr", "content", "output", "body"):
            v = tr.get(k)
            if isinstance(v, str) and v:
                return v
        try:
            return json.dumps(tr)
        except Exception:
            return ""
    if isinstance(tr, str):
        return tr
    return ""


# ---------------------------------------------------------------- program routing
def active_target():
    """First token of the active_target marker that sits next to this file."""
    try:
        with open(os.path.join(HOOK_DIR, "active_target")) as f:
            parts = f.read().strip().split()
            return parts[0] if parts else ""
    except Exception:
        return ""


def resolve_prog(blob, tool):
    """Program a tool call belongs to: an explicit targets/<prog>/ path wins; else,
    for live-probe tools only, the active-target marker (journal.py semantics)."""
    m = re.search(r'targets/([A-Za-z0-9_.\-]+)/', blob or "")
    if m and m.group(1) not in ("_recon", "_cleanup", "misc", "_shared", "_gate"):
        return m.group(1)
    if tool in ("Bash", "FetchURL", "WebFetch", "WebSearch"):
        return active_target()
    return ""


def state_dir(prog):
    return os.path.join(HOME, "targets", prog, "STATE")


def read_state(prog, name):
    try:
        with open(os.path.join(state_dir(prog), name), encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception:
        return ""


def append_state(prog, name, line, mode=0o644):
    d = state_dir(prog)
    try:
        os.makedirs(d, exist_ok=True)
        p = os.path.join(d, name)
        with open(p, "a", encoding="utf-8") as f:
            f.write(line.rstrip("\n") + "\n")
        try:
            os.chmod(p, mode)
        except Exception:
            pass
        return True
    except Exception:
        return False


# ---------------------------------------------------------------- URLs / hosts
URL_RE = re.compile(r'https?://[^\s\'"`<>|\\)]+', re.I)
DOMAIN_RE = re.compile(
    r'(?<![\w.-])(\*\.)?((?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,24})(?![\w-])',
    re.I,
)
NET_TOOLS = ("curl", "wget", "httpx", "http ", "nuclei", "ffuf", "feroxbuster",
             "gobuster", "dirb", "dirsearch", "wfuzz", "hydra", "nmap", "masscan",
             "nc ", "ncat", "openssl", "socat", "requests.", "httpie")


def urls_in(cmd):
    return URL_RE.findall(cmd or "")


def host_of(url):
    m = re.match(r'https?://(?:[^/@\s]+@)?([^/:\s]+)', url or "", re.I)
    return m.group(1).lower().rstrip(".") if m else ""


def request_hosts(cmd):
    """Destination hosts a command talks to: URL hosts always; bare domains too when
    the command invokes a known network tool."""
    hosts = set()
    for u in urls_in(cmd):
        h = host_of(u)
        if h:
            hosts.add(h)
    low = (cmd or "").lower()
    if any(t in low for t in NET_TOOLS):
        for _w, dom in DOMAIN_RE.findall(cmd or ""):
            hosts.add(dom.lower().rstrip("."))
    return hosts


_LOCAL_RE = re.compile(
    r'^(localhost|127\.|0\.0\.0\.0$|::1$|10\.|192\.168\.|169\.254\.|'
    r'172\.(1[6-9]|2[0-9]|3[01])\.)|\.(localhost|test|local|internal)$', re.I)


def is_local_host(h):
    if not h:
        return True
    return bool(_LOCAL_RE.search(h)) or h in ("localhost", "::1")


# ---------------------------------------------------------------- scope
def _section(text, header):
    """Lines between a `## header...` line and the next `## ` line."""
    out, grab = [], False
    for ln in text.splitlines():
        s = ln.strip()
        if s.startswith("## "):
            grab = header.lower() in s.lower()
            continue
        if grab:
            out.append(ln)
    return "\n".join(out)


def load_scope(prog):
    """Return (allow, deny) sets of registrable domains from STATE/SCOPE.md.
    Empty allow set means 'scope unknown' -> callers must NOT block on it."""
    txt = read_state(prog, "SCOPE.md")
    if not txt:
        return set(), set()
    allow, deny = set(), set()
    in_sec = _section(txt, "In scope")
    out_sec = _section(txt, "Out of scope")
    for _w, dom in DOMAIN_RE.findall(in_sec):
        d = dom.lower().rstrip(".")
        if d not in ("example.com", "policy.url"):
            allow.add(d)
    for _w, dom in DOMAIN_RE.findall(out_sec):
        deny.add(dom.lower().rstrip("."))
    return allow, deny


def host_matches(host, domain):
    host = (host or "").lower().rstrip(".")
    domain = (domain or "").lower().lstrip("*.").rstrip(".")
    return bool(domain) and (host == domain or host.endswith("." + domain))


def in_scope(host, allow, deny):
    """None = can't judge (no allowlist). True/False otherwise. Deny always wins."""
    if is_local_host(host):
        return True
    if any(host_matches(host, d) for d in deny):
        return False
    if not allow:
        return None
    return any(host_matches(host, d) for d in allow)


# ---------------------------------------------------------------- http parsing
_STATUS_RES = [
    re.compile(r'HTTP/\d(?:\.\d)?\s+(\d{3})'),
    re.compile(r'(?:^|\s)<\s*HTTP/\d(?:\.\d)?\s+(\d{3})'),
    re.compile(r'"status(?:Code)?"\s*:\s*(\d{3})'),
    re.compile(r'(?:^|\n)\s*(\d{3})\s+[A-Z][A-Za-z ]{2,}'),
]


def http_status(text):
    for rx in _STATUS_RES:
        m = rx.search(text or "")
        if m:
            return m.group(1)
    return ""


def error_class(text):
    """A short, stable label for the server's 'sentence' (error code/message)."""
    t = text or ""
    for rx in (r'"(?:error_code|errorCode|code|error|reason|title)"\s*:\s*"([^"]{1,60})"',
               r'"message"\s*:\s*"([^"]{1,80})"'):
        m = re.search(rx, t)
        if m:
            return " ".join(m.group(1).split())[:80]
    m = re.search(r'HTTP/\d(?:\.\d)?\s+\d{3}\s+([A-Za-z][A-Za-z ]{2,40})', t)
    if m:
        return m.group(1).strip()[:80]
    return ""


def http_method(cmd):
    m = re.search(r'-X\s*([A-Za-z]+)', cmd or "")
    if m:
        return m.group(1).upper()
    if re.search(r'--data|--json|-d\s|--form|-F\s', cmd or ""):
        return "POST"
    return "GET"


def first_surface(cmd):
    for u in urls_in(cmd):
        h = host_of(u)
        path = re.sub(r'^https?://[^/]+', '', u, flags=re.I).split("?")[0] or "/"
        if h:
            return h + path
    return ""


# ---------------------------------------------------------------- misc
def sha(s):
    return hashlib.sha256(s.encode("utf-8", "replace")).hexdigest()


def now():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def _emit(stream, text):
    """Write text, surviving a console whose encoding can't take it (e.g. Windows
    cp1252 vs an emoji). Never let an encoding error swallow a guard's message."""
    try:
        stream.write(text)
    except UnicodeEncodeError:
        try:
            stream.buffer.write(text.encode("utf-8", "replace"))
        except Exception:
            stream.write(text.encode("ascii", "replace").decode("ascii"))
    try:
        stream.flush()
    except Exception:
        pass


def block(msg):
    _emit(sys.stderr, "MYTHOS " + msg.strip() + "\n")
    sys.exit(2)


def nudge(line):
    _emit(sys.stdout, line.strip() + "\n")
    sys.exit(0)
