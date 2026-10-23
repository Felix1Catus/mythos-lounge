#!/usr/bin/env bash
# One-shot hunter upgrade fanout. SoT:
#   law     = ~/.kimi-code/AGENTS.md
#   brain   = ~/.grok/rules/CRITICAL_HUNTER.md
#   skills  = ~/.grok/skills
#   gate    = ~/.claude/mythos/prefile_gate.sh
#   doctrine= ~/.claude/feedback/hunt_doctrine.md
set -euo pipefail
ROOT="$HOME"
TS=$(date +%Y%m%d_%H%M%S)
echo "=== sync_hunters $TS ==="

# 1. cores
bash "$ROOT/.kimi-code/mythos/sync_mirrors.sh"

# 2. skills
bash "$ROOT/.grok/mythos/sync_skills.sh"

# 3. prefile gate copies (SoT stays at claude)
install -m 0755 "$ROOT/.claude/mythos/prefile_gate.sh" "$ROOT/.grok/mythos/prefile_gate.sh"
install -m 0755 "$ROOT/.claude/mythos/prefile_gate.sh" "$ROOT/.kimi-code/mythos/prefile_gate.sh"

# 4. hunt doctrine + never-refrain + source-first (skip same-file copies)
cp -a "$ROOT/.claude/feedback/hunt_doctrine.md" "$ROOT/.grok/feedback/hunt_doctrine.md"
cp -a "$ROOT/.claude/feedback/hunt_doctrine.md" "$ROOT/.kimi-code/feedback/hunt_doctrine.md"
mkdir -p "$ROOT/.claude-account2/feedback"
cp -a "$ROOT/.claude/feedback/hunt_doctrine.md" "$ROOT/.claude-account2/feedback/hunt_doctrine.md"

for dest in "$ROOT/.claude/feedback" "$ROOT/.kimi-code/feedback" "$ROOT/.claude-account2/feedback"; do
  mkdir -p "$dest"
  cp -a "$ROOT/.grok/feedback/feedback_never_refrain_fire.md" "$dest/feedback_never_refrain_fire.md"
  cp -a "$ROOT/.grok/feedback/feedback_source_first.md" "$dest/feedback_source_first.md"
done
cp -a "$ROOT/.grok/feedback/priority.md" "$ROOT/.kimi-code/feedback/priority.md"
cp -a "$ROOT/.grok/feedback/priority.md" "$ROOT/.claude-account2/feedback/priority.md"

# 5. hunter agents (do not delete dest extras)
for dest in \
  "$ROOT/.claude/agents" \
  "$ROOT/.claude-account2/agents" \
  "$ROOT/.kimi-code/agents"
do
  mkdir -p "$dest"
  for a in chain-breaker critical-hunter impact-prover scope-architect surface-re target-hunter warm-boot; do
    [ -f "$ROOT/.grok/agents/$a.md" ] && cp -a "$ROOT/.grok/agents/$a.md" "$dest/$a.md"
  done
done

# 6. commands (claude + dsclaude; grok2/3/4 already link to grok)
for dest in \
  "$ROOT/.claude/commands" \
  "$ROOT/.claude-account2/commands"
do
  mkdir -p "$dest"
  for c in chain.md critical.md error-protocol.md ground.md mythos-verify.md persist.md; do
    [ -f "$ROOT/.grok/commands/$c" ] && cp -a "$ROOT/.grok/commands/$c" "$dest/$c"
  done
done

echo "=== sync_hunters OK $TS ==="
