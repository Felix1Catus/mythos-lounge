#!/usr/bin/env python3
"""
probelib — shared probe plumbing for all hunt batteries (Kimi/Claude/Grok).

WHY THIS EXISTS (PROGRAM_81 2026-07-29/30 scars):
- batteries re-implemented req() and re-hit the SAME bugs: missing Content-Type → 415,
  json.dumps("14") → quoted body, curl [ globbing, heredoc stdin hijack, egress flapping
  killing runs, pgrep self-match.
RULE: batteries import this. Never hand-roll HTTP in a probe script again.

USAGE:
  from probelib import Probe, Battery
  p = Probe(base="https://www.PROGRAM_85.com", out="/path/to/results.json")
  st, body = p.get("/api/x", params={"a": 1})
  st, body = p.post("/api/y", json={"k": "v"}, headers={"XCaptcha-Token": t})
  st, body = p.post("/api/z", raw="14")               # raw sets CT: application/json
  b = Battery(p, delay=2.0); b.fire("label", p.post, "/api/y", json={...})
"""
from __future__ import annotations
import json, time, hashlib, urllib.request, urllib.error, urllib.parse, subprocess

DEFAULT_UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/126.0 Safari/537.36")

def egress_ip() -> str:
    try:
        return json.loads(urllib.request.urlopen(
            "https://api.ipify.org?format=json", timeout=8).read())["ip"]
    except Exception:
        return "unknown"

class Probe:
    def __init__(self, base: str, out: str | None = None, ua: str = DEFAULT_UA,
                 delay: float = 1.5, retries: int = 2, log_egress: bool = True):
        self.base = base.rstrip("/")
        self.out = out
        self.ua = ua
        self.delay = delay
        self.retries = retries
        self.records = []
        self.egress = egress_ip() if log_egress else "skip"
        self.cookies: dict[str, str] = {}

    def _request(self, method: str, path: str, data: bytes | None,
                 ctype: str | None, headers: dict | None) -> tuple[int, str]:
        url = path if path.startswith("http") else self.base + path
        last = (0, "")
        for attempt in range(self.retries + 1):
            req = urllib.request.Request(url, method=method)
            req.add_header("User-Agent", self.ua)
            req.add_header("Accept", "application/json")
            if self.cookies:
                req.add_header("Cookie", "; ".join(f"{k}={v}" for k, v in self.cookies.items()))
            if ctype:
                req.add_header("Content-Type", ctype)
            for k, v in (headers or {}).items():
                req.add_header(k, v)
            try:
                with urllib.request.urlopen(req, data=data, timeout=30) as r:
                    return r.status, r.read().decode(errors="replace")
            except urllib.error.HTTPError as e:
                return e.code, e.read().decode(errors="replace")
            except Exception as e:
                last = (0, f"NETERR: {e}")
                time.sleep(3 * (attempt + 1))
        return last

    def get(self, path: str, params: dict | None = None, headers: dict | None = None):
        if params:
            path += ("&" if "?" in path else "?") + urllib.parse.urlencode(params)
        time.sleep(self.delay)
        return self._request("GET", path, None, None, headers)

    def post(self, path: str, json_body=None, raw: str | bytes | None = None,
             ctype: str = "application/json", headers: dict | None = None):
        """json_body → json.dumps (ints stay ints: pass 14 not "14").
           raw → sent verbatim with ctype (default application/json)."""
        if raw is not None:
            data = raw.encode() if isinstance(raw, str) else raw
        elif json_body is not None:
            data = json.dumps(json_body).encode()
        else:
            data = None
        time.sleep(self.delay)
        return self._request("POST", path, data, ctype if data is not None else None, headers)

    def put(self, path: str, json_body=None, raw: str | None = None, headers: dict | None = None):
        data = raw.encode() if raw is not None else (json.dumps(json_body).encode() if json_body is not None else None)
        time.sleep(self.delay)
        return self._request("PUT", path, data, "application/json" if data is not None else None, headers)

    def curl(self, args: list[str]) -> tuple[int, str]:
        """Shell curl for TLS/resolve tricks. -g (globoff) is FORCED — [ in URLs must never glob."""
        cmd = ["curl", "-sg", "--max-time", "30"] + args
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=40)
            return r.returncode, r.stdout + r.stderr
        except Exception as e:
            return -1, str(e)

