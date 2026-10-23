#!/usr/bin/env python3
"""
HOOK 1/10 — scope_sentry  (PreToolUse: Bash|WebFetch|WebSearch, BLOCKING)

The single most report-ending mistake is a packet to an out-of-scope host. This reads
STATE/SCOPE.md for the active program, extracts the in-scope allowlist and the
exclusions, and BLOCKS any request whose destination host is excluded, or is a public
host absent from the allowlist. Enforces tendon 4 / program ethics.

Fails OPEN when scope cannot be judged (no SCOPE.md, empty allowlist) — a guard that
can't read the scope must never block legitimate work. Local/RFC1918/metadata hosts
pass (lab + SSRF payload targets are not egress-scope decisions).
"""
import mythos_hooklib as H


def main():
    d = H.read_payload()
    if d is None:
        return
    tool, ti = H.tool_and_input(d)

    hosts = set()
    if tool == "Bash":
        hosts = H.request_hosts(H.command_of(ti))
    elif tool in ("WebFetch", "FetchURL"):
        u = ti.get("url") or ""
        h = H.host_of(u)
        if h:
            hosts = {h}
    if not hosts:
        return

    blob = H.command_of(ti) or (ti.get("url") or "")
    prog = H.resolve_prog(blob, tool)
    if not prog:
        return
    allow, deny = H.load_scope(prog)
    if not allow and not deny:
        return  # scope unknown -> fail open

    excluded = [h for h in hosts if any(H.host_matches(h, x) for x in deny)]
    if excluded:
        H.block("scope_sentry: %s is OUT OF SCOPE (exclusion in %s/STATE/SCOPE.md). "
                "Do not probe it. Report-ending if ignored." % (excluded[0], prog))

    if allow:
        unknown = [h for h in hosts
                   if not H.is_local_host(h)
                   and not any(H.host_matches(h, a) for a in allow)]
        if unknown:
            H.block("scope_sentry: %s is NOT in the SCOPE.md allowlist for '%s'. "
                    "Confirm it is enrolled scope and add it to STATE/SCOPE.md, or stop. "
                    "In-scope roots: %s" % (unknown[0], prog, ", ".join(sorted(allow))[:200]))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    import sys
    sys.exit(0)
