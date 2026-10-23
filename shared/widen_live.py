#!/usr/bin/env python3
"""Resolve + live-fingerprint hot widen subs for wildcard-in-scope programs.
Output: <prog>/recon/widen_live_2026-10-16.txt  (sub | IPs | http_code | server | title)
Read-only GETs, 8s timeout, capped per program.
"""
import re, subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path("/home/RESEARCHER/targets")
PROGS = {"PROGRAM_87": 100, "PROGRAM_41": 150, "PROGRAM_97": 150, "h1-airbnb": 80,
         "h1-PROGRAM_76": 60, "PROGRAM_30": 20, "PROGRAM_59": 40, "unico": 50, "dynamic": 20}
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/155.0.0.0"

def hot_subs(prog, cap):
    f = ROOT/prog/"recon"/"widen_2026-10-16.txt"
    if not f.exists(): return []
    subs = []
    for line in f.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"): break  # stop at non-keyword section
        subs.append(line)
        if len(subs) >= cap: break
    return subs

def probe(sub):
    try:
        d = subprocess.run(["dig","+short","A",sub,"@1.1.1.1"], capture_output=True, text=True, timeout=10)
        ips = " ".join(x for x in d.stdout.split() if re.match(r"^\d+\.\d+\.\d+\.\d+$", x))
        if not ips: return (sub, "", "NXDOMAIN", "", "")
    except Exception:
        return (sub, "", "DNSERR", "", "")
    try:
        c = subprocess.run(["curl","-s","-o","/dev/null","--max-time","8",
            "-w","%{http_code}|%{header_json}", "-H",f"user-agent: {UA}", f"https://{sub}/"],
            capture_output=True, text=True, timeout=15)
        code, _, hj = c.stdout.partition("|")
        server = ""
        try:
            import json as J
            hdrs = J.loads(hj or "{}")
            server = (hdrs.get("server") or [""])[0]
        except Exception: pass
        return (sub, ips, code, server, "")
    except Exception:
        return (sub, ips, "ERR", "", "")

for prog, cap in PROGS.items():
    subs = hot_subs(prog, cap)
    if not subs: continue
    out = ROOT/prog/"recon"/"widen_live_2026-10-16.txt"
    with ThreadPoolExecutor(max_workers=10) as ex:
        res = list(ex.map(probe, subs))
    lines = [f"{s} | {ips} | {code} | {srv}" for s, ips, code, srv, _ in res]
    out.write_text("\n".join(lines) + "\n")
    live = [l for l in lines if " | 200 |" in l or " | 30" in l or " | 40" in l]
    print(f"{prog}: {len(subs)} probed, {sum(1 for _,ips,c,_,_ in res if ips)} resolve, {len(live)} answer HTTP", flush=True)
print("DONE")
