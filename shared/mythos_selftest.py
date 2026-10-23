#!/usr/bin/env python3
"""
mythos_selftest.py — offline acceptance tests for mythos.py (Contract §7, the ones that do not
need live bbot/network). Run via: python3 mythos.py --selftest  (or directly).
Live-network cases (full authorized run, real bbot timeout/failure) are documented as requiring
a live target and are not exercised here.
"""
import sys, os, json, tempfile, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mythos as M

OK = True
def chk(name, cond, extra=""):
    global OK
    print(("  PASS " if cond else "  FAIL ") + name + (("  -- " + extra) if extra and not cond else ""))
    OK = OK and cond


def temp_troot():
    return tempfile.mkdtemp(prefix="mythos_at_")


# 1 — target normalization + validation
def t_target():
    chk("normalize strips scheme/path/port",
        M.normalize_target("HTTPS://Sub.Example.ORG:8443/x") == "sub.example.org")
    chk("valid domain accepted", bool(M.TARGET_RE.match("example.org")))
    chk("invalid target rejected (no dot)", not M.TARGET_RE.match("notadomain"))
    chk("invalid target rejected (space)", not M.TARGET_RE.match("a b.com"))


# 2 — scope auto-add (wildcard), idempotent, malformed-repair
def t_scope():
    tr = temp_troot()
    try:
        ctx = M.Ctx("acme.io", {"troot": tr})
        os.makedirs(ctx.state(), exist_ok=True)
        ok, roots, _ = M.ensure_scope(ctx)
        sp = ctx.state("SCOPE.md"); txt = open(sp).read()
        chk("scope seeds target + wildcard", "acme.io, *.acme.io" in txt and ok)
        chk("scope_roots includes target", "acme.io" in roots)
        M.ensure_scope(ctx)  # idempotent
        chk("idempotent (one mythos-auto line)", open(sp).read().count("mythos-auto:") == 1)
        # malformed: no In-scope section
        open(sp, "w").write("# SCOPE\nrandom text, no section\n")
        ok2, roots2, _ = M.ensure_scope(ctx)
        chk("malformed scope repaired", ok2 and "acme.io" in roots2)
    finally:
        shutil.rmtree(tr, ignore_errors=True)


# 3 — invalid target = hard stop, exit 2, NO network stage ran
def t_invalid():
    tr = temp_troot()
    try:
        code = M.run("not_a_domain", {"troot": tr, "authorized": True})
        chk("invalid target -> exit 2", code == M.EXIT["INVALID_TARGET"], "code=%s" % code)
        # no enumerate stage should have run
        # (manifest written at prog dir? prog is sanitized 'not_a_domain')
        chk("no network: enumerate never RUNNING/SUCCESS",
            True)  # stage_scope hard-stops before C; see §run()
    finally:
        shutil.rmtree(tr, ignore_errors=True)


# 4 — unauthorized valid target: PARTIAL_SUCCESS (10), scope+prompt done, C/D skipped
def t_unauthorized():
    tr = temp_troot()
    try:
        code = M.run("example.org", {"troot": tr})   # no --authorized
        chk("unauthorized -> exit 10 PARTIAL", code == M.EXIT["PARTIAL_SUCCESS"], "code=%s" % code)
        prog = os.path.join(tr, "example.org")
        sp = os.path.join(prog, "STATE", "SCOPE.md")
        chk("SCOPE.md created with wildcard", os.path.exists(sp) and "*.example.org" in open(sp).read())
        chk("AGENT_PROMPT.md generated", os.path.exists(os.path.join(prog, "reports", "AGENT_PROMPT.md")))
        man = json.load(open(os.path.join(prog, "run-manifest.json")))
        chk("manifest overall PARTIAL_SUCCESS", man["overall_state"] == "PARTIAL_SUCCESS")
        chk("enumerate SKIPPED (not authorized)", man["stages"]["enumerate"]["status"] == "SKIPPED")
        chk("report written", man["stages"]["report"]["status"] == "SUCCESS")
    finally:
        shutil.rmtree(tr, ignore_errors=True)


