#!/usr/bin/env bash
# install.sh — one-command MYTHOS + Lounge installer (Linux / WSL / macOS).
# Non-destructive: backs up anything it overwrites to ~/.mythos-backup-<stamp>.
#
#   bash install.sh                 # doctrine + hooks + instruments, merge hooks into settings
#   bash install.sh --full-settings # also merge permissions/model/statusLine/outputStyle/effort
#   bash install.sh --with-bbot     # also install bbot via uv (managed py3.12, no sudo)
#   bash install.sh --full-settings --with-bbot
#
# Idempotent — safe to re-run to upgrade. Run from inside the bundle.
set -uo pipefail
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STAMP="$(date +%Y%m%d-%H%M%S)"
BK="$HOME/.mythos-backup-$STAMP"
FULL=0; BBOT=0
for a in "$@"; do case "$a" in --full-settings) FULL=1;; --with-bbot) BBOT=1;; esac; done
say(){ printf '\n\033[1m== %s ==\033[0m\n' "$*"; }
die(){ echo "install: $*" >&2; exit 1; }

say "0. Preconditions"
test -f "$SRC/engine/CLAUDE.core.md" || die "run from inside the bundle (engine/ not found at $SRC)"
for t in python3 rsync; do command -v "$t" >/dev/null || die "missing: $t"; done
echo "bundle=$SRC  HOME=$HOME"

say "1. Back up anything we overwrite -> $BK"
mkdir -p "$BK"
for p in "$HOME/.claude/CLAUDE.md" "$HOME/.claude/settings.json" "$HOME/.claude/mythos" \
         "$HOME/.kimi-code/mythos" "$HOME/.grok/rules" "$HOME/MYTHOS_CLAUDE_OS.txt"; do
  if [ -e "$p" ]; then rel="${p#$HOME/}"; mkdir -p "$BK/$(dirname "$rel")"; cp -r "$p" "$BK/$rel"; echo "backed up: $p"; fi
done

say "2. Trees"
mkdir -p "$HOME/.kimi-code" "$HOME/.claude/skills" "$HOME/.grok/rules" "$HOME/targets/_shared" "$HOME/targets/_gate/hooks"
rsync -a --delete "$SRC/engine/kimi-mythos/"   "$HOME/.kimi-code/mythos/"
rsync -a --delete "$SRC/engine/claude-mythos/" "$HOME/.claude/mythos/"
rsync -a          "$SRC/engine/grok-rules/"    "$HOME/.grok/rules/"
rsync -a          "$SRC/engine/skills/"        "$HOME/.claude/skills/"
rsync -a          "$SRC/lounge/"               "$HOME/targets/_shared/lounge/"
rsync -a          "$SRC/shared/"               "$HOME/targets/_shared/"
cp "$SRC/engine/CLAUDE.core.md"       "$HOME/.claude/CLAUDE.md"
cp "$SRC/engine/MYTHOS_CLAUDE_OS.txt" "$HOME/MYTHOS_CLAUDE_OS.txt"
echo "copied engine, skills, lounge, shared, CLAUDE.md, OS manual"

say "3. Normalize line endings + chmod"
find "$HOME/.kimi-code/mythos" "$HOME/.claude/mythos" "$HOME/targets/_shared" "$HOME/.grok/rules" \
     -type f \( -name '*.sh' -o -name '*.py' \) -print0 | xargs -0 sed -i 's/\r$//'
sed -i 's/\r$//' "$HOME/.claude/CLAUDE.md" 2>/dev/null || true
find "$HOME/.kimi-code/mythos" "$HOME/.claude/mythos" "$HOME/targets/_shared" \
     -type f \( -name '*.sh' -o -name '*.py' \) -exec chmod +x {} + 2>/dev/null || true

say "4. gate_hook.py stub (real pre-write gate was scrubbed; keep edits from being blocked)"
if [ ! -f "$HOME/targets/_gate/hooks/gate_hook.py" ]; then
  printf '#!/usr/bin/env python3\n# MYTHOS gate_hook stub (fail-open no-op). Replace with your real gate.\nimport sys\nsys.exit(0)\n' \
    > "$HOME/targets/_gate/hooks/gate_hook.py"
  chmod +x "$HOME/targets/_gate/hooks/gate_hook.py"; echo "created stub"
else echo "kept existing gate_hook.py"; fi

say "5. Merge hooks into ~/.claude/settings.json"
python3 - "$SRC/engine/hooks-config/settings.json" "$HOME/.claude/settings.json" "$HOME" "$FULL" <<'PY'
import json, sys, os
src, dst, home, full = sys.argv[1], sys.argv[2], sys.argv[3].rstrip("/"), sys.argv[4] == "1"
bundle = json.load(open(src))
cur = {}
if os.path.exists(dst):
    try: cur = json.load(open(dst))
    except Exception: cur = {}
def sub(x): return json.loads(json.dumps(x).replace("/home/RESEARCHER/", home + "/"))
cur["hooks"] = sub(bundle["hooks"]); keys = ["hooks"]
if full:
    for k in ("permissions", "model", "statusLine", "outputStyle", "effortLevel"):
        if k in bundle: cur[k] = sub(bundle[k]); keys.append(k)
os.makedirs(os.path.dirname(dst), exist_ok=True)
json.dump(cur, open(dst, "w"), indent=2)
print("merged:", ", ".join(keys))
PY

say "5b. Install the `mythos` command on PATH"
mkdir -p "$HOME/.local/bin"
install -m 0755 "$SRC/shared/mythos" "$HOME/.local/bin/mythos" 2>/dev/null \
  || { cp "$SRC/shared/mythos" "$HOME/.local/bin/mythos"; chmod +x "$HOME/.local/bin/mythos"; }
case ":$PATH:" in *":$HOME/.local/bin:"*) : ;; *) echo "note: add ~/.local/bin to PATH to use 'mythos' directly";; esac
echo "installed: ~/.local/bin/mythos  →  one command runs the whole pipeline"

if [ "$BBOT" -eq 1 ]; then
  say "6. bbot (enumeration) via uv"
  if command -v uv >/dev/null 2>&1; then
    uv tool install bbot --python 3.12 && echo "bbot installed" || echo "bbot install failed (see above)"
  else
    echo "uv not found — install it first: curl -LsSf https://astral.sh/uv/install.sh | sh"
  fi
fi

say "7. Health check (mythos_doctor)"
bash "$HOME/targets/_shared/mythos_doctor.sh" || echo "(structural failures above — review)"

say "DONE"
echo "backups: $BK"
echo "next: bash ~/.kimi-code/mythos/newtarget.sh <prog>  →  fill STATE/SCOPE.md  →  mtarget.sh <prog>"
