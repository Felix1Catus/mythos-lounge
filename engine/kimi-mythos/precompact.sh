#!/usr/bin/env bash
# MYTHOS PreCompact — checkpoint + auto-flush un-persisted state (Kimi Code edition)
# Fires before Kimi compacts context (matcher: manual|auto). Logs + marks RESUME.md if any
# target notes are newer than it. Return values are ignored by Kimi on PreCompact — disk is
# the only channel, so the marker goes INTO the file the next session reads.
# LOCATION: ~/.kimi-code/mythos/precompact.sh
set -uo pipefail

LOG="$HOME/.kimi-code/mythos/compaction.log"
mkdir -p "$(dirname "$LOG")"
TIMESTAMP=$(date -Iseconds)

INPUT=$(cat || true)
CWD=$(printf '%s' "$INPUT" | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
    print(str(d.get("cwd") or "").replace("\\", "/"))
except Exception:
    print("")
' 2>/dev/null || echo "")
TRIGGER=$(printf '%s' "$INPUT" | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
    print(d.get("trigger") or d.get("matcher") or "")
except Exception:
    print("")
' 2>/dev/null || echo "")

FLUSHED=""
LATEST_NOTE=""
LATEST_MTIME=0

for note in $(find "$HOME/targets" -maxdepth 4 -name "*.md" -mmin -5 2>/dev/null | head -20); do
  MTIME=$(stat -c %Y "$note" 2>/dev/null || echo 0)
  if [[ $MTIME -gt $LATEST_MTIME ]]; then
    LATEST_MTIME=$MTIME
    LATEST_NOTE=$note
  fi
done 2>/dev/null || true

if [[ -n "$LATEST_NOTE" ]]; then
  RESUME_DIR=$(dirname "$LATEST_NOTE")
  while [[ "$RESUME_DIR" != "$HOME" && "$RESUME_DIR" != "/" ]]; do
    if [[ -f "$RESUME_DIR/RESUME.md" ]]; then
      R_MTIME=$(stat -c %Y "$RESUME_DIR/RESUME.md" 2>/dev/null || echo 0)
      if [[ $LATEST_MTIME -gt $R_MTIME ]]; then
        FLUSH_MARKER="[$TIMESTAMP] AUTO-FLUSH (Kimi PreCompact ${TRIGGER:-?}): un-persisted work at ${LATEST_NOTE} (newer than RESUME.md). PERSIST before context is lost."
        echo "" >> "$RESUME_DIR/RESUME.md"
        echo "$FLUSH_MARKER" >> "$RESUME_DIR/RESUME.md"
        FLUSHED="yes"
      fi
      break
    fi
    RESUME_DIR=$(dirname "$RESUME_DIR")
  done
fi

{
  echo "[$TIMESTAMP] PreCompact fired (${TRIGGER:-?}) | cwd: ${CWD:-?}"
  if [[ -n "$FLUSHED" ]]; then
    echo "  AUTO-FLUSH: appended marker to RESUME.md"
  else
    echo "  No un-persisted work detected."
  fi
  echo "---"
} >> "$LOG"

exit 0
