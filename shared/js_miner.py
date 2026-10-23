#!/usr/bin/env python3
"""
js_miner.py — fetch a host's JS bundles and mine SECRETS + ENDPOINTS, feed the surface score.

Real keys and undocumented API routes hide in lazy-loaded JS chunks, not the HTML (surface_mine
doctrine). This fetches a live host's root HTML, BFS-fetches same-origin .js (recursing into
fetched JS for lazy chunks, capped), and extracts:
  · secrets  — tiered catalog (HIGH provider keys / MED / LOW), REDACTED in all shared output;
               raw HIGH secrets go to a chmod-600 file only (doctrine: secrets -> 600, never chat)
  · endpoints — /api, /v1, graphql, fetch()/axios/.get() targets, absolute same-host URLs

Writes recon/js/<host>.json (per-host detail) and appends a compact signal line to
STATE/JS_SIGNALS.ndjson, which rank_surface.py folds into each host's bug-likelihood score.

SCOPE-GATED: refuses a host not in STATE/SCOPE.md. Rate-limited, stdlib-only (urllib), read-only GETs.

USAGE
  js_miner.py <prog> --host <host>            # mine one host
  js_miner.py <prog> --from-surface [--top N] # mine the top-N hosts in SURFACE_MAP.md
  js_miner.py --selftest
LOCATION: ~/targets/_shared/js_miner.py   (bundle: shared/js_miner.py)
"""
import sys, os, re, json, time, hashlib, ssl
import urllib.request as UR

HOME = os.path.expanduser("~")
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/140.0 Safari/537.36")
BBH = os.environ.get("BBH_HEADER", "")   # optional bug-bounty header "Name: value"
CAP_FILES = 40
RATE = 0.2
TIMEOUT = 8

# ---- extraction catalogs ------------------------------------------------------
SECRETS = [
    ("HIGH", "private-key", re.compile(r'-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----')),
    ("HIGH", "aws-akid",    re.compile(r'\b(?:AKIA|ASIA)[0-9A-Z]{16}\b')),
    ("HIGH", "stripe-live",  re.compile(r'\bsk_live_[0-9A-Za-z]{16,}\b')),
    ("HIGH", "slack",        re.compile(r'\bxox[baprs]-[0-9A-Za-z-]{10,}\b')),
    ("HIGH", "github-pat",   re.compile(r'\bghp_[0-9A-Za-z]{30,}\b')),
    ("HIGH", "google-sa",    re.compile(r'"private_key_id"\s*:\s*"[0-9a-f]{20,}"')),
    ("MED",  "google-api",   re.compile(r'\bAIza[0-9A-Za-z_\-]{35}\b')),
    ("MED",  "firebase-db",  re.compile(r'https://[\w.-]+\.firebaseio\.com')),
    ("MED",  "jwt",          re.compile(r'\beyJ[0-9A-Za-z_\-]{8,}\.[0-9A-Za-z_\-]{8,}\.[0-9A-Za-z_\-]{4,}')),
    ("MED",  "assign-secret", re.compile(r'(?i)(?:api[_-]?key|secret|token|passwd|password|auth)'
                                         r'["\']?\s*[:=]\s*["\']([0-9A-Za-z._\-]{16,})["\']')),
    ("LOW",  "stripe-pub",   re.compile(r'\bpk_live_[0-9A-Za-z]{16,}\b')),
]
EP_PATTERNS = [
    re.compile(r'["\'`](\/(?:api|v\d+|graphql|rest|internal|admin|user|users|account|auth|oauth|'
               r'token|session|upload|file|download|payment|invoice|order|webhook)[\w\/.\-{}:]*)'),
    re.compile(r'(?:fetch|axios|\.(?:get|post|put|patch|delete))\s*\(\s*["\'`]([^"\'`]+)["\'`]'),
    re.compile(r'["\'`](https?:\/\/[\w.\-]+\/[\w\/.\-?=&{}:]+)["\'`]'),
]
SCRIPT_SRC = re.compile(r'<script[^>]+src=["\']([^"\']+)["\']', re.I)
JS_REF = re.compile(r'["\'`]([\w./\-]+\.js(?:\?[\w=.&-]*)?)["\'`]')


