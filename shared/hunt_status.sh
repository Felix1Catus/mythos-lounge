#!/usr/bin/env bash
# hunt_status.sh — one-screen status across all MYTHOS targets.
# Open leads, deadends, chain floor/ceiling, surface-map top-3, evidence count, last journal
# line — per program, active target starred. Read-only. No arg = all targets; <prog> = one.
#   hunt_status.sh [prog]
# LOCATION: ~/targets/_shared/hunt_status.sh   (bundle: shared/hunt_status.sh)
set -uo pipefail
T="$HOME/targets"
ACTIVE=""
for m in "$HOME/.claude/mythos/active_target" "$HOME/.kimi-code/mythos/active_target"; do
  [ -f "$m" ] && ACTIVE="$(head -1 "$m" | tr -d '[:space:]')" && break
done

bold(){ printf '\033[1m%b\033[0m\n' "$*"; }
field(){ grep -iE "$2" "$1" 2>/dev/null | head -1 | sed 's/[*_-]//g; s/^[^:]*:[[:space:]]*//' | cut -c1-54; }

one(){
  local p="$1"
  local d="$T/$p"
  local s="$d/STATE"
  local star=""
  [ "$p" = "$ACTIVE" ] && star=" \033[33m(active)\033[0m"
  printf '\n'; bold "▸ $1$star"
  local leads=0 dead=0
  [ -f "$s/LEADS.md" ] && leads=$(grep -cE '^\s*-\s*\[ \]' "$s/LEADS.md" 2>/dev/null || true)
  [ -f "$s/DEADENDS.md" ] && dead=$(awk -F'|' '/^## Active deadends/{a=1;next} /^## /{a=0} a && NF>2 && $2 !~ /Surface|---|—|^ *$/{c++} END{print c+0}' "$s/DEADENDS.md" 2>/dev/null || true)
  printf '   open leads: %s   deadends(rows): %s\n' "$leads" "$dead"
  if [ -f "$s/CHAIN_LEDGER.md" ]; then
    printf '   floor:   %s\n' "$(field "$s/CHAIN_LEDGER.md" 'Floor')"
    printf '   ceiling: %s\n' "$(field "$s/CHAIN_LEDGER.md" 'Ceiling')"
  fi
  if [ -f "$s/SURFACE_MAP.md" ]; then
    echo "   surface top-3:"
    grep -E '^\| [0-9]+ \|' "$s/SURFACE_MAP.md" 2>/dev/null | head -3 \
      | awk -F'|' '{printf "     #%s  score%s  %s\n",$2,$3,$4}'
  fi
  local ev=0
  [ -d "$d/evidence" ] && ev=$(find "$d/evidence" -type f 2>/dev/null | wc -l | tr -d ' ')
  printf '   evidence files: %s\n' "$ev"
  if [ -f "$s/JOURNAL.ndjson" ]; then
    printf '   last action: %s\n' "$(tail -1 "$s/JOURNAL.ndjson" 2>/dev/null | cut -c1-70)"
  fi
}

bold "MYTHOS hunt status  —  active: ${ACTIVE:-<none>}"
if [ -n "${1:-}" ]; then
  [ -d "$T/$1" ] || { echo "no target $1"; exit 1; }
  one "$1"
else
  found=0
  for d in "$T"/*/; do
    p="$(basename "$d")"; [ "$p" = "_shared" ] && continue; [ "$p" = "_gate" ] && continue
    [ -d "$d/STATE" ] || continue
    one "$p"; found=1
  done
  [ "$found" = 0 ] && echo "(no targets yet — scaffold with newtarget.sh <prog>)"
fi
echo