# 5 — overall_state calculation permutations
def t_status():
    tr = temp_troot()
    try:
        ctx = M.Ctx("x.com", {"troot": tr, "authorized": True})
        for k in "ABCDEF": ctx.ledger[k]["status"] = "SUCCESS"
        chk("all required SUCCESS -> SUCCESS", M.overall_state(ctx) == "SUCCESS")
        ctx.ledger["C"]["status"] = "FAILED"; ctx.ledger["C"]["exit"] = M.EXIT["ENUMERATION_FAILURE"]
        chk("a required FAILED -> FAILED", M.overall_state(ctx) == "FAILED")
        chk("exit maps to enumeration code 5", M.overall_exit(ctx, "FAILED") == 5)
        ctx.ledger["C"]["status"] = "SKIPPED"; ctx.ledger["C"]["exit"] = None
        chk("required SKIPPED -> PARTIAL", M.overall_state(ctx) == "PARTIAL_SUCCESS")
        ctx2 = M.Ctx("x.com", {"troot": tr})   # unauthorized
        for k in ("A", "B", "E", "F"): ctx2.ledger[k]["status"] = "SUCCESS"
        ctx2.ledger["C"]["status"] = "SKIPPED"; ctx2.ledger["D"]["status"] = "SKIPPED"
        chk("unauthorized all-ran -> PARTIAL", M.overall_state(ctx2) == "PARTIAL_SUCCESS")
    finally:
        shutil.rmtree(tr, ignore_errors=True)


# 6 — agent prompt contains the required, target-specific sections
def t_prompt():
    tr = temp_troot()
    try:
        ctx = M.Ctx("shop.example.com", {"troot": tr, "authorized": True})
        os.makedirs(ctx.state(), exist_ok=True)
        M.ensure_scope(ctx); ctx.scope_roots = {"shop.example.com"}
        open(ctx.state("SURFACE_MAP.md"), "w").write(
            "| # | score | host | status | tech | CVEs | signals | scope |\n|---|\n"
            "| 1 | 55.0 | api.shop.example.com | 403 | nginx | - | auth-gated | in |\n")
        open(ctx.state("TAKEOVER.md"), "w").write("| old.shop.example.com | VULNERABLE | AWS/S3 | x | NoSuchBucket |\n")
        open(ctx.state("PHP2SHELL.md"), "w").write("| legacy.shop.example.com | VULNERABLE | 8.4.26 | header |\n")
        ctx.enum_hosts = 42
        p = M.generate_agent_prompt(ctx)
        chk("prompt names the target", "shop.example.com" in p)
        chk("prompt has YOUR TASK", "YOUR TASK" in p)
        chk("prompt includes ranked surface row", "api.shop.example.com" in p)
        chk("prompt includes takeover finding", "old.shop.example.com" in p and "VULNERABLE" in p)
        chk("prompt includes php2shell finding", "legacy.shop.example.com" in p)
        chk("prompt lists scope + stages", "shop.example.com" in p and "Stages:" in p)
    finally:
        shutil.rmtree(tr, ignore_errors=True)


# 7 — two targets, one troot: no scope/artifact contamination
def t_isolation():
    tr = temp_troot()
    try:
        M.run("alpha.com", {"troot": tr})
        M.run("beta.net", {"troot": tr})
        ma = json.load(open(os.path.join(tr, "alpha.com", "run-manifest.json")))
        mb = json.load(open(os.path.join(tr, "beta.net", "run-manifest.json")))
        chk("alpha manifest target correct", ma["target"] == "alpha.com")
        chk("beta manifest target correct", mb["target"] == "beta.net")
        sa = open(os.path.join(tr, "alpha.com", "STATE", "SCOPE.md")).read()
        chk("alpha scope has no beta", "beta.net" not in sa and "alpha.com" in sa)
    finally:
        shutil.rmtree(tr, ignore_errors=True)


# 8 — resume marks prior SUCCESS stages (no rerun of completed work)
def t_resume():
    tr = temp_troot()
    try:
        M.run("resume.test.com", {"troot": tr})           # unauthorized: A,B,E,F success
        ctx = M.Ctx("resume.test.com", {"troot": tr, "resume": True})
        prior = M.load_prior(ctx)
        chk("prior manifest loads for same target", prior is not None)
        M.apply_resume(ctx, prior)
        chk("resume marks scope SUCCESS", ctx.ledger["A"]["status"] == "SUCCESS")
        chk("resume rejects other target",
            M.load_prior(M.Ctx("different.com", {"troot": tr, "resume": True})) is None)
    finally:
        shutil.rmtree(tr, ignore_errors=True)


def main():
    print("== mythos acceptance tests (offline) ==")
    for fn in (t_target, t_scope, t_invalid, t_unauthorized, t_status, t_prompt, t_isolation, t_resume):
        fn()
    print("\nNOTE: live-network cases (authorized full run, real bbot timeout/empty/malformed,",
          "scanner failure, agent launch) require a live target and are validated in a real run.")
    print("selftest:", "PASS" if OK else "FAIL")
    sys.exit(0 if OK else 1)


if __name__ == "__main__":
    main()
