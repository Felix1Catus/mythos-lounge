#!/usr/bin/env python3
"""
HOOK 3/10 — entropy_gate  (PreToolUse: Bash, BLOCKING)

Enforces L2 (entropy before attack): before a token prediction / brute / fuzz against an
identifier, the identifier's format must not already be known-random. Reads STATE/ENTROPY.md
(and TARGET_MODEL.md) for identifiers tagged high-entropy (uuidv4 / 128-bit / random /
ULID / crypto-random). If the command runs a brute/fuzz pattern against a parameter whose
name is logged high-entropy, it BLOCKS: prediction is dead on arrival, pivot to structure
(binding / race / leak channel / lifecycle).

Dormant until STATE/ENTROPY.md names an identifier — zero friction otherwise. Fails OPEN.
"""
import re
import mythos_hooklib as H

BRUTE = re.compile(r'\b(ffuf|hydra|patator|medusa|wfuzz|crunch|cewl)\b|--wordlist|'
                   r'(?:^|\s)-w\s+\S|FUZZ|\bseq\b|\{\d+\.\.\d+\}|range\(|\bintruder\b|'
                   r'\bbrute', re.I)
HIGH = re.compile(r'uuid\s*v?4|uuidv4|128[\s-]?bit|160[\s-]?bit|256[\s-]?bit|'
                  r'crypto(?:graphically)?[\s-]?random|\brandom\b|\bULID\b|\bnonce\b|'
                  r'high[\s-]?entropy|secure[\s-]?random', re.I)
# plausible identifier token on a line, e.g. session_token / api_key / csrf / reset_id
IDENT = re.compile(r'\b([a-z][a-z0-9_-]*(?:token|id|key|secret|'
                   r'nonce|code|hash|sig|session|csrf|otp))\b', re.I)


def high_entropy_idents(prog):
    idents = set()
    for fn in ("ENTROPY.md", "TARGET_MODEL.md"):
        for ln in H.read_state(prog, fn).splitlines():
            if HIGH.search(ln):
                for m in IDENT.findall(ln):
                    idents.add(m.lower())
    return idents


def main():
    d = H.read_payload()
    if d is None:
        return
    tool, ti = H.tool_and_input(d)
    if tool != "Bash":
        return
    cmd = H.command_of(ti)
    if not cmd or not BRUTE.search(cmd):
        return
    prog = H.resolve_prog(cmd, tool)
    if not prog:
        return
    idents = high_entropy_idents(prog)
    if not idents:
        return
    low = cmd.lower()
    hit = next((i for i in idents if re.search(r'\b' + re.escape(i) + r'\b', low)), None)
    if hit:
        H.block("entropy_gate (L2): '%s' is logged high-entropy in %s/STATE/ENTROPY.md. "
                "Prediction/brute is DEAD on arrival — pivot to structure: binding, race, "
                "leak channel, lifecycle. Remove it from ENTROPY.md only if the format "
                "claim is wrong." % (hit, prog))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    import sys
    sys.exit(0)
