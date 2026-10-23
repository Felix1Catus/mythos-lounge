#!/usr/bin/env python3
"""
HOOK 6/10 — two_fail_loosener  (PostToolUse: Bash|WebFetch, advisory)

The two-fail rule (L1 / P02): the same error class twice on one surface means the shape is
still the one the author expected — loosen ONE axis before leaving the thread. This tracks
(surface -> last class + repeat count) in STATE/.loosen_streak.json and, on the 2nd identical
class, nudges with the axes not yet obviously tried in the command (type, nesting, sibling
key, encoding, alg, method).

Never blocks; one stdout line on the 2nd identical hit. Fails OPEN.
"""
import json, os
import mythos_hooklib as H

AXES = {
    "method":   lambda c: bool(__import__("re").search(r'-X\s', c)),
    "encoding": lambda c: ("%25" in c or "%2f" in c.lower() or "base64" in c.lower()),
    "content-type confusion": lambda c: ("content-type" in c.lower()),
    "nesting/array": lambda c: ("[]" in c or "][" in c),
    "sibling key": lambda c: False,
    "type (int/str/bool/null)": lambda c: False,
    "alg/downgrade": lambda c: ("alg" in c.lower()),
}


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
    surface = H.first_surface(cmd) or H.host_of(ti.get("url") or "")
    if not surface:
        return
    prog = H.resolve_prog(cmd, tool)
    if not prog:
        return
    klass = (H.error_class(text) or status).strip()
    key = surface + "|" + H.http_method(cmd)

    path = os.path.join(H.state_dir(prog), ".loosen_streak.json")
    state = {}
    try:
        with open(path) as f:
            state = json.load(f)
    except Exception:
        state = {}
    prev = state.get(key)
    count = 2 if (prev and prev.get("class") == klass) else 1
    state[key] = {"class": klass, "count": count}
    try:
        os.makedirs(H.state_dir(prog), exist_ok=True)
        with open(path, "w") as f:
            json.dump(state, f)
    except Exception:
        pass

    if count >= 2:
        untried = [name for name, seen in AXES.items() if not seen(cmd)]
        H.nudge("🔁 MYTHOS two_fail_loosener: '%s' twice on %s. Shape still matches the "
                "author's expectation. Loosen ONE axis before leaving: %s."
                % (klass[:50], surface, ", ".join(untried[:5])))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    import sys
    sys.exit(0)
