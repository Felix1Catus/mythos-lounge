#!/usr/bin/env python3
"""
rank_surface.py — turn a bbot scan into a RANKED attack surface for MYTHOS.

Parses a bbot NDJSON event stream (output.ndjson) and scores every discovered host by how
likely it is to carry a bug, so the hunter works DEPTH down a short prioritized queue instead
of spraying a flat host list. Writes STATE/SURFACE_MAP.md (full ranked table) and promotes the
top N into STATE/LEADS.md (auto-block), each with a first-probe stub.

There is no canonical "vulnerability rank" — it is a weighted score over the signals bbot's
modules already emit (httpx status/title/tech, baddns takeover, nuclei vulns, portscan). See
WEIGHTS below; tune freely.

USAGE
  rank_surface.py <prog> [--ndjson PATH] [--top N] [--no-scope-filter]
  rank_surface.py --selftest
LOCATION: ~/targets/_shared/rank_surface.py   (bundle: shared/rank_surface.py)
"""
import sys, os, re, json, glob, datetime

HOME = os.path.expanduser("~")

# ---- scoring weights (tunable) ------------------------------------------------
W = {
    "takeover": 40,          # dangling CNAME / subdomain takeover = near-certain finding
    "vuln": {"critical": 25, "high": 15, "medium": 6, "low": 2, "info": 0.3},
    "finding": 4,            # bbot FINDING (non-takeover), capped
    "auth_gated": 12,        # 401/403 -> authz/BOLA surface
    "server_error": 6,       # 500 / stacktrace / dir-listing
    "naked_origin": 10,      # live URL with no CDN/WAF in front -> directly attackable
    "interesting_name": 8,   # dev/staging/admin/api/... neglected-asset heuristic
    "open_port": 7,          # each non-80/443 open port (capped)
    "cve_confirmed": 10,     # per nuclei-confirmed CVE on the host, scaled by CVSS (capped)
    "cve_suspected": 4,      # per tech+version heuristic CVE match (no nuclei confirmation)
    "js_secret_high": 14,    # per HIGH secret mined from the host's JS (provider key etc.)
    "js_secret_med": 6,      # per MED secret (jwt, google api, assignment)
    "js_endpoint_unit": 0.4, # per undocumented endpoint mined from JS (capped)
    "clone_penalty": -9,     # identical (status,title,server) clone beyond the first few
}
JS_SECRET_CAP, JS_EP_CAP = 5, 20
CVE_CAP = 4  # max distinct CVEs that contribute (avoid one host dwarfing everything)

# ---- nuclei tech->CVE enrichment ---------------------------------------------
CVE_RE = re.compile(r'CVE-\d{4}-\d{4,7}', re.I)
CVSS_RE = re.compile(r'(?:cvss[^0-9]{0,8})(\d{1,2}(?:\.\d)?)', re.I)
# tech+version -> CVE heuristic table (suspected, used when nuclei did NOT confirm).
# Extendable via an optional JSON at ~/targets/_shared/cve_rules.json or <prog>/STATE/cve_rules.json
# (same shape). Keep curated + conservative — these are leads, not proof.
CVE_HEURISTICS = {
    "log4j":     [{"lt": "2.17.1", "cve": "CVE-2021-44228", "sev": "critical"}],
    "log4j-core":[{"lt": "2.17.1", "cve": "CVE-2021-44228", "sev": "critical"}],
    "jquery":    [{"lt": "3.5.0",  "cve": "CVE-2020-11022", "sev": "medium"}],
    "apache httpd": [{"eq": "2.4.49", "cve": "CVE-2021-41773", "sev": "high"},
                     {"eq": "2.4.50", "cve": "CVE-2021-41773", "sev": "high"}],
    "httpd":     [{"eq": "2.4.49", "cve": "CVE-2021-41773", "sev": "high"},
                  {"eq": "2.4.50", "cve": "CVE-2021-41773", "sev": "high"}],
    "openssl":   [{"ge": "3.0.0", "lt": "3.0.7", "cve": "CVE-2022-3786", "sev": "high"}],
    "wordpress": [{"lt": "5.8.3",  "cve": "CVE-2022-21661", "sev": "high"}],
    "bootstrap": [{"lt": "3.4.0",  "cve": "CVE-2018-14041", "sev": "low"}],
}


