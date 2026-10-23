#!/usr/bin/env bash
# enum_pipeline.sh — MYTHOS enumeration phase (bbot-driven), scope-gated.
#
# Runs a BIG recursive enumeration with bbot (subdomains + web probe + takeover, optionally
# ports + nuclei), then hands the event stream to rank_surface.py which scores every host by
# bug-likelihood and writes STATE/SURFACE_MAP.md + promotes the top leads into STATE/LEADS.md.
#
#   enum_pipeline.sh <prog> [--vuln] [--ports] [--passive] [--mine-js] [--top N]
#     --vuln     also run nuclei inside bbot (active, heavier) -> VULNERABILITY signals
#     --ports    also run portscan (needs masscan/root) -> OPEN_TCP_PORT signals
#     --passive  passive-only discovery (no active web requests)
#     --mine-js  after ranking, mine top hosts' JS for secrets+endpoints, then re-rank
#     --no-takeover   skip the subdomain-takeover confirmer (on by default)
#     --no-php2shell  skip PHP2Shell (CVE-2026-109618/109619) version detection (on by default)
#     --top N    promote N leads into LEADS.md (default 15)
#   enum_pipeline.sh --selftest
#
# SCOPE-GATED: reads in-scope roots from STATE/SCOPE.md and targets ONLY those. No SCOPE.md
# roots -> refuses to run (enumeration is active; it belongs inside authorized scope only).
# LOCATION: ~/targets/_shared/enum_pipeline.sh   (bundle: shared/enum_pipeline.sh)
set -uo pipefail

SELF="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BBOT="${BBOT:-$HOME/.local/bin/bbot}"
RANK="$SELF/rank_surface.py"
HOMET="$HOME/targets"

die(){ echo "enum_pipeline: $*" >&2; exit 2; }

if [[ "${1:-}" == "--selftest" ]]; then
  echo "── enum_pipeline self-test ──"
  [[ -x "$BBOT" ]] || command -v bbot >/dev/null || die "bbot not found (set BBOT=/path)"
  "$BBOT" --version 2>/dev/null | tail -1 | sed 's/^/  bbot /'
  python3 "$RANK" --selftest || die "rank_surface selftest FAILED"
  echo "  would run: bbot -t <scope roots> -p subdomain-enum web -m baddns -om json ..."
  echo "self-test: PASS"; exit 0
fi

PROG="${1:-}"; [[ -n "$PROG" ]] || die "usage: enum_pipeline.sh <prog> [--vuln] [--ports] [--passive] [--top N]"
shift || true
TOP=15; VULN=0; PORTS=0; PASSIVE=0; MINEJS=0; TAKEOVER=1; PHP2S=1
while [[ $# -gt 0 ]]; do
  case "$1" in
    --vuln) VULN=1;; --ports) PORTS=1;; --passive) PASSIVE=1;; --mine-js) MINEJS=1;;
    --no-takeover) TAKEOVER=0;; --no-php2shell) PHP2S=0;;
    --top) TOP="${2:-15}"; shift;;
    *) die "unknown arg: $1";;
  esac; shift
done
JS="$SELF/js_miner.py"; TK="$SELF/takeover_check.py"; P2S="$SELF/php2shell_check.py"

SCOPE="$HOMET/$PROG/STATE/SCOPE.md"
[[ -f "$SCOPE" ]] || die "no $SCOPE — scaffold with newtarget.sh $PROG and fill SCOPE.md first"

# in-scope registrable domains from the '## In scope' section (strip wildcards + placeholders)
ROOTS=$(awk '/^## *[Ii]n scope/{f=1;next} /^## /{f=0} f' "$SCOPE" \
  | grep -oiE '([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,24}' \
  | sed 's/^\*\.//' | grep -viE '^(example\.com|policy\.url)$' | sort -u | paste -sd, -)
[[ -n "$ROOTS" ]] || die "no in-scope domains parsed from SCOPE.md — nothing authorized to enumerate"

DATE="$(date +%Y%m%d-%H%M%S)"
OUT="$HOMET/$PROG/recon/enum"
NAME="enum_$DATE"
mkdir -p "$OUT"

# bbot 3.x presets: subdomain-enum (discovery), web (quick web probe), baddns (takeover).
PRESETS=(-p subdomain-enum)
MODULES=(-m baddns)
DEADLY=()
if [[ $PASSIVE -eq 1 ]]; then
  MODULES=()            # baddns is active; drop it for passive-only
  PRESETS+=(-ef active) # exclude active-connection modules -> passive discovery only
else
  PRESETS+=(web)
fi
if [[ $VULN -eq 1 ]]; then MODULES+=(nuclei); DEADLY=(--allow-deadly); fi
if [[ $PORTS -eq 1 ]]; then MODULES+=(portscan); DEADLY=(--allow-deadly); fi

echo "enum_pipeline: prog=$PROG roots=$ROOTS vuln=$VULN ports=$PORTS passive=$PASSIVE"
echo "running: $BBOT -t $ROOTS ${PRESETS[*]} ${MODULES[*]} -om json -o $OUT -n $NAME -y ${DEADLY[*]}"
"$BBOT" -t "$ROOTS" "${PRESETS[@]}" "${MODULES[@]}" -om json -o "$OUT" -n "$NAME" -y "${DEADLY[@]}"
RC=$?
ND="$OUT/$NAME/output.ndjson"
[[ -f "$ND" ]] || ND="$(ls -t "$HOMET/$PROG/recon"/**/output.ndjson 2>/dev/null | head -1)"
[[ -f "$ND" ]] || die "bbot produced no output.ndjson (rc=$RC) — check the scan above"

echo
echo "ranking surface from $ND"
python3 "$RANK" "$PROG" --ndjson "$ND" --top "$TOP"

RERANK=0
if [[ $TAKEOVER -eq 1 ]]; then
  echo
  echo "confirming subdomain takeovers across the top $TOP hosts (second-source)"
  python3 "$TK" "$PROG" --from-surface --top "$TOP" && RERANK=1
fi
if [[ $PHP2S -eq 1 ]]; then
  echo
  echo "detecting PHP2Shell (CVE-2026-109618/109619) by version across the top $TOP hosts"
  python3 "$P2S" "$PROG" --from-surface --top "$TOP" && RERANK=1
fi
if [[ $MINEJS -eq 1 ]]; then
  echo
  echo "mining JS (secrets + endpoints) from the top $TOP ranked hosts"
  python3 "$JS" "$PROG" --from-surface --top "$TOP" && RERANK=1
fi
if [[ $RERANK -eq 1 ]]; then
  echo "re-ranking with takeover/JS signals folded in"
  python3 "$RANK" "$PROG" --ndjson "$ND" --top "$TOP"
fi

echo
echo "DONE. See $HOMET/$PROG/STATE/SURFACE_MAP.md, TAKEOVER.md, and the auto-blocks in STATE/LEADS.md"