def sha(s):
    return hashlib.sha256(s.encode("utf-8", "replace")).hexdigest()


def redact(s):
    s = s.replace("\n", "")
    return (s[:4] + "…" + s[-3:]) if len(s) > 10 else "…"


# ---- scope gate ---------------------------------------------------------------
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


# ---- fetch --------------------------------------------------------------------
def fetch(url):
    req = UR.Request(url, headers={"User-Agent": UA})
    if BBH and ":" in BBH:
        k, v = BBH.split(":", 1); req.add_header(k.strip(), v.strip())
    ctx = ssl.create_default_context()
    ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE  # research posture; -k equiv
    try:
        with UR.urlopen(req, timeout=TIMEOUT, context=ctx) as r:
            return r.read(2_000_000).decode("utf-8", "replace")
    except Exception:
        return ""


def mine_host(host):
    base = None
    html = ""
    for scheme in ("https", "http"):
        html = fetch("%s://%s/" % (scheme, host))
        if html:
            base = "%s://%s" % (scheme, host); break
    texts = {}
    if html:
        texts["/"] = html
    if not base:
        return texts
    # collect candidate JS urls from HTML + inline refs
    cand = set()
    for src in SCRIPT_SRC.findall(html) + JS_REF.findall(html):
        cand.add(src)
    fetched = 0
    seen = set()
    queue = list(cand)
    while queue and fetched < CAP_FILES:
        src = queue.pop(0)
        if src in seen:
            continue
        seen.add(src)
        if src.startswith("//"):
            u = "https:" + src
        elif src.startswith("http"):
            u = src
        elif src.startswith("/"):
            u = base + src
        else:
            u = base + "/" + src
        # same-origin only
        if host not in u:
            continue
        time.sleep(RATE)
        js = fetch(u)
        fetched += 1
        if js:
            texts[u] = js
            for ref in JS_REF.findall(js)[:20]:   # lazy chunks referenced inside JS
                if ref not in seen:
                    queue.append(ref)
    return texts


# ---- extract ------------------------------------------------------------------
def extract(texts):
    secrets, endpoints = [], set()
    for where, t in texts.items():
        for tier, name, rx in SECRETS:
            for m in rx.findall(t):
                val = m if isinstance(m, str) else (m[-1] if m else "")
                if val and len(val) >= 10:
                    secrets.append({"tier": tier, "name": name,
                                    "redacted": redact(val), "sha": sha(val)[:12],
                                    "where": where[:80], "_raw": val})
        for rx in EP_PATTERNS:
            for m in rx.findall(t):
                ep = m if isinstance(m, str) else m[0]
                if ep and len(ep) < 200:
                    endpoints.add(ep)
    # dedupe secrets by sha
    seen, uniq = set(), []
    for s in secrets:
        if s["sha"] in seen:
            continue
        seen.add(s["sha"]); uniq.append(s)
    return uniq, sorted(endpoints)


