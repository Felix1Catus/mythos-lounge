#!/usr/bin/env python3
"""
HOOK 5/10 — evidence_autolog  (PostToolUse: Bash|WebFetch, passive)

P01/P14 want receipts before any wave and a drafted report the same session. This saves
the raw request + response of anything worth keeping — a 2xx on a state-mutating method, a
5xx oracle, or an auth/redirect to an internal host — under
~/targets/<prog>/evidence/auto/<ts>.txt, with a curl-style repro line. So evidence-first
never depends on the agent remembering to save.

Never blocks, never writes stdout. Fails OPEN.
"""
import os, re
import mythos_hooklib as H


def interesting(cmd, status):
    if not status:
        return None
    s = int(status) if status.isdigit() else 0
    method = H.http_method(cmd)
    if method in ("POST", "PUT", "PATCH", "DELETE") and 200 <= s < 300:
        return "mutation-2xx (%s %d)" % (method, s)
    if 500 <= s < 600:
        return "5xx oracle (%d)" % s
    if s in (301, 302, 303, 307, 308):
        return "redirect (%d)" % s
    return None


def main():
    d = H.read_payload()
    if d is None:
        return
    tool, ti = H.tool_and_input(d)
    if tool not in ("Bash", "WebFetch", "FetchURL"):
        return
    cmd = H.command_of(ti) or (ti.get("url") or "")
    text = H.response_text(d)
    status = H.http_status(text)
    why = interesting(cmd, status)
    if not why:
        return
    prog = H.resolve_prog(cmd, tool)
    if not prog:
        return
    surface = H.first_surface(cmd) or H.host_of(ti.get("url") or "")
    if not surface:
        return

    d_evi = os.path.join(H.HOME, "targets", prog, "evidence", "auto")
    try:
        os.makedirs(d_evi, exist_ok=True)
        ts = H.now().replace(":", "").replace("-", "").replace("+", "p")
        safe = re.sub(r'[^A-Za-z0-9._-]', "_", surface)[:60]
        path = os.path.join(d_evi, "%s_%s.txt" % (ts, safe))
        with open(path, "w", encoding="utf-8") as f:
            f.write("# MYTHOS evidence_autolog\n")
            f.write("when: %s\nwhy: %s\nsurface: %s\nstatus: %s\n\n"
                    % (H.now(), why, surface, status))
            f.write("## repro\n%s\n\n" % cmd)
            f.write("## response (first 8KB)\n%s\n" % text[:8192])
    except Exception:
        pass


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    import sys
    sys.exit(0)
