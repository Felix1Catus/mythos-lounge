#!/usr/bin/env python3
"""
takeover_check.py — dedicated subdomain-takeover confirmer for MYTHOS.

Second-source verification on top of bbot's baddns: for each candidate host it resolves the
CNAME chain, matches the target against a fingerprint table of takeover-able services (S3,
GitHub Pages, Heroku, Azure, Shopify, Fastly, …), and fetches the host to check for that
service's "unclaimed" body fingerprint. Classifies:
  VULNERABLE — CNAME to a known service AND the unclaimed fingerprint is served (file-and-chain)
  LIKELY     — CNAME to a known service whose target does NOT resolve (dangling)
  POTENTIAL  — CNAME to a known service, but claimed/active (note, usually safe)
  SAFE       — no takeover-shaped CNAME

Writes STATE/TAKEOVER.md + STATE/TAKEOVER_SIGNALS.ndjson (rank_surface folds VULNERABLE/LIKELY
into the host's takeover weight) and promotes VULNERABLE/LIKELY into LEADS.md — takeover is a
self-evident finding. Scope-gated, rate-limited, stdlib (dig + urllib).

USAGE
  takeover_check.py <prog> --host <host>
  takeover_check.py <prog> --from-surface [--top N]
  takeover_check.py <prog> --list <file>
  takeover_check.py --selftest
LOCATION: ~/targets/_shared/takeover_check.py   (bundle: shared/takeover_check.py)
"""
import sys, os, re, json, time, ssl, subprocess, shutil
import urllib.request as UR

HOME = os.path.expanduser("~")
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/140.0 Safari/537.36")
RATE, TIMEOUT = 0.3, 8

# service -> CNAME patterns + unclaimed-body fingerprints (+ nxdomain-is-vuln).
# Curated from the public can-i-take-over-xyz fingerprints; extend via
# ~/targets/_shared/takeover_fingerprints.json or <prog>/STATE/takeover_fingerprints.json.
SERVICES = [
    {"service": "AWS/S3", "cname": [r"s3[.-].*amazonaws\.com", r"s3-website"],
     "fp": ["NoSuchBucket", "The specified bucket does not exist"], "nx": True},
    {"service": "GitHub Pages", "cname": [r"\.github\.io$"],
     "fp": ["There isn't a GitHub Pages site here", "For root URLs (like http://example.com/) you must provide an index.html file"], "nx": False},
    {"service": "Heroku", "cname": [r"herokuapp\.com$", r"herokudns\.com$"],
     "fp": ["No such app", "herokucdn.com/error-pages/no-such-app.html"], "nx": False},
    {"service": "Azure", "cname": [r"azurewebsites\.net$", r"cloudapp\.net$", r"trafficmanager\.net$",
                                   r"blob\.core\.windows\.net$", r"azureedge\.net$"],
     "fp": ["404 Web Site not found", "The resource you are looking for has been removed"], "nx": True},
    {"service": "Shopify", "cname": [r"myshopify\.com$"],
     "fp": ["Sorry, this shop is currently unavailable", "Only one step left!"], "nx": False},
    {"service": "Fastly", "cname": [r"fastly\.net$", r"\.fastly"],
     "fp": ["Fastly error: unknown domain"], "nx": False},
    {"service": "Tumblr", "cname": [r"domains\.tumblr\.com$"],
     "fp": ["There's nothing here.", "Whatever you were looking for doesn't currently exist at this address"], "nx": False},
    {"service": "WordPress", "cname": [r"wordpress\.com$"],
     "fp": ["Do you want to register"], "nx": False},
    {"service": "Zendesk", "cname": [r"zendesk\.com$"],
     "fp": ["Help Center Closed"], "nx": False},
    {"service": "Bitbucket", "cname": [r"bitbucket\.io$"],
     "fp": ["Repository not found"], "nx": True},
    {"service": "Pantheon", "cname": [r"pantheonsite\.io$"],
     "fp": ["The gods are wise, but do not know of the site which you seek"], "nx": False},
    {"service": "Netlify", "cname": [r"netlify\.app$", r"netlify\.com$"],
     "fp": ["Not Found - Request ID"], "nx": True},
    {"service": "Surge.sh", "cname": [r"surge\.sh$"],
     "fp": ["project not found"], "nx": False},
    {"service": "Ghost", "cname": [r"ghost\.io$"],
     "fp": ["The thing you were looking for is no longer here, or never was"], "nx": False},
    {"service": "Readthedocs", "cname": [r"readthedocs\.io$"],
     "fp": ["unknown to Read the Docs"], "nx": False},
    {"service": "Unbounce", "cname": [r"unbouncepages\.com$"],
     "fp": ["The requested URL was not found on this server"], "nx": False},
]


def load_fingerprints(prog):
    svcs = [dict(s) for s in SERVICES]
    for p in (os.path.join(HOME, "targets", "_shared", "takeover_fingerprints.json"),
              os.path.join(HOME, "targets", prog, "STATE", "takeover_fingerprints.json")):
        try:
            svcs.extend(json.load(open(p)))
        except Exception:
            pass
    return svcs


