#!/usr/bin/env python3
"""
HOOK 11/12 — recon_diff  (PreToolUse: Bash|WebFetch, BLOCKING once per session)

Source-first (M1/M2 + the 'black-box probing a source-available target' anti-pattern):
when the source IS published, you read/diff it and probe only to CONFIRM a hypothesis —
never to discover. This blocks the FIRST live probe of a session against a target whose
STATE/SOURCE.md exists but is not yet marked diffed, pointing at fork-vs-upstream /
patch-gap / version N-vs-N-1 before any black-box request goes out.

Dormant unless STATE/SOURCE.md exists — zero friction on black-box targets. Once per
session (marker). Local/RFC1918 destinations never count as a probe. Fails OPEN.
"""
import os, re
import mythos_hooklib as H

DIFFED = re.compile(r'(?im)^\s*[-*]?\s*diffed\s*[:=]\s*(yes|done|true|y)\b')
DIFFED_BOX = re.compile(r'(?im)^\s*[-*]?\s*\[x\].*diff')


def main():
    d = H.read_payload()
    if d is None:
        return
    tool, ti = H.tool_and_input(d)
    if tool == "Bash":
        cmd = H.command_of(ti)
        hosts = H.request_hosts(cmd)
    elif tool in ("WebFetch", "FetchURL"):
        cmd = ti.get("url") or ""
        h = H.host_of(cmd)
        hosts = {h} if h else set()
    else:
        return
    live = [h for h in hosts if not H.is_local_host(h)]
    if not live:
        return
    prog = H.resolve_prog(cmd, tool)
    if not prog:
        return
    src = H.read_state(prog, "SOURCE.md")
    if not src:
        return  # not a source-available target -> dormant
    if DIFFED.search(src) or DIFFED_BOX.search(src):
        return  # already diffed -> allow probing

    sess = H.session_of(d)
    marker = os.path.join(H.HOOK_DIR, "recondiff_nudged_" +
                          re.sub(r'[^A-Za-z0-9_.-]', '_', sess))
    if os.path.exists(marker):
        return  # only the first probe of the session is gated
    try:
        open(marker, "w").write(H.now())
    except Exception:
        pass
    H.block("recon_diff (M1/M2): '%s' is a source-available target (STATE/SOURCE.md) not "
            "yet diffed. Read/diff the source BEFORE black-box probing %s — fork-vs-upstream, "
            "patch-gap re-audit, version N-vs-N-1. Probe only to confirm a source hypothesis. "
            "Flip 'DIFFED: yes' in SOURCE.md once the audit is underway." % (prog, live[0]))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    import sys
    sys.exit(0)
