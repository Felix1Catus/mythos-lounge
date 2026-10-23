#!/usr/bin/env bash
# mythos_doctor.sh — one command that runs every MYTHOS self-test and reports health.
# STRUCTURAL checks must pass (offline, deterministic). LIVE checks need egress and only warn.
# Exit 0 iff all STRUCTURAL pass.
#   mythos_doctor.sh
# LOCATION: ~/targets/_shared/mythos_doctor.sh   (bundle: shared/mythos_doctor.sh)
set -uo pipefail
SH="$HOME/targets/_shared"
MY="$HOME/.claude/mythos"; [ -d "$MY" ] || MY="$HOME/.kimi-code/mythos"
SET="$HOME/.claude/settings.json"
PASS=0; FAIL=0; WARN=0
g(){ printf '\033[32m%s\033[0m' "$*"; }; r(){ printf '\033[31m%s\033[0m' "$*"; }; y(){ printf '\033[33m%s\033[0m' "$*"; }

# run_check NAME KIND CMD... (success = exit 0 AND stdout matches $TOKEN if set)
TOKEN=""
check(){
  local name="$1" kind="$2"; shift 2
  local out rc
  out="$("$@" 2>&1)"; rc=$?
  local good=0
  if [ $rc -eq 0 ]; then
    if [ -z "$TOKEN" ] || printf '%s' "$out" | grep -qE "$TOKEN"; then good=1; fi
  fi
  if [ $good -eq 1 ]; then
    printf '  [%s] %-34s\n' "$(g PASS)" "$name"; PASS=$((PASS+1))
  elif [ "$kind" = LIVE ]; then
    printf '  [%s] %-34s (needs egress)\n' "$(y WARN)" "$name"; WARN=$((WARN+1))
  else
    printf '  [%s] %-34s\n' "$(r FAIL)" "$name"; FAIL=$((FAIL+1))
    printf '%s\n' "$out" | tail -2 | sed 's/^/        /'
  fi
  TOKEN=""
}

printf '\033[1m== MYTHOS doctor ==\033[0m  edition: %s\n' "$MY"

echo "-- structural (must pass) --"
TOKEN=", 0 failed"; check "hooks (test_hooks.py)"      STRUCT python3 "$MY/test_hooks.py"
TOKEN="selftest: PASS"; check "rank_surface.py"         STRUCT python3 "$SH/rank_surface.py" --selftest
TOKEN="selftest: PASS"; check "coverage_map.py"         STRUCT python3 "$SH/coverage_map.py" --selftest
TOKEN="selftest: PASS"; check "report_draft.py"         STRUCT python3 "$SH/report_draft.py" --selftest
TOKEN="selftest: PASS"; check "js_miner.py"             STRUCT python3 "$SH/js_miner.py" --selftest
TOKEN="selftest: PASS"; check "takeover_check.py"       STRUCT python3 "$SH/takeover_check.py" --selftest
TOKEN="selftest: PASS"; check "php2shell_check.py"      STRUCT python3 "$SH/php2shell_check.py" --selftest
TOKEN="selftest: PASS"; check "mythos.py (orchestrator)" STRUCT python3 "$SH/mythos.py" --selftest
TOKEN="self-test: PASS"; check "enum_pipeline.sh"       STRUCT bash   "$SH/enum_pipeline.sh" --selftest
TOKEN="VALID";          check "settings.json parses"    STRUCT python3 -c "import json;json.load(open('$SET'));print('VALID')"

echo "-- referenced hook files present --"
present(){ TOKEN="OK"; check "$1" STRUCT bash -c "[ -e '$2' ] && echo OK || { echo MISSING; exit 1; }"; }
present "gate_hook.py"          "$HOME/targets/_gate/hooks/gate_hook.py"
present "supervisor_lane_guard" "$MY/supervisor_lane_guard.py"
present "context_router.sh"     "$MY/context_router.sh"
present "mythos_hooklib.py"     "$MY/mythos_hooklib.py"

echo "-- presence --"
TOKEN="";               check "bbot installed"          STRUCT bash -c "command -v bbot >/dev/null || [ -x '$HOME/.local/bin/bbot' ]"

echo "-- live (egress; warn only) --"
TOKEN="PASS";           check "probelib.py 3-arm"       LIVE   python3 "$SH/probelib.py"
TOKEN="";               check "probe.sh --selftest"     LIVE   bash   "$SH/probe.sh" --selftest

echo
printf 'result: %s pass, %s warn, %s fail\n' "$(g $PASS)" "$(y $WARN)" "$(r $FAIL)"
[ "$FAIL" -eq 0 ] && { echo "STRUCTURAL: healthy."; exit 0; } || { echo "STRUCTURAL failures above."; exit 1; }
