#!/usr/bin/env python3
"""
MYTHOS PreToolUse safety guard — Kimi Code edition.

Fires before Bash tool calls (PreToolUse, matcher "Bash"). Dangerous kernel/disk
primitives -> BLOCK (exit 2 + stderr reason, per Kimi hook contract). Fail-OPEN on
any parse error. Logs matches to ~/.kimi-code/mythos/safety.log.

Kimi hook payload (stdin): {"hook_event_name":"PreToolUse","session_id":...,"cwd":...,
                            "tool_name":"Bash","tool_input":{"command":"..."}}
Blocking: print reason to stderr, exit 2. (JSON hookSpecificOutput.permissionDecision
"deny" also works; stderr+exit2 keeps the reason in context for the model.)

Born from feedback_escape_harness_safety (modprobe/core_pattern left armed twice).
LOCATION: ~/.kimi-code/mythos/pretooluse_guard.py
"""
import json, sys, os, re, datetime

LOG = os.path.expanduser("~/.kimi-code/mythos/safety.log")

def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return  # unparseable -> allow silently (fail-open)

    tool = data.get("tool_name") or data.get("toolName") or ""
    tin = data.get("tool_input") or data.get("toolInput") or {}
    if not isinstance(tin, dict):
        tin = {}
    cmd = tin.get("command") or ""

    if tool != "Bash" or not cmd:
        return

    matched = None
    simple = [
        (r"\bmodprobe\b",        "modprobe (kernel module load)"),
        (r"\binsmod\b",          "insmod (kernel module insert)"),
        (r"\brmmod\b",           "rmmod (kernel module remove)"),
        (r"core_pattern",        "core_pattern tamper"),
        (r"/proc/sys/kernel",    "/proc/sys/kernel tamper"),
        (r"\bmkfs",              "mkfs (filesystem create)"),
        (r"\bfdisk\b",           "fdisk (disk partition)"),
        (r"\bswapoff\b",         "swapoff (memory pressure weapon)"),
        (r"chown\s+-R\s+/",      "chown -R / (recursive)"),
        (r"chmod\s+-R\s+/",      "chmod -R / (recursive)"),
    ]
    for rx, label in simple:
        if re.search(rx, cmd):
            matched = label
            break
    if matched is None and re.search(r"\brm\b", cmd) and re.search(r"\s-[a-zA-Z]*[rR]", cmd) \
       and re.search(r"(?:^|\s)(?:/|/\*|~|~/\*)(?:\s|$)", cmd):
        matched = "rm -rf on / , /* or ~ (recursive destruction)"
    if matched is None and re.search(r"\bdd\b", cmd) and "if=" in cmd and "of=" in cmd:
        matched = "dd if= of= (raw write)"
    if matched is None and "/dev/" in cmd and "of=" in cmd:
        matched = "raw device write (/dev/ + of=)"
    if matched is None:
        return

    try:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        with open(LOG, "a") as f:
            f.write(datetime.datetime.now().isoformat(timespec="seconds")
                    + "\tPreToolUse\t" + tool + "\tpattern=" + matched
                    + "\tcmd=" + cmd.replace("\n", "\\n") + "\n")
    except Exception:
        pass

    sys.stderr.write(
        "MYTHOS safety guard: dangerous primitive detected (" + matched + "). "
        "Confirm intentionally with the human, then re-run. Escape-harness rule: never leave "
        "modprobe/core_pattern armed; restore-and-verify after every run."
    )
    sys.exit(2)

if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
