#!/usr/bin/env python3
"""
HOOK 7/10 — liveness_watchdog  (PostToolUse: Bash|WebFetch, advisory)

P04 state-liveness: a liveness check per wave / ~25 authed requests, and the first 401 →
halt (never analyze post-401 corpses). This counts authed-looking requests per
(prog, session) in STATE/.liveness.json and nudges when a 401/403 follows an authed probe,
or every 25 authed requests.

Never blocks; one stdout line when it fires. Fails OPEN.
"""
import json, os, re
import mythos_hooklib as H

AUTHED = re.compile(r'authorization:|bearer\s|cookie:|x-api-key|-b\s|--cookie|'
                    r'session=|access_token|id_token', re.I)
EVERY = 25


def main():
    d = H.read_payload()
    if d is None:
        return
    tool, ti = H.tool_and_input(d)
    if tool not in ("Bash", "WebFetch", "FetchURL"):
        return
    cmd = H.command_of(ti) or ""
    headers = json.dumps(ti.get("headers", "")) if isinstance(ti, dict) else ""
    blob = cmd + " " + headers
    if not AUTHED.search(blob):
        return
    prog = H.resolve_prog(cmd or (ti.get("url") or ""), tool)
    if not prog:
        return
    sess = H.session_of(d)
    text = H.response_text(d)
    status = H.http_status(text)

    path = os.path.join(H.state_dir(prog), ".liveness.json")
    st = {}
    try:
        with open(path) as f:
            st = json.load(f)
    except Exception:
        st = {}
    rec = st.get(sess, {"n": 0, "halted": False})
    rec["n"] = rec.get("n", 0) + 1
    fire = None

    if status in ("401", "403") and not rec.get("halted"):
        rec["halted"] = True
        fire = ("🛑 MYTHOS liveness_watchdog (P04): %s after an authed request on '%s'. "
                "Auth may be dead — STOP analyzing post-401 corpses. Re-auth / run a "
                "liveness probe before the next wave." % (status, prog))
    elif status not in ("401", "403"):
        rec["halted"] = False
        if rec["n"] % EVERY == 0:
            fire = ("⏱ MYTHOS liveness_watchdog (P04): %d authed requests this session on "
                    "'%s' with no liveness check. Fire one before trusting the next batch."
                    % (rec["n"], prog))
    st[sess] = rec
    try:
        os.makedirs(H.state_dir(prog), exist_ok=True)
        with open(path, "w") as f:
            json.dump(st, f)
    except Exception:
        pass
    if fire:
        H.nudge(fire)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    import sys
    sys.exit(0)
