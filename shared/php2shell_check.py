#!/usr/bin/env python3
"""
php2shell_check.py — PHP2Shell (CVE-2026-109618 / CVE-2026-109619) detection + gated PoC plan.

PHP2Shell is an UNAUTHENTICATED RCE in PHP's session.upload_progress / RFC1867 multipart
handler, chained with an OOM-longjmp dangling-pointer bug (CVSS 9.2). Affected: PHP 5.4.0 –
8.5.11. Fixed in 8.2.35, 8.3.36, 8.4.27, 8.5.12.  Refs:
  - https://github.com/hypnguyen1209/php2shell
  - https://github.com/9bie/php2shell-bypass-aslr-exp
  - https://sansec.io/research/php2shell · https://www.wiz.io/blog/php2shell-php-rce

This module does the SAFE, reliable part automatically — fingerprint the PHP version and
classify it against the vulnerable range — and feeds rank_surface. The actual exploit is a
build-specific memory-corruption chain that crashes/respawns workers; per MYTHOS doctrine that
is a destructive/irreversible action, so it is HUMAN-GATED: `--poc` only prepares a single-
target, benign-marker plan referencing the public PoCs + their Docker labs. It never fires an
exploit and never mass-targets. Authorized, in-scope testing only.

USAGE
  php2shell_check.py <prog> --host <host|url>        # safe version detection
  php2shell_check.py <prog> --from-surface [--top N] # detect across ranked hosts
  php2shell_check.py <prog> --poc --target <url> --authorized   # print gated PoC plan
  php2shell_check.py --selftest
LOCATION: ~/targets/_shared/php2shell_check.py   (bundle: shared/php2shell_check.py)
"""
import sys, os, re, json, time, ssl, uuid
import urllib.request as UR

HOME = os.path.expanduser("~")
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/140.0 Safari/537.36")
RATE, TIMEOUT = 0.3, 8
CVES = ["CVE-2026-109618", "CVE-2026-109619"]
CVSS = 9.2

# per-branch first FIXED version; branches 5.4..8.1 are EOL/unpatched (vulnerable in-range)
PATCHED = {(8, 2): (8, 2, 35), (8, 3): (8, 3, 36), (8, 4): (8, 4, 27), (8, 5): (8, 5, 12)}
MIN_AFFECTED = (5, 4, 0)
MAX_AFFECTED = (8, 5, 11)
PHP_VER_RE = re.compile(r'PHP/(\d+)\.(\d+)\.(\d+)', re.I)


def vtuple(v):
    m = re.findall(r'\d+', str(v))
    return tuple(int(x) for x in m[:3]) if m else ()


def classify_version(v):
    """Pure classifier: VULNERABLE / PATCHED / NOT-AFFECTED / UNKNOWN."""
    t = vtuple(v)
    if len(t) < 2:
        return "UNKNOWN"
    t3 = t if len(t) == 3 else (t + (0,))
    if t3 < MIN_AFFECTED:
        return "NOT-AFFECTED"
    branch = (t3[0], t3[1])
    if branch in PATCHED:
        return "PATCHED" if t3 >= PATCHED[branch] else "VULNERABLE"
    if branch > (8, 5):
        return "NOT-AFFECTED"            # future branch beyond the advisory
    if t3 <= MAX_AFFECTED:
        return "VULNERABLE"              # EOL branch (5.4..8.1) inside the affected range
    return "UNKNOWN"


# ---- live fingerprint ---------------------------------------------------------
def fetch_meta(host):
    """Return (php_version_or_'', is_php_bool, note) from headers + body. Single GET."""
    url = host if host.startswith("http") else "http://" + host
    ctx = ssl.create_default_context()
    ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
    tries = [url]
    if not host.startswith("http"):
        tries = ["https://" + host, "http://" + host]
    for u in tries:
        try:
            req = UR.Request(u, headers={"User-Agent": UA})
            with UR.urlopen(req, timeout=TIMEOUT, context=ctx) as r:
                hdrs = {k.lower(): v for k, v in r.headers.items()}
                body = r.read(60_000).decode("utf-8", "replace")
        except Exception as e:
            body = ""
            hdrs = {}
            if hasattr(e, "headers") and e.headers:
                hdrs = {k.lower(): v for k, v in e.headers.items()}
            if not hdrs:
                continue
        blob = " ".join([hdrs.get("server", ""), hdrs.get("x-powered-by", ""), body[:20000]])
        m = PHP_VER_RE.search(blob)
        ver = "%s.%s.%s" % m.groups() if m else ""
        is_php = bool(ver) or "php" in (hdrs.get("x-powered-by", "").lower()) \
            or "phpsessid" in " ".join(hdrs.values()).lower() or ".php" in body.lower()
        return ver, is_php, ("header" if m else ("php-no-version" if is_php else "not-php"))
    return "", False, "unreachable"


