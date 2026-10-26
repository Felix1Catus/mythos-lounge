#!/usr/bin/env python3
"""
lean_enum.py — fast, dependency-free subdomain + web enumeration for MYTHOS.

The DEFAULT enumeration engine (bbot is now the opt-in `--deep` engine). It discovers
subdomains from Certificate Transparency logs (crt.sh), resolves them with the system
resolver, and does a light HTTP(S) probe (status / title / Server / CDN). It writes a
bbot-COMPATIBLE NDJSON event stream so rank_surface.py and the scan stage consume it with
ZERO changes:

  {"type":"DNS_NAME","host":H,"resolved_hosts":[ip,...]}
  {"type":"DNS_NAME_UNRESOLVED","host":H}
  {"type":"HTTP_RESPONSE","host":H,"data":{"url":U,"status_code":N,"title":T,"webserver":S},"tags":[...]}
  {"type":"TECHNOLOGY","host":H,"data":{"technology":"<Server header>"}}

Stdlib only — no Go binaries, no API keys. In scope by construction: every name queried and
probed derives from --roots. For huge/opaque scopes use `mythos <t> --deep` (full bbot).

USAGE
  lean_enum.py --roots a.com,b.com --out PATH [--timeout S] [--max N] [--selftest]
LOCATION: ~/targets/_shared/lean_enum.py   (bundle: shared/lean_enum.py)
"""
import sys, os, re, json, ssl, socket, argparse, time
import urllib.request, urllib.error, urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed

UA = "mythos-lean-enum/1.0 (authorized security research)"
CDN_HINTS = ("cloudflare", "cloudfront", "akamai", "fastly", "incapsula", "sucuri", "cf-ray",
             "x-amz-cf-id", "x-akamai", "x-fastly", "varnish", "google frontend", "x-azure")
TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)


def crtsh(root, timeout):
    """Best-effort CT-log name harvest for one root. Never raises."""
    names = set()
    url = "https://crt.sh/?q=%25." + urllib.parse.quote(root) + "&output=json"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8", "replace") or "[]")
        for row in data:
            for field in ("name_value", "common_name"):
                for n in str(row.get(field, "")).split("\n"):
                    n = n.strip().lower().lstrip("*.").rstrip(".")
                    if n and n.endswith(root) and re.match(r"^[a-z0-9.\-_]+$", n):
                        names.add(n)
    except Exception:
        pass
    return names


def certspotter(root, timeout):
    """Best-effort CT-log name harvest via certspotter (no key). Fallback for crt.sh. Never raises."""
    names = set()
    url = ("https://api.certspotter.com/v1/issuances?domain=" + urllib.parse.quote(root) +
           "&include_subdomains=true&expand=dns_names")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8", "replace") or "[]")
        for row in data:
            for n in (row.get("dns_names") or []):
                n = str(n).strip().lower().lstrip("*.").rstrip(".")
                if n and n.endswith(root) and re.match(r"^[a-z0-9.\-_]+$", n):
                    names.add(n)
    except Exception:
        pass
    return names


def resolve(host):
    try:
        infos = socket.getaddrinfo(host, None)
        return sorted({i[4][0] for i in infos})
    except Exception:
        return []


def probe(host, timeout):
    """Return (status, title, server, is_cdn, url) for the first scheme that answers, else None."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    for scheme in ("https", "http"):
        url = "%s://%s/" % (scheme, host)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA}, method="GET")
            resp = urllib.request.urlopen(req, timeout=timeout, context=ctx)
            status, headers, body = resp.status, resp.headers, resp.read(20000)
        except urllib.error.HTTPError as e:            # 4xx/5xx are valid, useful signals
            status, headers, body = e.code, e.headers, b""
            try: body = e.read(20000)
            except Exception: pass
        except Exception:
            continue                                   # scheme dead — try the next one
        title = ""
        m = TITLE_RE.search(body.decode("utf-8", "replace")) if body else None
        if m:
            title = re.sub(r"\s+", " ", m.group(1)).strip()[:80]
        server = (headers.get("Server") or "")[:60]
        blob = (" ".join("%s:%s" % (k, v) for k, v in headers.items()) + " " + server).lower()
        is_cdn = any(h in blob for h in CDN_HINTS)
        return status, title, server, is_cdn, url
    return None


def enumerate_roots(roots, out, timeout, cap):
    t0 = time.time()
    left = lambda: timeout - (time.time() - t0)
    cands = set()
    for root in roots:
        cands.update({root, "www." + root})
        if left() > 10:
            budget = min(60, max(10, left()))   # crt.sh is often slow — be patient
            cands.update(crtsh(root, budget))
            cands.update(certspotter(root, min(30, budget)))
    cands = sorted(cands)[:cap]
    sys.stdout.write("    lean_enum: %d candidate name(s) from %d root(s)\n" % (len(cands), len(roots)))
    sys.stdout.flush()

    resolved = {}
    with ThreadPoolExecutor(max_workers=40) as ex:
        futs = {ex.submit(resolve, h): h for h in cands}
        for f in as_completed(futs):
            if left() <= 2:
                break
            ips = f.result()
            if ips:
                resolved[futs[f]] = ips

    events, live = [], 0
    for h in cands:
        if h in resolved:
            events.append({"type": "DNS_NAME", "host": h, "resolved_hosts": resolved[h]})
        else:
            events.append({"type": "DNS_NAME_UNRESOLVED", "host": h})

    with ThreadPoolExecutor(max_workers=30) as ex:
        futs = {ex.submit(probe, h, 7): h for h in resolved}
        for f in as_completed(futs):
            if left() <= 1:
                break
            h = futs[f]
            res = f.result()
            if not res:
                continue
            status, title, server, is_cdn, url = res
            live += 1
            ev = {"type": "HTTP_RESPONSE", "host": h,
                  "data": {"url": url, "status_code": status, "title": title, "webserver": server},
                  "tags": (["cdn"] if is_cdn else []) + ["status-%d" % status]}
            events.append(ev)
            if server:
                events.append({"type": "TECHNOLOGY", "host": h, "data": {"technology": server}})

    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        for ev in events:
            f.write(json.dumps(ev) + "\n")
    sys.stdout.write("    lean_enum: %d resolved, %d live web host(s) -> %s\n"
                     % (len(resolved), live, out))
    sys.stdout.flush()
    return len(resolved)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--roots", default="")
    ap.add_argument("--out", default="")
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--max", type=int, default=1500)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        assert callable(crtsh) and callable(probe) and callable(resolve)
        print("lean_enum selftest OK")
        return 0
    roots = [r.strip().lower().rstrip(".") for r in a.roots.split(",") if r.strip()]
    if not roots or not a.out:
        print("lean_enum: --roots and --out are required", file=sys.stderr)
        return 2
    enumerate_roots(roots, a.out, a.timeout, a.max)
    return 0


if __name__ == "__main__":
    sys.exit(main())