def match_service(cname, svcs):
    c = (cname or "").lower().rstrip(".")
    if not c:
        return None
    for s in svcs:
        for pat in s["cname"]:
            if re.search(pat, c):
                return s
    return None


def classify(host, cname, cname_resolves, body, svcs):
    """Pure classifier (unit-tested offline)."""
    svc = match_service(cname, svcs)
    if not svc:
        return "SAFE", "", ""
    b = body or ""
    for fp in svc["fp"]:
        if fp in b:
            return "VULNERABLE", svc["service"], fp[:60]
    if not cname_resolves and svc.get("nx"):
        return "LIKELY", svc["service"], "CNAME target does not resolve (dangling)"
    return "POTENTIAL", svc["service"], ""


# ---- live helpers (dig if present, else DNS-over-HTTPS; no external dep needed) ----
_DNS_TYPE = {"A": 1, "AAAA": 28, "CNAME": 5}


def _dig(host, rtype):
    if not shutil.which("dig"):
        return None  # signal "dig unavailable" so caller falls back to DoH
    try:
        out = subprocess.run(["dig", "+short", rtype, host, "@1.1.1.1"],
                             capture_output=True, text=True, timeout=10).stdout
        return [x.strip().rstrip(".") for x in out.split() if x.strip()]
    except Exception:
        return []


def _doh(host, rtype):
    try:
        req = UR.Request("https://dns.google/resolve?name=%s&type=%s" % (host, rtype),
                         headers={"User-Agent": UA, "Accept": "application/dns-json"})
        with UR.urlopen(req, timeout=TIMEOUT) as r:
            d = json.loads(r.read(200_000).decode("utf-8", "replace"))
        want = _DNS_TYPE.get(rtype.upper())
        return [str(a.get("data", "")).rstrip(".") for a in (d.get("Answer") or [])
                if a.get("type") == want]
    except Exception:
        return []


def dns(host, rtype):
    recs = _dig(host, rtype)
    if recs is None:               # dig not installed -> DoH
        recs = _doh(host, rtype)
    return recs


def cname_of(host):
    recs = dns(host, "CNAME")
    return recs[0] if recs else ""


def resolves(host):
    return bool(dns(host, "A")) or bool(dns(host, "AAAA"))


def fetch(host):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
    for scheme in ("https", "http"):
        try:
            req = UR.Request("%s://%s/" % (scheme, host), headers={"User-Agent": UA})
            with UR.urlopen(req, timeout=TIMEOUT, context=ctx) as r:
                return r.read(400_000).decode("utf-8", "replace")
        except Exception as e:
            # a 404 page still carries the fingerprint — read the error body
            body = getattr(e, "read", None)
            if body:
                try:
                    return e.read(400_000).decode("utf-8", "replace")
                except Exception:
                    pass
    return ""


# ---- scope --------------------------------------------------------------------
DOMAIN_RE = re.compile(r'(?<![\w.-])(\*\.)?((?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+'
                       r'[a-z]{2,24})(?![\w-])', re.I)


def scope_roots(prog):
    try:
        txt = open(os.path.join(HOME, "targets", prog, "STATE", "SCOPE.md"),
                   encoding="utf-8", errors="replace").read()
    except Exception:
        return set()
    sec, grab = [], False
    for ln in txt.splitlines():
        if ln.strip().startswith("## "):
            grab = "in scope" in ln.lower(); continue
        if grab:
            sec.append(ln)
    return {d.lower().rstrip(".") for _w, d in DOMAIN_RE.findall("\n".join(sec))
            if d.lower() not in ("example.com", "policy.url")}


def in_scope(host, roots):
    return (not roots) or any(host == r or host.endswith("." + r) for r in roots)


# ---- run ----------------------------------------------------------------------
def check_host(host, svcs):
    cname = cname_of(host)
    if not cname:
        return {"host": host, "cname": "", "verdict": "SAFE", "service": "", "hit": ""}
    cres = resolves(cname)
    body = fetch(host)
    verdict, service, hit = classify(host, cname, cres, body, svcs)
    return {"host": host, "cname": cname, "verdict": verdict, "service": service, "hit": hit}


