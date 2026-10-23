#!/usr/bin/env bash
# MYTHOS stop-guard — Stop hook, SEAT-AWARE edition.
# Fires when the model is about to end its turn. Pressure is per-seat:
#   hunting seats (RECON/DATAFLOW/CHAIN/unknown) → original probe pressure (unchanged)
#   SUPERVISOR  → never end with a dirty board / undispatched READY work / unreviewed inbox
#   CHIEF_SKEPTIC → never end with a pending verdict you could render
#   LIBRARIAN   → never end with an unpersisted ingestion or stale dossier
# Fires at most ONCE per session (marker). No active target → silent. Fail-open on error.
# LOCATION: <install>/mythos/stop_guard.sh (seat is auto-detected from the install's core file)
set -uo pipefail
INPUT=$(cat || true)
printf '%s' "$INPUT" | python3 "$HOME/targets/_shared/lounge/live_talk.py" stop
_lt=$?
if [[ "$_lt" -eq 2 ]]; then
  exit 2
fi
SESSION=$(printf '%s' "$INPUT" | python3 -c '
import json, sys
try:
    print(json.load(sys.stdin).get("session_id") or "nosession")
except Exception:
    print("nosession")
' 2>/dev/null || echo "nosession")

# --- detect install + seat -------------------------------------------------
HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"      # <install>/mythos
CFG_DIR="$(dirname "$HOOK_DIR")"                              # <install>
CORE="$CFG_DIR/CLAUDE.md"; [ -f "$CORE" ] || CORE="$CFG_DIR/AGENTS.md"
SEAT="HUNTER"
[ -f "$CORE" ] && SEAT=$(grep -m1 -oE '^## SEAT: [A-Z_]+' "$CORE" 2>/dev/null | awk '{print $3}')
[ -n "$SEAT" ] || SEAT="HUNTER"

# --- active target (same contract as before) --------------------------------
ACTIVE="$CFG_DIR/mythos/active_target"
[ -f "$ACTIVE" ] || ACTIVE="$HOME/.kimi-code/mythos/active_target"
[ -f "$ACTIVE" ] || exit 0
PROG=$(head -1 "$ACTIVE" 2>/dev/null | tr -d '[:space:]')
[ -n "$PROG" ] || exit 0

MARKER="$CFG_DIR/mythos/stop_nudged_$SESSION"
[ -f "$MARKER" ] && exit 0
touch "$MARKER"

NEXT=""
CK="$HOME/targets/$PROG/STATE/CHECKPOINT.md"
if [ -f "$CK" ]; then
    NEXT=$(grep -E '^NEXT\s*:' "$CK" | head -1 | sed 's/^NEXT\s*:\s*//' | cut -c1-120)
fi
Q="$HOME/claude-shared/agents"

case "$SEAT" in
  SUPERVISOR_CLAUDE)
    >&2 echo "MYTHOS stop-guard (SUPERVISOR seat, once per session): active target '$PROG'. Before ending this turn: is the board clean? — TASK_QUEUE ($Q/TASK_QUEUE.json) persisted with every READY task dispatched · FINDINGS_INBOX has nothing un-routed · ANOMALY_LEDGER re-ranked · per-target STATE/ boards current (read-before-persist, _by: markers respected). If a dispatch is writable right now, WRITE it instead of stopping. You do not fire probes — you never end a turn with a dirty board. Queued next step on disk: ${NEXT:-<none — write one>}." ;;
  CHIEF_SKEPTIC_CLAUDE)
    >&2 echo "MYTHOS stop-guard (SKEPTIC seat, once per session): active target '$PROG'. Before ending this turn: render every pending verdict in $Q/FINDINGS_INBOX.json you have evidence for — APPROVED / NEEDS-REFINEMENT / REJECTED + the cheapest missing evidence. A pending candidate you could rule on is a dirty desk. Never approve on confidence; never end with an unreviewed queue. Queued next step on disk: ${NEXT:-<none>}." ;;
  LIBRARIAN_KIMI)
    >&2 echo "MYTHOS stop-guard (LIBRARIAN seat, once per session): active target '$PROG'. Before ending this turn: everything ingested this session is persisted (dossier updated with evidence pointers, journal written, compaction-safe). If another seat's query is unanswered, answer or log it. 'Not in the record' is valid; an unwritten memory is not. Queued next step on disk: ${NEXT:-<none>}." ;;
  *)
    >&2 echo "MYTHOS stop-guard (once per session): active target '$PROG'. Before ending this turn: if a probe is fireable right now, FIRE it instead of stopping. If not, persist the exact next step: python3 $CFG_DIR/mythos/checkpoint.py $PROG --next \"<exact command>\" and name the blocker. Queued next step on disk: ${NEXT:-<none — write one>}. Never end a hunt turn waiting for directives." ;;
esac
exit 2
