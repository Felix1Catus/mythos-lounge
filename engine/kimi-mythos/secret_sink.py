#!/usr/bin/env python3
"""
HOOK 9/10 — secret_sink  (PreToolUse + PostToolUse: Bash|WebFetch)

M6 secret-to-sink + the token-leakage anti-pattern, in two directions:

  PostToolUse : scans the tool result for secrets (JWT, AWS/Google keys, private keys,
                bearer tokens, api_key/secret assignments). Logs a REDACTED locator to
                STATE/SECRETS_SEEN.md and the sha256 of each secret to STATE/.secrets_index
                (chmod 600). The secret value itself is never written to disk.
  PreToolUse  : hashes long tokens in an OUTBOUND command; if one matches a captured secret
                AND the destination host is not in SCOPE.md, BLOCK — a captured secret must
                not be exfiltrated off-scope.

Fails OPEN: no index, or scope unknown -> never blocks.
"""
import os, re
import mythos_hooklib as H

PATTERNS = [
    ("jwt", re.compile(r'eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{4,}')),
    ("aws-akid", re.compile(r'\b(AKIA|ASIA)[0-9A-Z]{16}\b')),
    ("google-api", re.compile(r'\bAIza[0-9A-Za-z_-]{35}\b')),
    ("slack", re.compile(r'\bxox[baprs]-[0-9A-Za-z-]{10,}\b')),
    ("private-key", re.compile(r'-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----')),
    ("bearer", re.compile(r'[Bb]earer\s+([A-Za-z0-9._\-]{20,})')),
    ("assign", re.compile(r'(?i)(?:api[_-]?key|secret|token|passwd|password)'
                          r'["\']?\s*[:=]\s*["\']?([A-Za-z0-9._\-]{16,})')),
]
TOKEN = re.compile(r'[A-Za-z0-9._\-]{20,}')


def index_path(prog):
    return os.path.join(H.state_dir(prog), ".secrets_index")


def load_index(prog):
    try:
        with open(index_path(prog)) as f:
            return set(x.strip() for x in f if x.strip())
    except Exception:
        return set()


def record(prog, kind, secret):
    h = H.sha(secret)
    idx = load_index(prog)
    if h in idx:
        return
    try:
        os.makedirs(H.state_dir(prog), exist_ok=True)
        p = index_path(prog)
        with open(p, "a") as f:
            f.write(h + "\n")
        os.chmod(p, 0o600)
    except Exception:
        pass
    red = secret[:4] + "…" + secret[-2:] if len(secret) > 8 else "…"
    H.append_state(prog, "SECRETS_SEEN.md",
                   "- [%s] %s  sha256=%s…  (%s)" % (H.now(), kind, h[:12], red))


def main():
    d = H.read_payload()
    if d is None:
        return
    ev = H.event_of(d)
    tool, ti = H.tool_and_input(d)
    if tool not in ("Bash", "WebFetch", "FetchURL"):
        return
    cmd = H.command_of(ti) or (ti.get("url") or "")
    prog = H.resolve_prog(cmd, tool)
    if not prog:
        return

    if ev == "PostToolUse":
        text = H.response_text(d)
        for kind, rx in PATTERNS:
            for m in rx.findall(text):
                sec = m if isinstance(m, str) else (m[-1] if m else "")
                if sec and len(sec) >= 12:
                    record(prog, kind, sec)
        return

    # PreToolUse: block exfil of a known secret to an off-scope host
    idx = load_index(prog)
    if not idx:
        return
    hosts = H.request_hosts(cmd)
    if not hosts:
        return
    allow, deny = H.load_scope(prog)
    if not allow:
        return  # scope unknown -> fail open
    offscope = [h for h in hosts if not H.is_local_host(h)
                and not any(H.host_matches(h, a) for a in allow)]
    if not offscope:
        return
    for tok in set(TOKEN.findall(cmd)):
        if H.sha(tok) in idx:
            H.block("secret_sink (M6): this request would send a captured secret "
                    "(sha256=%s…) to off-scope host %s. Token leakage blocked — a secret "
                    "seen in-scope must not be exfiltrated. Verify the destination."
                    % (H.sha(tok)[:12], offscope[0]))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    import sys
    sys.exit(0)
