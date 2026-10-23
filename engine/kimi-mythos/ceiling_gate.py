#!/usr/bin/env python3
"""
HOOK 10/10 — ceiling_gate  (Stop, BLOCKING once per session)

P11 / "escalate every finding to its highest ceiling": do not end a turn with a finding
sitting at the proven floor and no ceiling named. This reads STATE/CHAIN_LEDGER.md for the
active program; if the 'Floor (proven)' line has content but 'Ceiling (one more link)' or
'Missing Critical link' is still empty, it BLOCKS the stop once and demands the horizontal
sweep + second-order variants before ending.

Once per session (marker). No active target, or ledger complete -> silent. Fails OPEN.
"""
import os, re
import mythos_hooklib as H


def field(txt, label):
    # tolerate markdown bold where the colon sits inside the ** .. ** (e.g. **Floor (proven):**)
    for raw in txt.splitlines():
        ln = raw.replace("*", "").strip()
        m = re.match(r'(?i)^[-\s]*' + re.escape(label) + r'[^:]*:\s*(.*)$', ln)
        if m:
            return m.group(1).strip(" —-")
    return ""


def main():
    d = H.read_payload()
    if d is None:
        return
    prog = H.active_target()
    if not prog:
        return
    sess = H.session_of(d)
    marker = os.path.join(H.HOOK_DIR, "ceiling_nudged_" +
                          re.sub(r'[^A-Za-z0-9_.-]', '_', sess))
    if os.path.exists(marker):
        return
    txt = H.read_state(prog, "CHAIN_LEDGER.md")
    if not txt:
        return
    floor = field(txt, "Floor")
    ceiling = field(txt, "Ceiling")
    missing = field(txt, "Missing")
    if floor and not (ceiling and missing):
        try:
            open(marker, "w").write(H.now())
        except Exception:
            pass
        gap = "ceiling" if not ceiling else "missing-link"
        H.block("ceiling_gate (P11): active chain on '%s' has a proven floor (\"%s\") but "
                "no %s named in CHAIN_LEDGER.md. Don't stop at the floor — do the horizontal "
                "sweep + second-order variants, then name floor/ceiling/missing-link. If "
                "truly capped, write the gap (never claim the rung above)."
                % (prog, floor[:70], gap))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    import sys
    sys.exit(0)
