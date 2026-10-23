#!/usr/bin/env bash
# probe.sh — the one correct curl. Encodes the instrument scars mechanically so they
# cannot be forgotten (notes don't load; paths do).  Installed by audit 2026-07-31.
#
#   CL-D scars this closes:
#     · stale tempfile bodies read as target data (x2) -> mktemp per run + truncate + trap
#     · a 000 stored beside a body                     -> 000 is CONNECTION-ONLY, body suppressed
#     · HTTPS-by-IP with no SNI (1,341 all-000 probes) -> --ip forces --resolve
#     · -k omitted on private-CA hosts (PROGRAM_78)          -> -k is an explicit decision, echoed
#     · bare httpx / relative tool paths               -> curl pinned to /usr/bin/curl
#
# USAGE
#   probe.sh <url> [-- curl args...]
#   probe.sh <url> --ip <A.B.C.D>        # HTTPS by IP, SNI preserved from the URL host
#   probe.sh <url> --insecure-ok         # private CA / self-signed EXPECTED (adds -k, logs it)
#   probe.sh <url> --body                # print the body (default: class only)
#   probe.sh --selftest                  # known-good + known-dead positive control
#
# OUTPUT: one CLASS line -> code | bytes | time | ct | server | tls | url
#   code=000 means CONNECTION FAILED. There is no body. Never quote it as target behaviour.
set -uo pipefail

CURL=/usr/bin/curl
UA='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36'

die(){ echo "probe.sh: $*" >&2; exit 2; }
[[ -x "$CURL" ]] || die "no curl at $CURL"

# --- per-run scratch, always fresh, always cleaned -----------------------------
BODY=$(mktemp "${TMPDIR:-/tmp}/probe.body.XXXXXXXX") || die "mktemp failed"
HDRS=$(mktemp "${TMPDIR:-/tmp}/probe.hdrs.XXXXXXXX") || die "mktemp failed"
cleanup(){ rm -f "$BODY" "$HDRS"; }
trap cleanup EXIT
: > "$BODY"; : > "$HDRS"          # explicit truncate — never inherit a prior run's bytes

selftest(){
  echo "── probe.sh self-test (positive control BEFORE any battery) ──"
  local ok=0
  echo "[arm 1] known-GOOD  https://example.com"
  "$0" https://example.com | sed 's/^/    /'
  local c1; c1=$("$0" https://example.com | awk -F'|' '{gsub(/ /,"",$1);print $1}')
  [[ "$c1" == "200" ]] && { echo "    PASS (200)"; ok=$((ok+1)); } || echo "    FAIL (got '$c1')"
  echo "[arm 2] known-DEAD  https://this-host-does-not-exist-mythos.invalid"
  "$0" https://this-host-does-not-exist-mythos.invalid | sed 's/^/    /'
  local c2; c2=$("$0" https://this-host-does-not-exist-mythos.invalid | awk -F'|' '{gsub(/ /,"",$1);print $1}')
  [[ "$c2" == "000" ]] && { echo "    PASS (000 = connection result, no body)"; ok=$((ok+1)); } || echo "    FAIL (got '$c2')"
  echo "── self-test $ok/2 ──"
  [[ $ok -eq 2 ]] || exit 1
}
[[ "${1:-}" == "--selftest" ]] && { selftest; exit 0; }

URL="${1:-}"; shift || true
[[ -n "$URL" ]] || die "usage: probe.sh <url> [--ip A.B.C.D] [--insecure-ok] [--body] [-- curl args]"

IP=""; INSECURE=0; SHOWBODY=0; EXTRA=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --ip)          IP="${2:-}"; shift 2 ;;
    --insecure-ok) INSECURE=1; shift ;;
    --body)        SHOWBODY=1; shift ;;
    --)            shift; EXTRA=("$@"); break ;;
    *)             EXTRA+=("$1"); shift ;;
  esac
done

HOST=$(sed -E 's#^[a-zA-Z]+://##; s#[/?].*$##; s#^.*@##; s#:[0-9]+$##' <<<"$URL")
PORT=443; [[ "$URL" == http://* ]] && PORT=80

ARGS=( -sS -o "$BODY" -D "$HDRS" --globoff --max-time 20 --connect-timeout 10
       -A "$UA" -w '%{http_code}|%{size_download}|%{time_total}|%{content_type}|%{ssl_verify_result}' )

# SNI: HTTPS-by-IP MUST use --resolve so the TLS SNI stays the hostname. Never rewrite the URL.
TLSNOTE="verify"
if [[ -n "$IP" ]]; then
  ARGS+=( --resolve "${HOST}:${PORT}:${IP}" )
  TLSNOTE="sni=${HOST}@${IP}"
fi
# -k is a DECISION MADE BEFORE THE PROBE, and it is always echoed in the class line.
if [[ $INSECURE -eq 1 ]]; then
  ARGS+=( -k )
  TLSNOTE="${TLSNOTE},INSECURE(-k: private-CA expected)"
fi
((${#EXTRA[@]})) && ARGS+=( "${EXTRA[@]}" )

W=$("$CURL" "${ARGS[@]}" "$URL" 2>/dev/null) || true
IFS='|' read -r CODE SIZE TIME CT VERIFY <<<"${W:-000|0|0||}"
SERVER=$(awk -F': ' 'tolower($1)=="server"{gsub(/\r/,"",$2);print $2;exit}' "$HDRS" 2>/dev/null)

if [[ "$CODE" == "000" ]]; then
  # A 000 is a CONNECTION result. It says NOTHING about the target and must never be
  # stored or quoted beside a body. Suppress the (necessarily empty/stale-risk) body.
  printf '%3s | %8s | %6ss | %-24s | %-14s | %s | %s\n' \
    "000" "CONN-FAIL" "${TIME:-0}" "(no response)" "(none)" "$TLSNOTE" "$URL"
  echo "     ^ CONNECTION FAILED — not a target verdict. Check DNS/egress/SNI/-k before concluding anything." >&2
  exit 1
fi

printf '%3s | %8s | %6ss | %-24s | %-14s | %s | %s\n' \
  "$CODE" "$SIZE" "$TIME" "${CT:0:24}" "${SERVER:0:14}" "$TLSNOTE" "$URL"

if [[ $SHOWBODY -eq 1 ]]; then echo "── body ──"; cat "$BODY"; echo; fi
exit 0
