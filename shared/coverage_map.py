#!/usr/bin/env python3
"""
coverage_map.py — P12 surface x class x status coverage ledger for MYTHOS.

Folds the error_oracle hook's STATE/ERROR_ORACLE.ndjson into a per-surface coverage table and
writes STATE/COVERAGE_MAP.md. "Covered" is a claim unless the empty cells are listed — so this
also prints, per surface, the HTTP methods NOT yet tried. That is where the next probe goes.

USAGE
  coverage_map.py <prog>
  coverage_map.py --selftest
LOCATION: ~/targets/_shared/coverage_map.py   (bundle: shared/coverage_map.py)
"""
import sys, os, json, datetime

HOME = os.path.expanduser("~")
ALL_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"]


def load(ndjson_path):
    surf = {}
    with open(ndjson_path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            s = r.get("surface")
            if not s:
                continue
            b = surf.setdefault(s, {"methods": set(), "statuses": set(),
                                    "classes": set(), "ts": ""})
            if r.get("method"):
                b["methods"].add(str(r["method"]).upper())
            if r.get("status"):
                b["statuses"].add(str(r["status"]))
            if r.get("class"):
                b["classes"].add(str(r["class"])[:40])
            ts = r.get("ts", "")
            if ts > b["ts"]:
                b["ts"] = ts
    return surf


def render(prog, surf):
    now = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    out = ["# COVERAGE MAP — %s" % prog, "",
           "> P12 surface x class x status ledger, folded from ERROR_ORACLE.ndjson.",
           "> 'Covered' is a lie without the empty cells: the 'methods-untested' column IS",
           "> the next-probe list. Generated: %s" % now, "",
           "| surface | methods tested | statuses | distinct error-classes | methods UNTESTED | last |",
           "|---|---|---|---|---|---|"]
    for s in sorted(surf):
        b = surf[s]
        untested = [m for m in ALL_METHODS if m not in b["methods"]]
        out.append("| %s | %s | %s | %d | %s | %s |" % (
            s,
            ",".join(sorted(b["methods"])) or "-",
            ",".join(sorted(b["statuses"])) or "-",
            len(b["classes"]),
            ",".join(untested) or "(all)",
            (b["ts"] or "-")[:19]))
    out += ["", "## Distinct error-classes per surface (each = one mapped internal branch, P10)"]
    for s in sorted(surf):
        cls = sorted(surf[s]["classes"])
        if cls:
            out.append("- **%s**: %s" % (s, " | ".join(cls)))
    return "\n".join(out) + "\n"


def main():
    if "--selftest" in sys.argv:
        return selftest()
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(2)
    prog = sys.argv[1]
    nd = os.path.join(HOME, "targets", prog, "STATE", "ERROR_ORACLE.ndjson")
    if not os.path.exists(nd):
        print("no ERROR_ORACLE.ndjson for %s — run some probes first (error_oracle hook fills it)" % prog)
        sys.exit(1)
    surf = load(nd)
    path = os.path.join(HOME, "targets", prog, "STATE", "COVERAGE_MAP.md")
    open(path, "w", encoding="utf-8").write(render(prog, surf))
    print("coverage: %d surfaces -> %s" % (len(surf), path))
    for s in sorted(surf):
        unt = [m for m in ALL_METHODS if m not in surf[s]["methods"]]
        print("  %-45s tested=%s  untested=%s" % (
            s[:45], ",".join(sorted(surf[s]["methods"])), ",".join(unt) or "(all)"))


def selftest():
    import tempfile, shutil
    root = tempfile.mkdtemp(prefix="cov_")
    try:
        sd = os.path.join(root, "targets", "t", "STATE")
        os.makedirs(sd)
        rows = [
            {"ts": "2026-10-22T10:00:00", "surface": "api.x/u", "status": "403", "class": "denied", "method": "GET"},
            {"ts": "2026-10-22T10:01:00", "surface": "api.x/u", "status": "200", "class": "ok", "method": "POST"},
            {"ts": "2026-10-22T10:02:00", "surface": "api.x/v", "status": "500", "class": "err", "method": "GET"},
        ]
        nd = os.path.join(sd, "ERROR_ORACLE.ndjson")
        open(nd, "w").write("\n".join(json.dumps(r) for r in rows) + "\n")
        surf = load(nd)
        md = render("t", surf)
        ok = True
        def chk(n, c):
            nonlocal ok; print(("  PASS " if c else "  FAIL ") + n); ok = ok and c
        chk("two surfaces parsed", len(surf) == 2)
        chk("api.x/u has GET+POST tested", surf["api.x/u"]["methods"] == {"GET", "POST"})
        chk("PUT listed untested for api.x/u", "PUT" in md and "methods UNTESTED" in md)
        chk("distinct classes counted", len(surf["api.x/u"]["classes"]) == 2)
        print("selftest:", "PASS" if ok else "FAIL")
        sys.exit(0 if ok else 1)
    finally:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as e:
        print("coverage_map error:", e); sys.exit(1)
