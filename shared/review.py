#!/usr/bin/env python3
"""
review.py — static review + self-test harness for the MYTHOS toolkit.

Walks the shared tools and the hook modules, and for each Python file:
  · AST-parses + byte-compiles it (syntax / compile errors)
  · flags risky patterns: bare `except:`, mutable default args, `== None`, unused `import`
    of the obvious kind, leftover `pdb`/`breakpoint()`
  · runs its `--selftest` if it advertises one (so logic regressions surface here too)

Exit 0 only if nothing FAILED. Warnings do not fail the run. This is the "halt and review"
gate before shipping.

USAGE
  review.py                 # review shared/ + engine hook dirs (auto-detected)
  review.py <dir> [<dir>…]  # review specific dirs
LOCATION: ~/targets/_shared/review.py   (bundle: shared/review.py)
"""
import sys, os, ast, subprocess, re, py_compile, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
FAIL, WARN = [], []


def default_dirs():
    dirs = [HERE]
    home = os.path.expanduser("~")
    for d in (os.path.join(home, ".claude", "mythos"),
              os.path.join(home, ".kimi-code", "mythos")):
        if os.path.isdir(d):
            dirs.append(d)
    # bundle layout (running from the repo, not an install)
    repo = os.path.dirname(HERE)
    for d in (os.path.join(repo, "engine", "kimi-mythos"),
              os.path.join(repo, "engine", "claude-mythos")):
        if os.path.isdir(d):
            dirs.append(d)
    # de-dupe, keep order
    seen, out = set(), []
    for d in dirs:
        rp = os.path.realpath(d)
        if rp not in seen:
            seen.add(rp); out.append(d)
    return out


def has_selftest(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return "--selftest" in f.read()
    except Exception:
        return False


def lint_ast(path, src):
    issues = []
    try:
        tree = ast.parse(src, filename=path)
    except SyntaxError as e:
        FAIL.append("%s: SyntaxError line %s: %s" % (path, e.lineno, e.msg))
        return
    imported, used = set(), set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            issues.append("bare `except:` at line %d (use `except Exception`)" % node.lineno)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for d in node.args.defaults + node.args.kw_defaults:
                if isinstance(d, (ast.List, ast.Dict, ast.Set)):
                    issues.append("mutable default arg in %s() line %d" % (node.name, node.lineno))
        if isinstance(node, ast.Compare):
            for op, comp in zip(node.ops, node.comparators):
                if isinstance(op, (ast.Eq, ast.NotEq)) and isinstance(comp, ast.Constant) and comp.value is None:
                    issues.append("`== None` / `!= None` at line %d (use `is None`)" % node.lineno)
        if isinstance(node, ast.Import):
            for n in node.names:
                imported.add((n.asname or n.name).split(".")[0])
        if isinstance(node, ast.ImportFrom):
            for n in node.names:
                if n.name != "*":
                    imported.add(n.asname or n.name)
        if isinstance(node, ast.Name):
            used.add(node.id)
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            used.add(node.value.id)
    if re.search(r'\b(pdb\.set_trace|breakpoint)\s*\(', src):
        FAIL.append("%s: leftover debugger (pdb/breakpoint)" % path)
    for name in sorted(imported - used):
        if name not in ("annotations",):
            issues.append("possibly-unused import `%s`" % name)
    for i in issues:
        WARN.append("%s: %s" % (path, i))


def compile_check(path):
    try:
        py_compile.compile(path, doraise=True)
        return True
    except py_compile.PyCompileError as e:
        FAIL.append("%s: compile error: %s" % (path, str(e).splitlines()[-1][:120]))
        return False


def run_selftest(path):
    try:
        r = subprocess.run([sys.executable, path, "--selftest"],
                           capture_output=True, text=True, timeout=60,
                           env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    except Exception as e:
        FAIL.append("%s: --selftest crashed: %s" % (path, e)); return
    out = (r.stdout or "") + (r.stderr or "")
    if r.returncode != 0 or "FAIL" in out and "selftest: PASS" not in out:
        tail = "\n".join(out.strip().splitlines()[-3:])
        FAIL.append("%s: --selftest FAILED (rc=%d)\n      %s" % (path, r.returncode, tail))
    else:
        print("    selftest PASS: %s" % os.path.basename(path))


def main():
    dirs = sys.argv[1:] or default_dirs()
    pyfiles = []
    for d in dirs:
        for root, _dd, files in os.walk(d):
            if "__pycache__" in root:
                continue
            for fn in files:
                if fn.endswith(".py") and fn != "review.py":
                    pyfiles.append(os.path.join(root, fn))
    print("== MYTHOS review ==  %d python files across %d dir(s)" % (len(pyfiles), len(dirs)))
    for p in sorted(pyfiles):
        with open(p, encoding="utf-8", errors="replace") as f:
            src = f.read()
        lint_ast(p, src)
        if compile_check(p) and has_selftest(p):
            run_selftest(p)
    print("\n-- warnings (%d) --" % len(WARN))
    for w in WARN:
        print("  WARN " + w)
    print("\n-- failures (%d) --" % len(FAIL))
    for f in FAIL:
        print("  FAIL " + f)
    print("\nreview:", "CLEAN" if not FAIL else "%d FAILURE(S)" % len(FAIL))
    sys.exit(1 if FAIL else 0)


if __name__ == "__main__":
    main()
