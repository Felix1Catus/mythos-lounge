#!/usr/bin/env python3
"""
HOOK 12/12 — pow_detector  (PostToolUse: Bash|WebFetch, advisory)

DIVERGENCE PROTOCOL: when a response shows the server expects browser-computed state — a
proof-of-work, a signed/HMAC'd body, a nonce challenge, a JS/edge challenge (Cloudflare
Turnstile, cf-chl, hashcash) — guessing the envelope by hand burns the session. Intercept
the SPA's OWN submit in-flight and mutate that. This flags such a response once per surface.

Never blocks; one stdout line the first time a surface shows a challenge. Fails OPEN.
"""
import os, re
import mythos_hooklib as H

POW = re.compile(
    r'proof[\s_-]?of[\s_-]?work|\bhashcash\b|\bpow\b|x-pow|'
    r'cf[-_]chl|__cf_chl|turnstile|challenge-platform|just a moment|enable javascript|'
    r'invalid\s+signature|signature\s+(?:required|mismatch|invalid)|signed\s+request|'
    r'hmac\s+(?:mismatch|invalid|required)|missing\s+nonce|invalid\s+nonce|'
    r'captcha|recaptcha|h-captcha|hcaptcha', re.I)


def main():
    d = H.read_payload()
    if d is None:
        return
    tool, ti = H.tool_and_input(d)
    if tool not in ("Bash", "WebFetch", "FetchURL"):
        return
    cmd = H.command_of(ti) or (ti.get("url") or "")
    text = H.response_text(d)
    m = POW.search(text or "")
    if not m:
        return
    prog = H.resolve_prog(cmd, tool)
    if not prog:
        return
    surface = H.first_surface(cmd) or H.host_of(ti.get("url") or "")
    if not surface:
        return

    seen_path = os.path.join(H.state_dir(prog), ".pow_seen")
    seen = set()
    try:
        with open(seen_path) as f:
            seen = set(x.strip() for x in f if x.strip())
    except Exception:
        seen = set()
    if surface in seen:
        return
    try:
        os.makedirs(H.state_dir(prog), exist_ok=True)
        with open(seen_path, "a") as f:
            f.write(surface + "\n")
    except Exception:
        pass

    H.nudge("🧩 MYTHOS pow_detector (divergence protocol): %s expects browser-computed "
            "state ('%s'). Don't hand-guess the envelope — intercept the SPA's own submit "
            "in-flight and mutate that (probelib.load_profile_cookies / in-flight capture)."
            % (surface, m.group(0)[:40]))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    import sys
    sys.exit(0)