def _ver(v):
    try:
        return tuple(int(x) for x in re.findall(r'\d+', str(v))[:4])
    except Exception:
        return ()


def _vlt(a, b):  # version a < b, tuple-compared
    return bool(a) and bool(b) and a < b


def load_cve_rules(prog):
    rules = dict(CVE_HEURISTICS)
    for p in (os.path.join(HOME, "targets", "_shared", "cve_rules.json"),
              os.path.join(HOME, "targets", prog, "STATE", "cve_rules.json")):
        try:
            with open(p) as f:
                ext = json.load(f)
            for k, v in ext.items():
                rules[k.lower()] = v
        except Exception:
            pass
    return rules


def suspected_cves(product, version, rules):
    out = []
    prod = (product or "").lower().strip()
    for key, entries in rules.items():
        if key not in prod:
            continue
        pv = _ver(version)
        for e in entries:
            ok = True
            if "eq" in e:
                ok = pv == _ver(e["eq"])
            if "lt" in e:
                ok = ok and _vlt(pv, _ver(e["lt"]))
            if "ge" in e:
                ok = ok and (pv >= _ver(e["ge"]) if pv else False)
            if ok and (pv or "eq" not in e):
                out.append((e["cve"], e.get("sev", "medium")))
    return out
NAME_RE = re.compile(r'(?:^|[.\-_])(dev|stag|staging|test|uat|qa|sandbox|preprod|internal|'
                     r'intranet|admin|api|legacy|old|bak|backup|git|gitlab|jenkins|grafana|'
                     r'kibana|jira|confluence|vpn|dash|portal|beta|demo|corp|s3|storage|'
                     r'vault|ci|build|debug)(?:[.\-_]|$)', re.I)
FINDING_CAP, PORT_CAP = 3, 3
CLONE_FREE = 3  # first N identical clones unpenalized


def host_of_event(ev):
    for k in ("host", "parent_host"):
        v = ev.get(k)
        if isinstance(v, str) and v:
            return v.lower().rstrip(".")
    d = ev.get("data")
    if isinstance(d, dict):
        for k in ("host", "url"):
            v = d.get(k)
            if isinstance(v, str) and v:
                m = re.search(r'https?://([^/:\s]+)', v)
                return (m.group(1) if m else v).lower().rstrip(".")
    if isinstance(d, str):
        m = re.search(r'https?://([^/:\s]+)', d)
        if m:
            return m.group(1).lower().rstrip(".")
    return ""


def tags_of(ev):
    t = ev.get("tags") or []
    return [str(x).lower() for x in t] if isinstance(t, list) else []


def status_from(ev, tags):
    d = ev.get("data")
    if isinstance(d, dict):
        s = d.get("status_code") or d.get("status")
        if s:
            try: return int(s)
            except Exception: pass
    for t in tags:
        m = re.match(r'status-(\d{3})', t)
        if m:
            return int(m.group(1))
    return None


def severity_from(ev, tags):
    d = ev.get("data")
    if isinstance(d, dict):
        s = (d.get("severity") or "").lower()
        if s in W["vuln"]:
            return s
    for t in tags:
        for sev in W["vuln"]:
            if t == sev or t == "severity-" + sev:
                return sev
    return "info"


def desc_of(ev):
    d = ev.get("data")
    if isinstance(d, dict):
        return " ".join(str(d.get(k, "")) for k in ("description", "name", "technology", "url"))
    return str(d) if d else ""


