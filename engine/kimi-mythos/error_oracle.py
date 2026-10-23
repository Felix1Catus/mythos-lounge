#!/usr/bin/env python3
"""
HOOK 4/10 — error_oracle  (PostToolUse: Bash|WebFetch, advisory)

Every distinct error class is one mapped internal branch (P10). This scrapes the HTTP
status + error class out of the tool result and appends an NDJSON line to
STATE/ERROR_ORACLE.ndjson keyed by surface (host+path). When the SAME status reappears
for a surface carrying a DIFFERENT error class, that is a stage flip — the proof P10
talks about — and it is flagged on stdout so the model sees it immediately.

Never blocks; one stdout line only on a flip. Fails OPEN.
"""
import json
import mythos_hooklib as H


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
    if not status:
        return
    surface = H.first_surface(cmd) or (H.host_of(ti.get("url") or ""))
    if not surface:
        return
    prog = H.resolve_prog(cmd or (ti.get("url") or ""), tool)
    if not prog:
        return
    klass = H.error_class(text)

    # scan prior lines for this surface+status to detect a class flip
    flip = None
    prior = H.read_state(prog, "ERROR_ORACLE.ndjson")
    for ln in prior.splitlines():
        try:
            rec = json.loads(ln)
        except Exception:
            continue
        if rec.get("surface") == surface and rec.get("status") == status:
            if klass and rec.get("class") and rec.get("class") != klass:
                flip = rec.get("class")
                break

    H.append_state(prog, "ERROR_ORACLE.ndjson", json.dumps(
        {"ts": H.now(), "surface": surface, "status": status,
         "class": klass, "method": H.http_method(cmd)}, ensure_ascii=False))

    if flip:
        H.nudge("🔀 MYTHOS error_oracle: %s returned %s with a NEW class '%s' "
                "(was '%s'). P10 stage flip — two branches behind one status. "
                "That flip is the proof: map the branch between them."
                % (surface, status, klass, flip))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    import sys
    sys.exit(0)
