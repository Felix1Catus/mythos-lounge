#!/usr/bin/env python3
"""Safely patch ~/targets/_shared/enum_pipeline.sh scope parsing."""
from pathlib import Path
import os, shutil, sys, tempfile
from datetime import datetime

home = Path.home()
target = Path(os.environ.get("PIPELINE", str(home / "targets/_shared/enum_pipeline.sh"))).expanduser()
if not target.is_file():
    sys.exit(f"ERROR: pipeline not found: {target}\nSet PIPELINE=/path/to/enum_pipeline.sh and rerun.")
text = target.read_text(encoding="utf-8")
start = text.find("# in-scope registrable domains")
end = text.find('DATE="$(date +%Y%m%d-%H%M%S)"', start if start >= 0 else 0)
if start < 0 or end < 0:
    sys.exit("ERROR: couldn't identify the expected scope-parser block. No changes made.")

replacement = r'''# Parse authorized roots from SCOPE.md.
# Supports either a dedicated "## In scope" section or a plain file containing
# one domain/URL per line. If other Markdown sections exist without an In scope
# section, fail closed rather than interpreting unrelated text as authorization.
ROOTS="$(python3 - "$SCOPE" <<'PY_SCOPE_PARSER'
import re, sys
from urllib.parse import urlsplit
from pathlib import Path

path = Path(sys.argv[1])
try:
    raw = path.read_text(encoding="utf-8-sig")
except (OSError, UnicodeError) as exc:
    print(f"scope parser: cannot read {path}: {exc}", file=sys.stderr)
    raise SystemExit(2)
lines = raw.splitlines()
heading_re = re.compile(r"^##\s+(.+?)\s*#*\s*$", re.I)
section_start = None
has_headings = False
for i, line in enumerate(lines):
    m = heading_re.match(line.strip())
    if m:
        has_headings = True
        if m.group(1).strip().lower().rstrip(":") == "in scope":
            section_start = i + 1
            break

if section_start is not None:
    content = []
    for line in lines[section_start:]:
        if heading_re.match(line.strip()):
            break
        content.append(line)
elif has_headings:
    print("scope parser: Markdown headings found, but no '## In scope' section; refusing to infer scope", file=sys.stderr)
    raise SystemExit(2)
else:
    # Legacy/simple format: the whole file is a list of domains/URLs, one per line.
    content = lines

# Accept a hostname, wildcard hostname, or URL as a whole list item. Do not
# harvest arbitrary domain-looking substrings from prose or unrelated text.
host_re = re.compile(r"^(?:\*\.)?(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$", re.I)
roots = set()
for original in content:
    line = original.strip()
    if not line or line.startswith(("<!--", "#")):
        continue
    line = re.sub(r"^[-*+]\s+", "", line).strip()
    line = line.strip("` \t")
    if not line or line.startswith("<!--"):
        continue
    candidate = line
    if re.match(r"^https?://", candidate, re.I):
        try:
            candidate = urlsplit(candidate).hostname or ""
        except ValueError:
            candidate = ""
    candidate = candidate.rstrip(".").lower()
    if not host_re.fullmatch(candidate):
        if not line.startswith(("<!--", ">")):
            print(f"scope parser: ignoring non-domain entry: {original.strip()!r}", file=sys.stderr)
        continue
    candidate = candidate.removeprefix("*.")
    if candidate in {"example.com", "policy.url"}:
        print(f"scope parser: ignoring placeholder: {candidate}", file=sys.stderr)
        continue
    roots.add(candidate)

if not roots:
    print("scope parser: no valid in-scope domains found", file=sys.stderr)
    raise SystemExit(3)
print(",".join(sorted(roots)))
PY_SCOPE_PARSER
)" || die "could not parse in-scope domains from $SCOPE — review STATE/SCOPE.md"
echo "scope roots: ${ROOTS//,/ , }"
'''
new_text = text[:start] + replacement + text[end:]
backup = target.with_name(target.name + ".bak.scope-parser-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
shutil.copy2(target, backup)
fd, tmpname = tempfile.mkstemp(prefix=target.name + ".tmp.", dir=str(target.parent))
try:
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
        f.write(new_text)
    os.chmod(tmpname, target.stat().st_mode)
    os.replace(tmpname, target)
except Exception:
    try:
        os.unlink(tmpname)
    except OSError:
        pass
    raise
print(f"Updated: {target}")
print(f"Backup:  {backup}")
print("Supports '## In scope' Markdown and plain one-domain-per-line scope files.")
print("Fails closed if other Markdown headings exist but no '## In scope' section is present.")