def check_host(host):
    ver, is_php, note = fetch_meta(host)
    if ver:
        verdict = {"VULNERABLE": "VULNERABLE", "PATCHED": "PATCHED",
                   "NOT-AFFECTED": "NOT-AFFECTED", "UNKNOWN": "PHP-UNKNOWN-VER"}[classify_version(ver)]
    elif is_php:
        verdict = "PHP-NO-VERSION"   # PHP present, version hidden -> can't rule out
    else:
        verdict = "NOT-PHP" if note != "unreachable" else "UNREACHABLE"
    return {"host": host, "verdict": verdict, "version": ver, "note": note}


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


def host_only(h):
    return re.sub(r'^https?://', '', h).split("/")[0].split(":")[0].lower()


def in_scope(host, roots):
    h = host_only(host)
    return (not roots) or any(h == r or h.endswith("." + r) for r in roots)


# ---- persist + signals --------------------------------------------------------
def persist(prog, results):
    sdir = os.path.join(HOME, "targets", prog, "STATE")
    os.makedirs(sdir, exist_ok=True)
    order = {"VULNERABLE": 0, "PHP-NO-VERSION": 1, "PHP-UNKNOWN-VER": 2,
             "PATCHED": 3, "NOT-AFFECTED": 4, "NOT-PHP": 5, "UNREACHABLE": 6}
    results = sorted(results, key=lambda r: order.get(r["verdict"], 9))
    lines = ["# PHP2SHELL — %s" % prog, "",
             "> CVE-2026-109618 / CVE-2026-109619 (CVSS 9.2). Version-based detection.",
             "> VULNERABLE = PHP in 5.4.0–8.5.11 and below its branch fix "
             "(8.2.35/8.3.36/8.4.27/8.5.12).", "",
             "| host | verdict | PHP version | source |", "|---|---|---|---|"]
    for r in results:
        lines.append("| %s | %s | %s | %s |" %
                     (r["host"], r["verdict"], r["version"] or "-", r["note"]))
    open(os.path.join(sdir, "PHP2SHELL.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")

    sig = [r for r in results if r["verdict"] in ("VULNERABLE", "PHP-NO-VERSION")]
    open(os.path.join(sdir, "PHP2SHELL_SIGNALS.ndjson"), "w", encoding="utf-8").write(
        "\n".join(json.dumps({"host": host_only(r["host"]), "verdict": r["verdict"],
                              "version": r["version"]}, ensure_ascii=False) for r in sig) +
        ("\n" if sig else ""))

    vuln = [r for r in results if r["verdict"] == "VULNERABLE"]
    if vuln:
        lp = os.path.join(sdir, "LEADS.md")
        try:
            cur = open(lp, encoding="utf-8", errors="replace").read()
        except Exception:
            cur = "# LEADS — %s\n" % prog
        B, E = "<!-- php2shell:begin -->", "<!-- php2shell:end -->"
        cur = re.sub(re.escape(B) + r".*?" + re.escape(E), "", cur, flags=re.S).rstrip()
        blk = [B, "## PHP2SHELL (CVE-2026-109618/109619) — version-vulnerable PHP"]
        for r in vuln:
            blk.append("- [ ] **%s** — PHP %s in vulnerable range. Confirm RCE with the gated "
                       "PoC (human-gated): php2shell_check.py %s --poc --target <url> --authorized"
                       % (r["host"], r["version"], prog))
        blk.append(E)
        open(lp, "w", encoding="utf-8").write(cur + "\n\n" + "\n".join(blk) + "\n")
    return results


# ---- gated PoC plan (NEVER executes an exploit) -------------------------------
def poc_plan(prog, target, authorized):
    roots = scope_roots(prog)
    if not in_scope(target, roots):
        print("REFUSED: %s is not in STATE/SCOPE.md for '%s'. PoC is authorized-scope only."
              % (host_only(target), prog)); sys.exit(2)
    if not authorized:
        print("REFUSED: PHP2Shell RCE crashes/respawns PHP workers (destructive, human-gated).\n"
              "Re-run with --authorized to confirm you have written permission for this exact\n"
              "target, and the tool will print the single-target PoC plan (it will NOT run it).")
        sys.exit(2)
    token = "P2S-" + uuid.uuid4().hex[:12]
    d = os.path.join(HOME, "targets", prog, "reports")
    os.makedirs(d, exist_ok=True)
    plan = """# PHP2Shell PoC plan — {target}
_Human-gated. MYTHOS does not fire this exploit for you (it crashes/respawns workers).
Run it yourself against this ONE authorized target (or, first, the reference Docker lab)._

Benign proof token: {token}
Prove RCE with a benign, non-destructive marker only — e.g. `id` or `echo {token}`.
Do NOT run destructive commands. One target. Capture the marker, then stop (file at the floor).

## Validate SAFELY in a local lab first (reference PoCs ship one)
    git clone https://github.com/hypnguyen1209/php2shell && cd php2shell
    docker compose up -d
    python3 php2shell.py 127.0.0.1 8860 -c 'echo {token}>/tmp/p2s'
    docker exec p2s-final cat /tmp/p2s        # expect: {token}
  or (official-config variant, recalculates offsets itself):
    git clone https://github.com/9bie/php2shell-bypass-aslr-exp && cd php2shell-bypass-aslr-exp
    ./pure/run_pure.sh
    python3 exploit.py --port 18110 --cmd 'echo {token}'

## Against the authorized target (only after lab success + written permission)
  Offsets are PHP-build-specific; derive them for the target's exact PHP/distro build.
    python3 php2shell.py {host} <port> -c 'echo {token}'    # benign marker only

## Evidence to capture (minimal, P14)
  - target PHP version (PHP2SHELL.md) + the marker '{token}' returned by the server
  - one request/response pair; nothing destructive, no secondary commands
Patched by 8.2.35 / 8.3.36 / 8.4.27 / 8.5.12. Mitigation: session.upload_progress.enabled=Off.
""".format(target=target, host=host_only(target), token=token)
    path = os.path.join(d, "php2shell_poc_%s.md" % host_only(target))
    open(path, "w", encoding="utf-8").write(plan)
    print("gated PoC plan written -> %s" % path)
    print("benign proof token: %s   (use `echo %s` / `id` only — human-gated, one target)"
          % (token, token))


# ---- main ---------------------------------------------------------------------
def main():
    if "--selftest" in sys.argv:
        return selftest()
    if len(sys.argv) < 2 or sys.argv[1].startswith("--"):
        print(__doc__); sys.exit(2)
    prog = sys.argv[1]
    if "--poc" in sys.argv:
        if "--target" not in sys.argv:
            print("--poc needs --target <url>"); sys.exit(2)
        return poc_plan(prog, sys.argv[sys.argv.index("--target") + 1], "--authorized" in sys.argv)

    roots = scope_roots(prog)
    hosts = []
    if "--host" in sys.argv:
        hosts = [sys.argv[sys.argv.index("--host") + 1]]
    elif "--from-surface" in sys.argv:
        top = int(sys.argv[sys.argv.index("--top") + 1]) if "--top" in sys.argv else 25
        p = os.path.join(HOME, "targets", prog, "STATE", "SURFACE_MAP.md")
        try:
            for ln in open(p, encoding="utf-8", errors="replace"):
                m = re.match(r'\|\s*\d+\s*\|[^|]*\|\s*([^\s|]+)\s*\|', ln)
                if m and m.group(1) != "host":
                    hosts.append(m.group(1))
        except Exception:
            pass
        hosts = hosts[:top]
    if not hosts:
        print("no hosts — use --host / --from-surface, or --poc --target"); sys.exit(1)
    results = []
    for h in hosts:
        if not in_scope(h, roots):
            print("  skip (out of scope): %s" % h); continue
        time.sleep(RATE)
        r = check_host(h)
        results.append(r)
        mark = {"VULNERABLE": "!!"}.get(r["verdict"], "  ")
        print("  %s %-40s %-16s PHP %s" % (mark, host_only(h), r["verdict"], r["version"] or "?"))
    persist(prog, results)
    v = sum(1 for r in results if r["verdict"] == "VULNERABLE")
    print("-> STATE/PHP2SHELL.md (%d vulnerable-version) ; signals -> PHP2SHELL_SIGNALS.ndjson" % v)
    if v:
        print("   confirm RCE on a vulnerable host (human-gated): "
              "php2shell_check.py %s --poc --target <url> --authorized" % prog)


def selftest():
    ok = True
    def chk(n, c):
        nonlocal ok; print(("  PASS " if c else "  FAIL ") + n); ok = ok and c
    cases = {"8.4.26": "VULNERABLE", "8.4.27": "PATCHED", "8.4.28": "PATCHED",
             "8.2.34": "VULNERABLE", "8.2.35": "PATCHED", "8.3.36": "PATCHED",
             "8.5.11": "VULNERABLE", "8.5.12": "PATCHED", "8.6.0": "NOT-AFFECTED",
             "8.1.33": "VULNERABLE", "7.4.33": "VULNERABLE", "5.4.0": "VULNERABLE",
             "5.3.29": "NOT-AFFECTED", "": "UNKNOWN"}
    for v, want in cases.items():
        got = classify_version(v)
        chk("classify %-8s -> %-12s" % (repr(v), want), got == want)
    chk("PHP version regex pulls from Server header",
        PHP_VER_RE.search("Apache/2.4 (Debian) PHP/8.4.26").group(0) == "PHP/8.4.26")
    # scope gate on PoC plan is enforced (in_scope False -> would refuse)
    chk("host_only strips scheme/port/path", host_only("https://a.b.com:8443/x") == "a.b.com")
    print("selftest:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        print("php2shell_check error:", e); sys.exit(1)
