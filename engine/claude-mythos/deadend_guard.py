#!/usr/bin/env python3
"""
HOOK 2/10 — deadend_guard  (PreToolUse: Bash, BLOCKING)

Reads STATE/DEADENDS.md 'Active deadends' table. BLOCKS a probe that would re-hit a
surface already killed as an L3 infra identity gate (waf/egress/edge/identity/cloud-armor
/middlebox/caddy/f5), or that repeats a method already tried against a dead surface.
Enforces L3 / P05: re-probing an egress-identity gate the same way is banned; walls are
maps, not retries.

A deadend recorded on HTTP status ALONE is not an L3 gate — those rows (no error class,
no infra keyword) are ignored here, matching the template's 'reopen it' rule.
Fails OPEN on any uncertainty.
"""
import re
import mythos_hooklib as H

INFRA = re.compile(r'\b(waf|egress|edge|identity|infra|cloud.?armor|middlebox|caddy|'
                   r'f5|akamai|cloudflare|fastly|imperva|source.?ip|tls)\b', re.I)
METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD", "TRACE", "CONNECT")


def active_rows(txt):
    rows, grab = [], False
    for ln in txt.splitlines():
        s = ln.strip()
        if s.startswith("## "):
            grab = "active deadend" in s.lower()
            continue
        if grab and s.startswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            # skip header / separator / placeholder rows
            joined = " ".join(cells)
            if (not joined or set(joined) <= set("-: ") or "Surface" in cells[0]
                    or joined.replace("—", "").strip() == ""):
                continue
            rows.append(cells)
    return rows


def main():
    d = H.read_payload()
    if d is None:
        return
    tool, ti = H.tool_and_input(d)
    if tool != "Bash":
        return
    cmd = H.command_of(ti)
    hosts = H.request_hosts(cmd)
    if not hosts:
        return
    prog = H.resolve_prog(cmd, tool)
    if not prog:
        return
    txt = H.read_state(prog, "DEADENDS.md")
    if not txt:
        return
    method = H.http_method(cmd)

    for cells in active_rows(txt):
        row = " ".join(cells)
        gate_cell = cells[1] if len(cells) > 1 else ""
        class_cell = cells[2] if len(cells) > 2 else ""
        # domains named anywhere in the row
        row_hosts = {dom.lower().rstrip(".") for _w, dom in H.DOMAIN_RE.findall(row)}
        if not row_hosts:
            continue
        hit = next((h for h in hosts if any(H.host_matches(h, rh) or H.host_matches(rh, h)
                                            for rh in row_hosts)), None)
        if not hit:
            continue
        is_l3 = bool(INFRA.search(gate_cell) or INFRA.search(row))
        has_class = bool(class_cell and class_cell not in ("—", "-", ""))
        tried = {m for m in METHODS if re.search(r'\b' + m + r'\b', row)}
        if is_l3 and has_class:
            H.block("deadend_guard: %s is a logged L3 infra gate in %s/STATE/DEADENDS.md "
                    "(%s). Same method+host+scheme is DEAD — do not re-probe it. "
                    "Reopen only with a genuinely new class." % (hit, prog, gate_cell[:60]))
        if has_class and method in tried:
            H.block("deadend_guard: %s %s already recorded dead in DEADENDS.md "
                    "(class: %s). Loosen one axis or pick a new surface before re-firing."
                    % (method, hit, class_cell[:60]))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    import sys
    sys.exit(0)
