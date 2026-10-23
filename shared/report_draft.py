#!/usr/bin/env python3
"""
report_draft.py — P14 report assembler for MYTHOS.

A COMPLETE reproducible chain gets its report drafted the SAME session. This stitches the
target's CHAIN_LEDGER (floor/ceiling/missing-link), SCOPE (affected host/program), and the
auto-captured evidence (evidence/auto/*.txt — the evidence_autolog hook) into
reports/DRAFT_<date>.md: a skeleton you finish, not file blind. It drafts at the PROVEN floor
and names the gap; it never claims the rung above.

USAGE
  report_draft.py <prog> [--title "..."]
  report_draft.py --selftest
LOCATION: ~/targets/_shared/report_draft.py   (bundle: shared/report_draft.py)
"""
import sys, os, re, glob, datetime

HOME = os.path.expanduser("~")


def field(txt, label):
    for raw in txt.splitlines():
        ln = raw.replace("*", "").strip()
        m = re.match(r'(?i)^[-\s]*' + re.escape(label) + r'[^:]*:\s*(.*)$', ln)
        if m:
            return m.group(1).strip(" —-")
    return ""


def scope_program(troot, prog):
    try:
        txt = open(os.path.join(troot, "STATE", "SCOPE.md"), encoding="utf-8", errors="replace").read()
    except Exception:
        return prog, ""
    m = re.search(r'(?im)^\s*[-*]?\s*(?:domains?|host)[^:]*:\s*(.+)$', txt)
    return prog, (m.group(1).strip() if m else "")


def evidence(troot, cap=5):
    files = sorted(glob.glob(os.path.join(troot, "evidence", "auto", "*.txt")),
                   key=os.path.getmtime, reverse=True)[:cap]
    items = []
    for f in files:
        try:
            t = open(f, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        repro = ""
        m = re.search(r'## repro\n(.+?)\n', t, re.S)
        if m:
            repro = m.group(1).strip()
        why = (re.search(r'why:\s*(.+)', t) or [None, ""])[1].strip() if "why:" in t else ""
        items.append((os.path.basename(f), why, repro))
    return items


def build(prog, troot, title):
    try:
        ledger = open(os.path.join(troot, "STATE", "CHAIN_LEDGER.md"), encoding="utf-8", errors="replace").read()
    except Exception:
        ledger = ""
    floor = field(ledger, "Floor") or "<the proven primitive>"
    ceiling = field(ledger, "Ceiling") or "<one more link>"
    missing = field(ledger, "Missing") or "<the gap — do NOT claim it>"
    _p, host = scope_program(troot, prog)
    evs = evidence(troot)
    now = datetime.date.today().isoformat()
    title = title or ("%s — <vuln class> on %s" % (prog, host or "<host>"))

    L = ["# %s" % title, "",
         "_Draft generated %s by report_draft.py — finish before filing (P14)._" % now, "",
         "## Summary", "<one-paragraph: what an attacker can do, in impact terms>", "",
         "## Affected", "- Program/scope: %s" % (host or prog), "- Target: <exact URL/endpoint>", "",
         "## Steps to reproduce"]
    if evs:
        for i, (fn, why, repro) in enumerate(evs, 1):
            L.append("%d. (%s) %s" % (i, why or "captured", ""))
            if repro:
                L.append("   ```\n   %s\n   ```" % repro.replace("\n", "\n   "))
    else:
        L.append("1. <request>  →  <response>  (no auto-evidence captured yet)")
    L += ["", "## Observed vs expected",
          "- Observed (PROVEN floor): %s" % floor,
          "- Expected: <what a correct server would do>", "",
          "## Impact",
          "- Proven now: %s" % floor,
          "- One link away (ceiling): %s" % ceiling,
          "- Missing link to that ceiling: %s" % missing,
          "> File at the floor. State the ceiling as the escalation path, not as achieved.", "",
          "## Remediation", "<server-side fix — authz check / validation / binding>", "",
          "## Evidence", ]
    L += ["- %s" % fn for fn, _w, _r in evs] or ["- <attach captures from evidence/>"]
    return title, "\n".join(L) + "\n"


def main():
    if "--selftest" in sys.argv:
        return selftest()
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(2)
    prog = sys.argv[1]
    title = None
    if "--title" in sys.argv:
        title = sys.argv[sys.argv.index("--title") + 1]
    troot = os.path.join(HOME, "targets", prog)
    if not os.path.isdir(troot):
        print("no target %s — scaffold with newtarget.sh first" % prog); sys.exit(1)
    _t, md = build(prog, troot, title)
    d = os.path.join(troot, "reports")
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, "DRAFT_%s.md" % datetime.date.today().isoformat())
    open(path, "w", encoding="utf-8").write(md)
    print("drafted -> %s" % path)


def selftest():
    import tempfile, shutil
    root = tempfile.mkdtemp(prefix="rep_")
    try:
        troot = os.path.join(root, "targets", "t")
        os.makedirs(os.path.join(troot, "STATE"))
        os.makedirs(os.path.join(troot, "evidence", "auto"))
        open(os.path.join(troot, "STATE", "CHAIN_LEDGER.md"), "w").write(
            "## Active chain\n- **Floor (proven):** IDOR read of victim invoice\n"
            "- **Ceiling (one more link):** write to victim invoice\n"
            "- **Missing Critical link:** CSRF token reuse\n")
        open(os.path.join(troot, "STATE", "SCOPE.md"), "w").write(
            "## In scope\n- domains: api.acme.com\n")
        open(os.path.join(troot, "evidence", "auto", "20261022_x.txt"), "w").write(
            "why: mutation-2xx\n\n## repro\ncurl -X POST https://api.acme.com/inv/42\n\n## response\n200 OK\n")
        title, md = build("t", troot, None)
        ok = True
        def chk(n, c):
            nonlocal ok; print(("  PASS " if c else "  FAIL ") + n); ok = ok and c
        chk("floor pulled into report", "IDOR read of victim invoice" in md)
        chk("ceiling present", "write to victim invoice" in md)
        chk("evidence repro embedded", "curl -X POST https://api.acme.com/inv/42" in md)
        chk("affected host from scope", "api.acme.com" in md)
        chk("has required sections", all(s in md for s in
            ("## Summary", "## Steps to reproduce", "## Impact", "## Remediation")))
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
        print("report_draft error:", e); sys.exit(1)
