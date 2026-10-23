#!/usr/bin/env bash
# sync_mirrors.sh — copy shared hunter law from the canonical Kimi core.
# Seats dismantled 2026-09-29 until further notice. Every install is solo.
# Role files under ~/claude-shared/roles/ stay on disk and are not wired in.
# ~/AGENTS.md is the home solo router — this script never overwrites it.
# FAILS LOUDLY on any missing anchor or a missing SOLO block.
set -uo pipefail

SRC="$HOME/.kimi-code/AGENTS.md"

REQUIRED=(
  "BLOCK A — GROUND TRUTH FIRST"
  "INTROSPECT/CAPTURE BEFORE GUESSING"
  "TWO-FAIL RULE"
  "MECHANICAL DIFF BEFORE VARIANTS"
  "TIER/EDITION GATE CHECK"
  "PLATFORM PRIMER"
  "BLOCK B — INSTRUMENT DISCIPLINE"
  "SELF-TEST BEFORE BELIEVING"
  "HARNESS-FIRST HYPOTHESIS"
  "DIVERGENCE PROTOCOL"
  "THROTTLE SELF-AWARENESS"
  "BLOCK C — LEAN CONTEXT"
  "BLOCK D — STATE INTEGRITY"
  "READ-BEFORE-PERSIST"
  "MULTI-AGENT"
  "ONE CANONICAL CORE"
  "SOLO — seats dismantled"
  "BLOCK G - SOURCE-FIRST"
  "prefile_gate"
)

check() { local f="$1" miss=0 a
  for a in "${REQUIRED[@]}"; do
    grep -qF "$a" "$f" || { echo "  MISSING in $f: $a"; miss=$((miss+1)); }
  done
  return $miss
}

echo "── source check: $SRC"
check "$SRC" || { echo "SOURCE FAILED — fix $SRC first"; exit 1; }
grep -qF "^## SEAT:" "$SRC" && { echo "SOURCE STILL HAS A SEAT BLOCK — remove it"; exit 1; }

build() { # build <dest> <agent-display-name>
  local dest="$1" name="$2" tmp
  [ -f "$dest" ] || { echo "  skip missing $dest"; return 0; }
  tmp=$(mktemp)
  sed -e "s/MYTHOS OS for KIMI v3/MYTHOS OS for ${name^^} v3/" \
      -e "s|~/.kimi-code/AGENTS.md|$dest|g" \
      "$SRC" > "$tmp"
  # A seat block must not survive a sync, even if one is appended to the source later.
  sed -i '/^## SEAT: /,$d' "$tmp"
  grep -qF "## SOLO — seats dismantled" "$tmp" || { echo "SOLO BLOCK LOST: $dest"; rm -f "$tmp"; return 1; }
  cp -a "$dest" "$dest.bak-sync" 2>/dev/null || true
  cp "$tmp" "$dest" && rm -f "$tmp"
  echo "── mirror check: $dest [SOLO]"
  check "$dest" || { echo "MIRROR FAILED: $dest — restored .bak-sync"; cp -a "$dest.bak-sync" "$dest"; return 1; }
  grep -qF "^## SEAT:" "$dest" && { echo "SEAT BLOCK RETURNED: $dest — restored"; cp -a "$dest.bak-sync" "$dest"; return 1; }
  echo "   OK ($(wc -c < "$dest") bytes)"
}

build "$HOME/.claude/CLAUDE.md" "claude" || exit 1
build "$HOME/.claude-account2/CLAUDE.md" "claude" || exit 1
build "$HOME/.grok/AGENTS.md" "grok" || exit 1
[ -e "$HOME/.gemini/GEMINI.md" ] && { build "$HOME/.gemini/GEMINI.md" "gemini" || exit 1; }

# grok2/3/4 follow grok1 so they cannot drift
for g in grok2 grok3 grok4; do
  dest="$HOME/.$g/AGENTS.md"
  [ -e "$HOME/.$g" ] || continue
  if [ -e "$dest" ] || [ -L "$dest" ]; then
    cp -a "$dest" "$dest.bak-sync" 2>/dev/null || true
  fi
  ln -sfn "$HOME/.grok/AGENTS.md" "$dest"
  echo "── link $dest -> ~/.grok/AGENTS.md"
done
echo "SYNC OK — canonical: $SRC (solo; ~/AGENTS.md left untouched)"