def persist(prog, results):
    sdir = os.path.join(HOME, "targets", prog, "STATE")
    os.makedirs(sdir, exist_ok=True)
    rank = {"VULNERABLE": 0, "LIKELY": 1, "POTENTIAL": 2, "SAFE": 3}
    results = sorted(results, key=lambda r: rank.get(r["verdict"], 9))
    lines = ["# SUBDOMAIN TAKEOVER — %s" % prog, "",
             "> takeover_check.py (second-source, confirms bbot baddns). VULNERABLE = CNAME to a",
             "> known service AND its unclaimed fingerprint served. Claim it to prove (human-gated).", "",
             "| host | verdict | service | CNAME | fingerprint |", "|---|---|---|---|---|"]
    for r in results:
        lines.append("| %s | %s | %s | %s | %s |" %
                     (r["host"], r["verdict"], r["service"] or "-", r["cname"] or "-", r["hit"] or "-"))
    open(os.path.join(sdir, "TAKEOVER.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")

    # signals for rank_surface (only the actionable verdicts)
    sig = [r for r in results if r["verdict"] in ("VULNERABLE", "LIKELY")]
    sp = os.path.join(sdir, "TAKEOVER_SIGNALS.ndjson")
    open(sp, "w", encoding="utf-8").write(
        "\n".join(json.dumps({"host": r["host"], "verdict": r["verdict"],
                              "service": r["service"]}, ensure_ascii=False) for r in sig) +
        ("\n" if sig else ""))

    # promote to LEADS (takeover is self-evident impact)
    if sig:
        lp = os.path.join(sdir, "LEADS.md")
        try:
            cur = open(lp, encoding="utf-8", errors="replace").read()
        except Exception:
            cur = "# LEADS — %s\n" % prog
        B, E = "<!-- takeover:begin -->", "<!-- takeover:end -->"
        cur = re.sub(re.escape(B) + r".*?" + re.escape(E), "", cur, flags=re.S).rstrip()
        blk = [B, "## SUBDOMAIN TAKEOVER (takeover_check.py)"]
        for r in sig:
            blk.append("- [ ] **%s** — %s on %s (%s). Claim the resource to prove; human-gated."
                       % (r["host"], r["verdict"], r["service"], r["cname"]))
        blk.append(E)
        open(lp, "w", encoding="utf-8").write(cur + "\n\n" + "\n".join(blk) + "\n")
    return results


def hosts_from_surface(prog, top):
    p = os.path.join(HOME, "targets", prog, "STATE", "SURFACE_MAP.md")
    out = []
    try:
        for ln in open(p, encoding="utf-8", errors="replace"):
            m = re.match(r'\|\s*\d+\s*\|[^|]*\|\s*([^\s|]+)\s*\|', ln)
            if m and m.group(1) != "host":
                out.append(m.group(1))
    except Exception:
        pass
    return out[:top]


def main():
    if "--selftest" in sys.argv:
        return selftest()
    if len(sys.argv) < 2 or sys.argv[1].startswith("--"):
        print(__doc__); sys.exit(2)
    prog = sys.argv[1]
    roots = scope_roots(prog)
    svcs = load_fingerprints(prog)
    hosts = []
    if "--host" in sys.argv:
        hosts = [sys.argv[sys.argv.index("--host") + 1]]
    elif "--from-surface" in sys.argv:
        top = int(sys.argv[sys.argv.index("--top") + 1]) if "--top" in sys.argv else 25
        hosts = hosts_from_surface(prog, top)
    elif "--list" in sys.argv:
        f = sys.argv[sys.argv.index("--list") + 1]
        hosts = [l.strip() for l in open(f) if l.strip()]
    if not hosts:
        print("no hosts — use --host / --from-surface / --list"); sys.exit(1)
    results = []
    for h in hosts:
        if not in_scope(h, roots):
            print("  skip (out of scope): %s" % h); continue
        time.sleep(RATE)
        r = check_host(h, svcs)
        results.append(r)
        mark = {"VULNERABLE": "!!", "LIKELY": "! ", "POTENTIAL": "? ", "SAFE": "  "}.get(r["verdict"], "")
        print("  %s %-40s %-11s %s" % (mark, h, r["verdict"], r["service"]))
    persist(prog, results)
    v = sum(1 for r in results if r["verdict"] == "VULNERABLE")
    l = sum(1 for r in results if r["verdict"] == "LIKELY")
    print("-> STATE/TAKEOVER.md (%d vulnerable, %d likely) ; signals -> TAKEOVER_SIGNALS.ndjson" % (v, l))


def selftest():
    svcs = load_fingerprints("")
    ok = True
    def chk(n, c):
        nonlocal ok; print(("  PASS " if c else "  FAIL ") + n); ok = ok and c
    v, s, _ = classify("x.acme.com", "acme.s3.amazonaws.com", True,
                       "<html>...The specified bucket does not exist...</html>", svcs)
    chk("S3 unclaimed body -> VULNERABLE", v == "VULNERABLE" and s == "AWS/S3")
    v, s, _ = classify("gh.acme.com", "acme.github.io", True,
                       "<h1>There isn't a GitHub Pages site here.</h1>", svcs)
    chk("GitHub Pages fingerprint -> VULNERABLE", v == "VULNERABLE")
    v, _s, _ = classify("old.acme.com", "gone.s3-website-us-east-1.amazonaws.com", False, "", svcs)
    chk("dangling S3 CNAME (NXDOMAIN) -> LIKELY", v == "LIKELY")
    v, _s, _ = classify("live.acme.com", "shop.myshopify.com", True,
                        "<html>Welcome to our live shop</html>", svcs)
    chk("claimed Shopify (no fingerprint) -> POTENTIAL", v == "POTENTIAL")
    v, _s, _ = classify("www.acme.com", "acme.com.cdn.cloudflare.net", True, "<html>home</html>", svcs)
    chk("non-takeover CNAME -> SAFE", v == "SAFE")
    v, _s, _ = classify("plain.acme.com", "", True, "<html>home</html>", svcs)
    chk("no CNAME -> SAFE", v == "SAFE")
    print("selftest:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        print("takeover_check error:", e); sys.exit(1)