class Battery:
    """Checkpointed probe battery: fires, classifies, persists per-probe (resumable)."""
    def __init__(self, probe: Probe, out: str, delay: float | None = None):
        self.p = probe
        self.out = out
        self.results = []
        if delay is not None:
            self.p.delay = delay
        try:
            self.results = json.load(open(out))
        except Exception:
            pass
        self.done = {r["label"] for r in self.results}

    def fire(self, label: str, fn, *args, **kwargs):
        if label in self.done:
            print(f"[skip] {label}", flush=True)
            return
        st, body = fn(*args, **kwargs)
        sig = hashlib.md5(body.encode()).hexdigest()[:8] if body else "empty"
        rec = {"label": label, "status": st, "len": len(body), "sig": sig, "body": body[:400]}
        self.results.append(rec)
        self.done.add(label)
        print(f"[{st}|{len(body):>5}|{sig}] {label} :: {body[:120]}", flush=True)
        json.dump({"egress": self.p.egress, "results": self.results}, open(self.out, "w"), indent=1)

# process-safety: NEVER `pkill -f <pattern>` from a battery — the pattern matches your own
# shell's cmdline. Use kill_by_comm (matches /proc/<pid>/comm exactly).
def kill_by_comm(comm_name: str, sig: int = 9):
    import os, signal
    killed = []
    for pid in os.listdir("/proc"):
        if not pid.isdigit():
            continue
        try:
            if open(f"/proc/{pid}/comm").read().strip() == comm_name:
                os.kill(int(pid), sig)
                killed.append(int(pid))
        except Exception:
            pass
    return killed


def load_profile_cookies(profile_dir: str, domain_filter: str | None = None) -> dict[str, str]:
    """Extract+decrypt cookies from a Chromium profile (Linux).
    Handles: DB at Default/Cookies or Default/Network/Cookies; v10 AES-128-CBC
    (mock/basic keychain: PBKDF2(peanuts, saltysalt, 1)); strips the 32-byte
    SHA-256 host_key prefix Chrome prepends to the decrypted plaintext."""
    import sqlite3, shutil, tempfile, os, hashlib, sys
    db = None
    for cand in ("Default/Cookies", "Default/Network/Cookies", "Network/Cookies"):
        p = os.path.join(profile_dir, cand)
        if os.path.exists(p):
            db = p
            break
    if not db:
        return {}
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "pylibs"))
    from Crypto.Cipher import AES
    fd, tmp = tempfile.mkstemp(suffix=".sqlite")  # unique per run — never a stale path
    os.close(fd)
    shutil.copy(db, tmp)
    try:
        con = sqlite3.connect(tmp)
        rows = list(con.execute("SELECT name, encrypted_value, host_key FROM cookies ORDER BY creation_utc"))
        con.close()
    finally:
        os.unlink(tmp)
    key = hashlib.pbkdf2_hmac("sha1", b"peanuts", b"saltysalt", 1, 16)

    def dec(ev: bytes) -> str:
        if not ev:
            return ""
        if not ev.startswith(b"v10"):
            return ev.decode(errors="replace")
        pt = AES.new(key, AES.MODE_CBC, b" " * 16).decrypt(ev[3:])
        pt = pt[:-pt[-1]]
        return pt[32:].decode(errors="replace")  # strip SHA-256(host) prefix

    out = {}
    for name, ev, host in rows:
        if domain_filter and domain_filter not in host:
            continue
        try:
            out[name] = dec(ev)
        except Exception:
            pass
    return out


def self_test(verbose: bool = True) -> bool:
    """INSTRUMENT DISCIPLINE (I1/I2 scars): run ONCE per session before believing any
    null/negative from a battery. Fires known-good requests and checks the plumbing:
      1. GET  https://example.com            → expect 200 (transport alive)
      2. POST https://postman-echo.com/post  → expect 200 + our JSON echoed back
         (proves Content-Type default + body encoding — the 415 captcha-chase bug)
      3. egress IP logged (egress flaps killed runs before)
    Prints PASS/FAIL per arm. Returns True only if ALL arms pass."""
    ok = True
    p = Probe(base="https://example.com", delay=0, retries=0, log_egress=True)
    st, body = p.get("/")
    arm1 = st == 200 and "Example Domain" in body
    ok &= arm1
    if verbose:
        print(f"[{'PASS' if arm1 else 'FAIL'}] GET example.com → {st} (want 200)")
    p2 = Probe(base="https://postman-echo.com", delay=0, retries=0, log_egress=False)
    st2, body2 = p2.post("/post", json_body={"probe_selftest": 14})
    try:
        echoed = json.loads(body2).get("json", {}) == {"probe_selftest": 14}
    except Exception:
        echoed = False
    arm2 = st2 == 200 and echoed
    ok &= arm2
    if verbose:
        print(f"[{'PASS' if arm2 else 'FAIL'}] POST postman-echo → {st2} json-echo={echoed} (want 200 True)")
        print(f"[{'PASS' if p.egress not in ('unknown', 'skip') else 'FAIL'}] egress IP: {p.egress}")
    if p.egress in ("unknown", "skip"):
        ok = False
    return ok


if __name__ == "__main__":
    import sys
    sys.exit(0 if self_test() else 1)
