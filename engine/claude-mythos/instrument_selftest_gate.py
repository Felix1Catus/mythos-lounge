#!/usr/bin/env python3
"""
HOOK 8/10 — instrument_selftest_gate  (PreToolUse + PostToolUse: Bash)

P03 / tendon 2: positive-control every load-bearing negative; an instrument's null is
worthless until the instrument is exonerated. This gate requires a probelib self-test PASS
once per session before probelib output is trusted.

  PostToolUse : sees `probelib.py` self-test output containing PASS -> drops a session marker.
  PreToolUse  : a command that USES probelib as a library/probe (not the bare self-test),
                with no marker this session -> BLOCK, tell the agent to self-test first.

The bare self-test (`python3 .../probelib.py` with no extra args, or `--selftest`) is always
allowed. Fails OPEN on any uncertainty.
"""
import os, re
import mythos_hooklib as H

MARKER_DIR = os.path.join(H.HOOK_DIR, "selftest")
USES = re.compile(r'probelib', re.I)
BARE = re.compile(r'probelib\.py(\s+--selftest)?\s*$|probelib\.py\s*(?:#|$)')


def marker(sess):
    return os.path.join(MARKER_DIR, "ok_" + re.sub(r'[^A-Za-z0-9_.-]', '_', sess))


def main():
    d = H.read_payload()
    if d is None:
        return
    ev = H.event_of(d)
    tool, ti = H.tool_and_input(d)
    if tool != "Bash":
        return
    cmd = H.command_of(ti)
    if not cmd or not USES.search(cmd):
        return
    sess = H.session_of(d)

    if ev == "PostToolUse":
        text = H.response_text(d)
        if re.search(r'\bPASS\b|self-?test.*ok|ALL\s+PASS', text, re.I):
            try:
                os.makedirs(MARKER_DIR, exist_ok=True)
                open(marker(sess), "w").write(H.now())
            except Exception:
                pass
        return

    # PreToolUse
    if BARE.search(cmd.strip()):
        return  # the self-test itself — allow
    if os.path.exists(marker(sess)):
        return
    H.block("instrument_selftest_gate (P03): probelib used before its self-test PASSED "
            "this session. Run `python3 ~/targets/_shared/probelib.py` first — a null from "
            "an unverified instrument is not evidence. Re-run this probe after it reports PASS.")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    import sys
    sys.exit(0)
