#!/usr/bin/env python3
"""Annotate widen results with scope status per program.
Reads <prog>/STATE/SCOPE.md, decides wildcard vs host-list, filters widen_2026-10-16.txt.
Writes _shared/widen_scoped_2026-10-16.md ranking in-scope new hot subs.
"""
import re
from pathlib import Path

ROOT = Path("/home/RESEARCHER/targets")

def scope_rule(prog):
    sf = ROOT/prog/"STATE"/"SCOPE.md"
    if not sf.exists(): return None, []
    t = sf.read_text(errors="ignore")
    wild = re.findall(r'\*\.\[?\`?([a-z0-9.-]+\.[a-z]{2,})', t)
    return t, wild

rows = []
for wf in sorted(ROOT.glob("*/recon/widen_2026-10-16.txt")):
    prog = wf.parts[-3]
    subs = [l.strip() for l in wf.read_text().splitlines()
            if l.strip() and not l.startswith("#")]
    t, wild = scope_rule(prog)
    if t is None:
        rows.append((prog, len(subs), "NO SCOPE FILE", [])); continue
    inscope = []
    for s in subs:
        hit = any(s.endswith(w.lstrip("*.")) or s == w.lstrip("*.") for w in wild)
        # explicit host listed in scope text?
        explicit = s in t
        if hit or explicit: inscope.append(s)
    oos_note = ""
    if re.search(r'ANY.*subdomain.*OOS|not listed.*OOS|ONLY authorized', t, re.I|re.S):
        oos_note = "HOST-LIST-ONLY (subs OOS unless listed)"
    rows.append((prog, len(subs), oos_note or ("wildcards: "+",".join(wild) if wild else "no wildcard seen"), inscope[:10]))

out = ["# widen results scope-filtered 2026-10-16\n"]
for prog, n, rule, ins in rows:
    out.append(f"## {prog} — {n} new subs — {rule}")
    for s in ins: out.append(f"  IN-SCOPE?: {s}")
(ROOT/"_shared"/"widen_scoped_2026-10-16.md").write_text("\n".join(out)+"\n")
print("\n".join(out)[:3000])