def persist(prog, host, secrets, endpoints, nfiles):
    d = os.path.join(HOME, "targets", prog, "recon", "js")
    os.makedirs(d, exist_ok=True)
    detail = {"host": host, "files_fetched": nfiles,
              "secrets": [{k: v for k, v in s.items() if k != "_raw"} for s in secrets],
              "endpoints": endpoints}
    open(os.path.join(d, re.sub(r'[^\w.-]', "_", host) + ".json"), "w",
         encoding="utf-8").write(json.dumps(detail, indent=2))
    # raw HIGH secrets -> chmod 600 only (never chat / never the shared ndjson)
    highs = [s for s in secrets if s["tier"] == "HIGH"]
    if highs:
        p = os.path.join(d, re.sub(r'[^\w.-]', "_", host) + ".secrets")
        with open(p, "w", encoding="utf-8") as f:
            for s in highs:
                f.write("%s\t%s\t%s\n" % (s["name"], s["where"], s["_raw"]))
        try: os.chmod(p, 0o600)
        except Exception: pass
    sig = {"host": host,
           "high": sum(1 for s in secrets if s["tier"] == "HIGH"),
           "med":  sum(1 for s in secrets if s["tier"] == "MED"),
           "low":  sum(1 for s in secrets if s["tier"] == "LOW"),
           "endpoints": len(endpoints),
           "top": [s["name"] for s in secrets[:3]],
           "sample_ep": endpoints[:5]}
    sp = os.path.join(HOME, "targets", prog, "STATE", "JS_SIGNALS.ndjson")
    os.makedirs(os.path.dirname(sp), exist_ok=True)
    # read-before-persist: drop any prior line for this host, re-append
    lines = []
    if os.path.exists(sp):
        for ln in open(sp, encoding="utf-8", errors="replace"):
            try:
                if json.loads(ln).get("host") != host:
                    lines.append(ln.rstrip("\n"))
            except Exception:
                pass
    lines.append(json.dumps(sig, ensure_ascii=False))
    open(sp, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    return sig


def top_hosts_from_surface(prog, top):
    p = os.path.join(HOME, "targets", prog, "STATE", "SURFACE_MAP.md")
    hosts = []
    try:
        for ln in open(p, encoding="utf-8", errors="replace"):
            m = re.match(r'\|\s*\d+\s*\|[^|]*\|\s*([^\s|]+)\s*\|', ln)
            if m and m.group(1) not in ("host",):
                hosts.append(m.group(1))
    except Exception:
        pass
    return hosts[:top]


def main():
    if "--selftest" in sys.argv:
        return selftest()
    if len(sys.argv) < 2 or sys.argv[1].startswith("--"):
        print(__doc__); sys.exit(2)
    prog = sys.argv[1]
    roots = scope_roots(prog)
    hosts = []
    if "--host" in sys.argv:
        hosts = [sys.argv[sys.argv.index("--host") + 1]]
    elif "--from-surface" in sys.argv:
        top = int(sys.argv[sys.argv.index("--top") + 1]) if "--top" in sys.argv else 10
        hosts = top_hosts_from_surface(prog, top)
    if not hosts:
        print("no hosts — use --host <h> or --from-surface (needs SURFACE_MAP.md)"); sys.exit(1)
    for h in hosts:
        if not in_scope(h, roots):
            print("  skip (out of scope): %s" % h); continue
        texts = mine_host(h)
        secrets, endpoints = extract(texts)
        sig = persist(prog, h, secrets, endpoints, len(texts))
        print("  %-40s files=%d secrets=H%d/M%d/L%d endpoints=%d"
              % (h, len(texts), sig["high"], sig["med"], sig["low"], sig["endpoints"]))
    print("-> STATE/JS_SIGNALS.ndjson ; re-rank: rank_surface.py %s" % prog)


# ---- selftest (offline: exercise the extractor) -------------------------------
SAMPLE_JS = r'''
  var cfg = {apiKey:"AIzaSyD-1234567890abcdefGHIJKLMNOPqrstu", token:"sk_live_abcDEF1234567890xyz"};
  const AWS="AKIAIOSFODNN7EXAMPLE";
  fetch("/api/v2/users/me"); axios.get("/internal/admin/flags");
  var jwt="eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.ABCdef123456";
  $.post("/payment/charge", data); const u="https://api.acme.com/v1/orders";
  import("./lazy.chunk.js");
'''


def selftest():
    secrets, endpoints = extract({"/app.js": SAMPLE_JS})
    names = {s["name"] for s in secrets}
    tiers = {s["tier"] for s in secrets}
    ok = True
    def chk(n, c):
        nonlocal ok; print(("  PASS " if c else "  FAIL ") + n); ok = ok and c
    chk("AWS key (HIGH) found", "aws-akid" in names)
    chk("stripe sk_live (HIGH) found", "stripe-live" in names)
    chk("google api (MED) found", "google-api" in names)
    chk("jwt (MED) found", "jwt" in names)
    chk("HIGH tier present", "HIGH" in tiers)
    chk("endpoints extracted", "/api/v2/users/me" in endpoints and "/internal/admin/flags" in endpoints)
    chk("payment route found", "/payment/charge" in endpoints)
    chk("secrets are redacted (no raw akid in shared view)",
        all("AKIAIOSFODNN7EXAMPLE" not in s["redacted"] for s in secrets))
    print("selftest:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        print("js_miner error:", e); sys.exit(1)