def parse(ndjson_path, prog=""):
    """Fold the event stream into {host: signal-bag}."""
    H = {}

    def bag(h):
        return H.setdefault(h, {"vulns": [], "findings": 0, "takeover": False,
                                "status": set(), "ports": set(), "tech": set(),
                                "cdn": False, "has_url": False,
                                "cves": set(), "cves_susp": set(), "cvss": 0.0,
                                "techv": set(), "title": "", "server": "",
                                "js_high": 0, "js_med": 0, "js_endpoints": 0})

    with open(ndjson_path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except Exception:
                continue
            if not isinstance(ev, dict):
                continue
            typ = (ev.get("type") or "").upper()
            host = host_of_event(ev)
            if not host:
                continue
            tags = tags_of(ev)
            b = bag(host)
            d = ev.get("data")
            low = (desc_of(ev) + " " + " ".join(tags)).lower()

            if typ in ("DNS_NAME", "DNS_NAME_UNRESOLVED"):
                pass  # just register the host
            elif typ in ("URL", "URL_UNVERIFIED", "HTTP_RESPONSE"):
                b["has_url"] = True
                st = status_from(ev, tags)
                if st:
                    b["status"].add(st)
                if isinstance(d, dict):
                    b["title"] = b["title"] or str(d.get("title", ""))[:80]
                    b["server"] = b["server"] or str(d.get("webserver", d.get("server", "")))[:40]
                if any("cdn" in t or "waf" in t or "cloudflare" in t or "akamai" in t for t in tags):
                    b["cdn"] = True
            elif typ == "OPEN_TCP_PORT":
                m = re.search(r':(\d+)$', str(d))
                p = int(m.group(1)) if m else ev.get("port")
                if p:
                    b["ports"].add(int(p))
            elif typ == "TECHNOLOGY":
                techstr = ""
                if isinstance(d, dict):
                    techstr = str(d.get("technology", ""))
                elif isinstance(d, str):
                    techstr = d
                if techstr:
                    b["tech"].add(techstr[:40])
                    # pull product + version e.g. "jquery 3.3.1" / "Apache httpd/2.4.49"
                    for m in re.finditer(r'([A-Za-z][\w .+-]*?)[ /]v?(\d+\.\d+(?:\.\d+)?)', techstr):
                        b["techv"].add((m.group(1).strip().lower(), m.group(2)))
            elif typ == "FINDING":
                if "takeover" in low:
                    b["takeover"] = True
                else:
                    b["findings"] += 1
            elif typ == "VULNERABILITY":
                if "takeover" in low:
                    b["takeover"] = True
                b["vulns"].append(severity_from(ev, tags))
            if "takeover" in low:
                b["takeover"] = True
            # confirmed CVEs (nuclei via bbot): CVE-IDs in description/tags + any CVSS number
            for cid in CVE_RE.findall(low):
                b["cves"].add(cid.upper())
            mcv = CVSS_RE.search(low)
            if mcv:
                try:
                    b["cvss"] = max(b["cvss"], float(mcv.group(1)))
                except Exception:
                    pass

    # suspected CVEs from tech+version heuristics (only where not already confirmed)
    rules = load_cve_rules(prog)
    for h, b in H.items():
        for prod, ver in b["techv"]:
            for cid, sev in suspected_cves(prod, ver, rules):
                if cid not in b["cves"]:
                    b["cves_susp"].add((cid, sev))
    return H


def score(H):
    # cluster signature -> count, to penalize farms of identical clones
    sig_count = {}
    for h, b in H.items():
        sig = (tuple(sorted(b["status"])), b["title"], b["server"])
        sig_count[sig] = sig_count.get(sig, 0) + 1
    sig_seen = {}

    ranked = []
    for h, b in H.items():
        s, why = 0.0, []
        if b["takeover"]:
            s += W["takeover"]; why.append("TAKEOVER")
        for sev in b["vulns"]:
            s += W["vuln"][sev]
        if b["vulns"]:
            why.append("vuln:" + ",".join(sorted(set(b["vulns"]))))
        if b["findings"]:
            add = min(b["findings"], FINDING_CAP) * W["finding"]
            s += add; why.append("finding x%d" % b["findings"])
        if b["status"] & {401, 403}:
            s += W["auth_gated"]; why.append("auth-gated")
        if any(x >= 500 for x in b["status"]):
            s += W["server_error"]; why.append("5xx")
        if b["has_url"] and not b["cdn"]:
            s += W["naked_origin"]; why.append("naked-origin")
        if NAME_RE.search(h):
            s += W["interesting_name"]; why.append("hot-name")
        extra = [p for p in b["ports"] if p not in (80, 443)]
        if extra:
            s += min(len(extra), PORT_CAP) * W["open_port"]
            why.append("ports:" + ",".join(map(str, sorted(extra)[:4])))
        cves = sorted(b["cves"])
        if cves:
            per = (b["cvss"] / 10.0) if b["cvss"] else 0.7   # CVSS-scaled; default ~7.0
            s += min(len(cves), CVE_CAP) * W["cve_confirmed"] * max(per, 0.4)
            why.append("CVE:" + ",".join(cves[:3]) + ("+" if len(cves) > 3 else ""))
        susp = sorted({c for c, _sev in b["cves_susp"]})
        if susp:
            s += min(len(susp), CVE_CAP) * W["cve_suspected"]
            why.append("cve?:" + ",".join(susp[:3]))
        if b["js_high"] or b["js_med"]:
            s += min(b["js_high"], JS_SECRET_CAP) * W["js_secret_high"]
            s += min(b["js_med"], JS_SECRET_CAP) * W["js_secret_med"]
            why.append("js-secrets:H%d/M%d" % (b["js_high"], b["js_med"]))
        if b["js_endpoints"]:
            s += min(b["js_endpoints"], JS_EP_CAP) * W["js_endpoint_unit"]
            why.append("js-endpoints:%d" % b["js_endpoints"])
        sig = (tuple(sorted(b["status"])), b["title"], b["server"])
        sig_seen[sig] = sig_seen.get(sig, 0) + 1
        if sig_count[sig] > CLONE_FREE and sig_seen[sig] > CLONE_FREE:
            s += W["clone_penalty"]; why.append("clone")
        ranked.append((round(s, 1), h, b, why))
    ranked.sort(key=lambda r: (-r[0], r[1]))
    return ranked


# ---- scope filter (standalone; mirrors scope_sentry's SCOPE.md parse) ---------
DOMAIN_RE = re.compile(r'(?<![\w.-])(\*\.)?((?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+'
                       r'[a-z]{2,24})(?![\w-])', re.I)


def scope_roots(prog):
    p = os.path.join(HOME, "targets", prog, "STATE", "SCOPE.md")
    try:
        txt = open(p, encoding="utf-8", errors="replace").read()
    except Exception:
        return set()
    sec, grab = [], False
    for ln in txt.splitlines():
        if ln.strip().startswith("## "):
            grab = "in scope" in ln.lower(); continue
        if grab:
            sec.append(ln)
    roots = set()
    for _w, dom in DOMAIN_RE.findall("\n".join(sec)):
        d = dom.lower().rstrip(".")
        if d not in ("example.com", "policy.url"):
            roots.add(d)
    return roots


def in_scope(host, roots):
    if not roots:
        return True
    return any(host == r or host.endswith("." + r) for r in roots)


# ---- JS miner signals (js_miner.py -> STATE/JS_SIGNALS.ndjson) ----------------
def load_js_signals(prog):
    p = os.path.join(HOME, "targets", prog, "STATE", "JS_SIGNALS.ndjson")
    out = {}
    try:
        for ln in open(p, encoding="utf-8", errors="replace"):
            ln = ln.strip()
            if not ln:
                continue
            r = json.loads(ln)
            if r.get("host"):
                out[r["host"].lower().rstrip(".")] = r
    except Exception:
        pass
    return out


def _blank_bag():
    return {"vulns": [], "findings": 0, "takeover": False, "status": set(),
            "ports": set(), "tech": set(), "cdn": False, "has_url": True,
            "cves": set(), "cves_susp": set(), "cvss": 0.0, "techv": set(),
            "title": "", "server": "", "js_high": 0, "js_med": 0, "js_endpoints": 0}


def apply_js(H, jsmap):
    """Fold js_miner signals into the host bags (creating bags for JS-only hosts)."""
    for host, r in jsmap.items():
        b = H.setdefault(host, _blank_bag())
        b["js_high"] = int(r.get("high", 0) or 0)
        b["js_med"] = int(r.get("med", 0) or 0)
        b["js_endpoints"] = int(r.get("endpoints", 0) or 0)
    return H


def load_takeover(prog):
    p = os.path.join(HOME, "targets", prog, "STATE", "TAKEOVER_SIGNALS.ndjson")
    out = {}
    try:
        for ln in open(p, encoding="utf-8", errors="replace"):
            ln = ln.strip()
            if not ln:
                continue
            r = json.loads(ln)
            if r.get("host") and r.get("verdict") in ("VULNERABLE", "LIKELY"):
                out[r["host"].lower().rstrip(".")] = r["verdict"]
    except Exception:
        pass
    return out


def apply_takeover(H, tmap):
    """A confirmed/likely takeover is the top-weight signal — mark the host."""
    for host in tmap:
        H.setdefault(host, _blank_bag())["takeover"] = True
    return H


def load_php2shell(prog):
    p = os.path.join(HOME, "targets", prog, "STATE", "PHP2SHELL_SIGNALS.ndjson")
    out = {}
    try:
        for ln in open(p, encoding="utf-8", errors="replace"):
            ln = ln.strip()
            if not ln:
                continue
            r = json.loads(ln)
            if r.get("host") and r.get("verdict") == "VULNERABLE":
                out[r["host"].lower().rstrip(".")] = r.get("version", "")
    except Exception:
        pass
    return out


def apply_php2shell(H, pmap):
    """A version-vulnerable PHP2Shell host carries a confirmed critical CVE pair."""
    for host in pmap:
        b = H.setdefault(host, _blank_bag())
        b["cves"].update(["CVE-2026-109618", "CVE-2026-109619"])
        b["cvss"] = max(b["cvss"], 9.2)
    return H


# ---- outputs ------------------------------------------------------------------
def write_surface_map(prog, ranked, roots, nd):
    sdir = os.path.join(HOME, "targets", prog, "STATE")
    os.makedirs(sdir, exist_ok=True)
    now = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    lines = ["# SURFACE MAP — %s" % prog,
             "",
             "> Ranked attack surface from bbot (%s). Score = weighted bug-likelihood; work" % nd,
             "> DEPTH from the top, not breadth. Regenerate: rank_surface.py %s" % prog,
             "> Generated: %s" % now, "",
             "| # | score | host | status | tech | CVEs | signals | scope |",
             "|---|---|---|---|---|---|---|---|"]
    for i, (s, h, b, why) in enumerate(ranked, 1):
        st = ",".join(map(str, sorted(b["status"]))) or "-"
        tech = ",".join(sorted(b["tech"]))[:30] or "-"
        cves = sorted(b["cves"]) + sorted("%s?" % c for c, _ in b["cves_susp"])
        cvecol = ",".join(cves[:4]) or "-"
        sc = "in" if in_scope(h, roots) else "OUT"
        lines.append("| %d | %s | %s | %s | %s | %s | %s | %s |"
                     % (i, s, h, st, tech, cvecol, ("; ".join(why))[:60] or "-", sc))
    open(os.path.join(sdir, "SURFACE_MAP.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    return len(ranked)


BEGIN = "<!-- rank_surface:begin -->"
END = "<!-- rank_surface:end -->"


def promote_leads(prog, ranked, roots, top):
    p = os.path.join(HOME, "targets", prog, "STATE", "LEADS.md")
    try:
        cur = open(p, encoding="utf-8", errors="replace").read()
    except Exception:
        cur = "# LEADS — %s\n" % prog
    cur = re.sub(re.escape(BEGIN) + r".*?" + re.escape(END), "", cur, flags=re.S).rstrip()
    picks = [r for r in ranked if in_scope(r[1], roots)][:top]
    blk = [BEGIN,
           "## AUTO-RANKED SURFACE (rank_surface.py, top %d) — %s"
           % (top, datetime.date.today().isoformat()),
           "> Each = highest bug-likelihood host. Design the first probe; strike ONE at a time.", ""]
    for s, h, b, why in picks:
        st = ",".join(map(str, sorted(b["status"]))) or "?"
        blk.append("- [ ] **%s** (score %s, %s) — %s" % (h, s, st, "; ".join(why) or "live host"))
        blk.append("      first-probe: <hypothesis + the ONE violating input + success signal>")
    blk.append(END)
    open(p, "w", encoding="utf-8").write(cur + "\n\n" + "\n".join(blk) + "\n")
    return len(picks)


def newest_ndjson(prog):
    base = os.path.join(HOME, "targets", prog, "recon")
    hits = glob.glob(os.path.join(base, "**", "output.ndjson"), recursive=True)
    return max(hits, key=os.path.getmtime) if hits else ""


# ---- selftest -----------------------------------------------------------------
SAMPLE = [
    {"type": "DNS_NAME", "host": "staging.acme.com"},
    {"type": "URL", "host": "staging.acme.com", "data": {"url": "https://staging.acme.com/",
     "status_code": 403, "title": "Login", "webserver": "nginx"}, "tags": ["status-403"]},
    {"type": "VULNERABILITY", "host": "takeover.acme.com",
     "data": {"severity": "high", "description": "subdomain takeover (unclaimed S3 CNAME)"}},
    {"type": "DNS_NAME", "host": "www.acme.com"},
    {"type": "URL", "host": "www.acme.com", "data": {"url": "https://www.acme.com/",
     "status_code": 200, "title": "Home", "webserver": "cloudflare"}, "tags": ["status-200", "cdn-cloudflare"]},
    {"type": "OPEN_TCP_PORT", "host": "api.acme.com", "data": "api.acme.com:8443"},
    {"type": "URL", "host": "api.acme.com", "data": {"url": "https://api.acme.com:8443/",
     "status_code": 200, "title": "api", "webserver": "kestrel"}, "tags": ["status-200"]},
]
# plus a farm of identical clones to prove the clone penalty
SAMPLE += [{"type": "URL", "host": "cdn%d.acme.com" % i,
            "data": {"url": "https://cdn%d.acme.com/" % i, "status_code": 200,
                     "title": "Home", "webserver": "cloudflare"},
            "tags": ["status-200", "cdn-cloudflare"]} for i in range(8)]
# nuclei-confirmed CVE (with CVSS) and a tech+version -> suspected CVE
SAMPLE += [
    {"type": "DNS_NAME", "host": "cve.acme.com"},
    {"type": "VULNERABILITY", "host": "cve.acme.com",
     "data": {"severity": "critical",
              "description": "Apache Log4j2 RCE (CVE-2021-44228) cvss: 10.0"}},
    {"type": "DNS_NAME", "host": "old.acme.com"},
    {"type": "URL", "host": "old.acme.com", "tags": ["status-200"],
     "data": {"url": "https://old.acme.com/", "status_code": 200, "title": "Old", "webserver": "nginx"}},
    {"type": "TECHNOLOGY", "host": "old.acme.com",
     "data": {"technology": "jquery 3.3.1", "url": "https://old.acme.com/"}},
]


def selftest():
    import tempfile
    fd, path = tempfile.mkstemp(suffix=".ndjson")
    with os.fdopen(fd, "w") as f:
        for ev in SAMPLE:
            f.write(json.dumps(ev) + "\n")
    H = parse(path, "t")
    os.unlink(path)
    apply_js(H, {"jsleak.acme.com": {"high": 2, "med": 1, "endpoints": 25}})
    apply_takeover(H, {"dangle.acme.com": "LIKELY"})
    apply_php2shell(H, {"php.acme.com": "8.4.26"})
    ranked = score(H)
    order = [h for _s, h, _b, _w in ranked]
    bag = {h: b for _s, h, b, _w in ranked}
    sc = {h: s for s, h, _b, _w in ranked}
    whym = {h: " ".join(w) for _s, h, _b, w in ranked}
    ok = True
    def chk(name, cond):
        nonlocal ok
        print(("  PASS " if cond else "  FAIL ") + name); ok = ok and cond
    top = order[0]
    chk("takeover host ranks #1", top == "takeover.acme.com")
    chk("auth-gated staging outranks plain www",
        order.index("staging.acme.com") < order.index("www.acme.com"))
    chk("nonstandard-port api scored > plain cdn clone", sc["api.acme.com"] > sc["cdn7.acme.com"])
    chk("clone farm penalized below a unique 200 host", sc["cdn7.acme.com"] < sc["api.acme.com"])
    chk("confirmed CVE extracted", "CVE-2021-44228" in bag["cve.acme.com"]["cves"])
    chk("confirmed-CVE host outranks plain www", sc["cve.acme.com"] > sc["www.acme.com"])
    chk("suspected CVE from jquery version", any(c == "CVE-2020-11022"
        for c, _s in bag["old.acme.com"]["cves_susp"]))
    chk("JS-secret host created + outranks plain www", sc["jsleak.acme.com"] > sc["www.acme.com"])
    chk("js signals shown in why", "js-secrets" in whym.get("jsleak.acme.com", ""))
    chk("takeover signal marks host", "TAKEOVER" in whym.get("dangle.acme.com", ""))
    chk("takeover host ranks at the top", sc["dangle.acme.com"] >= sc["www.acme.com"] + 30)
    chk("php2shell host carries the CVE pair", "CVE-2026-109618" in bag["php.acme.com"]["cves"])
    chk("php2shell host outranks plain www", sc["php.acme.com"] > sc["www.acme.com"])
    chk("every host scored", len(ranked) == len(H))
    print("selftest:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main():
    args = sys.argv[1:]
    if "--selftest" in args:
        sys.exit(selftest())
    if not args:
        print(__doc__); sys.exit(2)
    prog = args[0]
    nd = None
    top = 15
    no_scope = "--no-scope-filter" in args
    if "--ndjson" in args:
        nd = args[args.index("--ndjson") + 1]
    if "--top" in args:
        top = int(args[args.index("--top") + 1])
    if not nd:
        nd = newest_ndjson(prog)
    if not nd or not os.path.exists(nd):
        print("no bbot output.ndjson under ~/targets/%s/recon/ — run enum_pipeline.sh first" % prog)
        sys.exit(1)
    H = parse(nd, prog)
    apply_js(H, load_js_signals(prog))
    apply_takeover(H, load_takeover(prog))
    apply_php2shell(H, load_php2shell(prog))
    ranked = score(H)
    roots = set() if no_scope else scope_roots(prog)
    n = write_surface_map(prog, ranked, roots, os.path.basename(os.path.dirname(nd)))
    k = promote_leads(prog, ranked, roots, top)
    print("ranked %d hosts -> STATE/SURFACE_MAP.md ; promoted top %d -> STATE/LEADS.md" % (n, k))
    for s, h, b, why in ranked[:min(10, len(ranked))]:
        print("  %6s  %s  [%s]" % (s, h, "; ".join(why)[:60]))


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        print("rank_surface error:", e); sys.exit(1)
