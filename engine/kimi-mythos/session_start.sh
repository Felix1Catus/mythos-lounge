#!/usr/bin/env bash
# MYTHOS SessionStart — creed + feedback queue + warm-boot pointer (Kimi Code edition)
# matcher: startup|resume. Stdout MAY be appended to context — keep it lean (~30 lines max).
# RESUME.md stays on-demand (read when resuming), never auto-dumped.
# LOCATION: ~/.kimi-code/mythos/session_start.sh
set -uo pipefail

LOG="$HOME/.kimi-code/mythos/session_start.log"
mkdir -p "$(dirname "$LOG")"
TS=$(date -Iseconds)
echo "[$TS] SessionStart cwd=${PWD:-?}" >> "$LOG"

echo "◆ MYTHOS OS (Kimi) — execute the prompt. Brain: ~/.grok/rules/CRITICAL_HUNTER.md. Do not read another file before the request. Loop: GROUND→PROBE→ANALYZE→PERSIST→VALIDATE. Probes > theory. OS: ~/.kimi-code/AGENTS.md"
echo "🎯 CRITICAL HUNTER — default = Critical path. Not critical ⇒ chain or escalate. Floor / ceiling / missing link."
echo "◆ P01–P14 protocols: ~/.kimi-code/mythos/doctrine/protocols/ (P05 ceiling-ban · P13 T1–T10 tripwires) · TRAPS: ~/targets/_shared/TRAPS.md"

# Feedback priority queue — head only (10 lines; full file on demand).
if [[ -f "$HOME/.claude/feedback/priority.md" ]]; then
  echo "── FEEDBACK PRIORITY (head; full: ~/.claude/feedback/priority.md) ──"
  head -n 10 "$HOME/.claude/feedback/priority.md"
fi

# Warm-boot pointer: PROVEN+NEXT lines only, not the full checkpoint (google resume_brief pattern).
F="$HOME/.kimi-code/mythos/active_target"
if [[ -f "$F" ]]; then
  PROG=$(head -1 "$F" 2>/dev/null | tr -d '[:space:]')
  CK="$HOME/targets/$PROG/STATE/CHECKPOINT.md"
  if [[ -n "$PROG" && -f "$CK" ]]; then
    echo "════════ WARM-BOOT — active target: $PROG ════════"
    grep -E '^(PROVEN|NEXT|BLOCKERS)\s*:' "$CK" | cut -c1-200
    echo "Full trail: bash ~/.kimi-code/mythos/resume.sh $PROG"
  fi
fi

# Janitor — silent, fast, once per session: prune stale once-markers, rotate fat logs.
find "$HOME/.kimi-code/mythos" -maxdepth 1 -name 'stop_nudged_*' -mtime +14 -delete 2>/dev/null
find "$HOME/.kimi-code/mythos/router_seen" -mindepth 1 -maxdepth 1 -mtime +14 -exec rm -rf {} + 2>/dev/null
for L in "$HOME/.kimi-code/mythos"/*.log; do
  [ -f "$L" ] && [ "$(stat -c%s "$L" 2>/dev/null || echo 0)" -gt 524288 ] && tail -n 200 "$L" > "$L.tmp" && mv "$L.tmp" "$L"
done 2>/dev/null

exit 0
