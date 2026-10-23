#!/usr/bin/env bash
# bypass_matrix.sh — ONE instrument: method · override · path · trust-header · CORS matrices.
# Merged 2026-07-31 from PROGRAM_81/scripts/{bypass_matrix,xforward_matrix,cors_matrix}.sh, which
# were three separate scripts fired at three different times (the CORS + X-Forwarded matrices
# only ran after a user prod). Running them as one instrument removes that gap.
#
# Fixes carried in (CL-C / CL-D):
#   · mktemp per run + truncate     (was a shared /tmp/bm.b, /tmp/xf.b — stale-body risk)
#   · -k is an explicit DECISION    (was unconditional `curl -sk` on every probe)
#   · PRE-FLIGHT positive control   (differ proven to detect a known difference BEFORE the run)
#   · rate gate: --slow = 2s single-threaded for prod fintech/bank/critical-infra
#   · first WAF/challenge signal aborts the run (CL-C)
#
# USAGE
#   bypass_matrix.sh <url> [--insecure-ok] [--slow] [--only methods|path|trust|cors]
#   bypass_matrix.sh --selftest
set -uo pipefail
CURL=/usr/bin/curl
UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36'

B=$(mktemp "${TMPDIR:-/tmp}/bm.XXXXXXXX"); H=$(mktemp "${TMPDIR:-/tmp}/bh.XXXXXXXX")
trap 'rm -f "$B" "$H"' EXIT
K=(); SLEEP=0.9; ONLY=all; BASE_SIG=""; TRIPPED=0

sig(){ # sig <curl args...> -> "code|bytes"; body in $B, headers in $H
  : > "$B"; : > "$H"                       # truncate ALWAYS — never inherit a prior body
  local c; c=$("$CURL" -sS -o "$B" -D "$H" --globoff -A "$UA" --max-time 15 \
                --connect-timeout 8 -w '%{http_code}' "${K[@]}" "$@" 2>/dev/null) || c=000
  if [[ "$c" == "000" ]]; then echo "000|CONN"; return; fi   # 000 = connection, not a verdict
  echo "$c|$(wc -c <"$B")"
}
waf(){ # abort on first bot/WAF signal — CL-C
  command grep -qiE 'cf-mitigated|just a moment|attention required|captcha|akamai reference|incapsula' "$B" "$H" 2>/dev/null \
    && { echo "  ⛔ WAF/BOT SIGNAL — stopping the matrix (CL-C: cooldown, resume single-threaded)"; TRIPPED=1; }
}
row(){ # row [--cmp-code] [--base SIG] <label> <curl args...>
  [[ $TRIPPED -eq 1 ]] && return
  # Two false-POSITIVE generators found by running this tool against a live Apache ACL
  # (PROGRAM_101, 2026-07-31) — both fixed here:
  #   --cmp-code : HEAD always returns 0 bytes, so a code|bytes signature flags it every
  #                time. Compare code only for bodyless methods.
  #   --base     : the URL-rewrite arm requests $base/ but was diffed against the $path
  #                baseline — guaranteed ★ on any host where / differs from $path.
  #                It now carries its own baseline.
  local cmp=sig base="$BASE_SIG"
  while :; do case "${1:-}" in
    --cmp-code) cmp=code; shift ;; --base) base="$2"; shift 2 ;; *) break ;; esac; done
  local l="$1"; shift; local s; s=$(sig "$@")
  # a 000 is a CONNECTION result, never a bypass — retry once before reporting it
  [[ "$s" == 000\|* ]] && { sleep 2; s=$(sig "$@"); }
  local a="$s" b="$base"
  [[ "$cmp" == code ]] && { a="${s%%|*}"; b="${base%%|*}"; }
  if [[ "$a" != "$b" ]]; then
    if [[ "$s" == 000\|* ]]; then
      printf '    (000 twice on %s — connection, not a bypass; check egress)\n' "$l"
    else
      printf '  ★ %-52s %-10s %s\n' "$l" "$s" "$(head -c 70 "$B" | tr -d '\n\r')"
    fi
  fi
  waf; sleep "$SLEEP"
}

retry_sig(){ # a 000 is a CONNECTION result, never evidence — retry once before believing it
  local s; s=$(sig "$@"); [[ "$s" == 000\|* ]] && { sleep 2; s=$(sig "$@"); }; echo "$s"
}
selftest(){
  echo "── bypass_matrix pre-flight positive control ──"
  # The differ must (a) call identical responses identical, (b) call a KNOWN difference different.
  # Control pair is deliberately nasty: example.com/ = 200|559 and a bogus path = 404|559 —
  # SAME byte size, different code. A size-only differ FAILS this, which is the point.
  # A 000 on either arm is a HARNESS failure, never a pass: assert both are real HTTP.
  BASE_SIG=$(retry_sig https://example.com/)
  local same diff; same=$(retry_sig https://example.com/)
  diff=$(retry_sig https://example.com/definitely-not-a-real-path-mythos)
  echo "   baseline            : $BASE_SIG"
  echo "   identical replay    : $same   $([[ "$same" == "$BASE_SIG" ]] && echo PASS || echo FAIL)"
  echo "   known-different path: $diff   $([[ "$diff" != "$BASE_SIG" && "$diff" != 000\|* ]] && echo PASS || echo FAIL)"
  if [[ "$BASE_SIG" == 000\|* || "$same" == 000\|* || "$diff" == 000\|* ]]; then
    echo "── differ INCONCLUSIVE — a control arm returned 000 (no egress / DNS / TLS)."
    echo "   That is a HARNESS result, not a differ result. Fix egress before running a matrix. ──"
    return 1
  fi
  [[ "$same" == "$BASE_SIG" && "$diff" != "$BASE_SIG" ]] \
    && { echo "── differ VALIDATED (2/2) — safe to run a matrix ──"; return 0; } \
    || { echo "── differ FAILED — do NOT trust any 'no bypass' result from it ──"; return 1; }
}
[[ "${1:-}" == "--selftest" ]] && { selftest; exit $?; }

U="${1:-}"; shift || true
[[ -n "$U" ]] || { echo "usage: bypass_matrix.sh <url> [--insecure-ok] [--slow] [--only S] | --selftest"; exit 2; }
while [[ $# -gt 0 ]]; do
  case "$1" in
    --insecure-ok) K+=( -k ); shift ;;
    --slow)        SLEEP=2.0; shift ;;
    --only)        ONLY="${2:-all}"; shift 2 ;;
    *)             shift ;;
  esac
done

host=$(sed -E 's|^https?://([^/]+).*|\1|' <<<"$U")
path=$(sed -E 's|^https?://[^/]+||' <<<"$U"); [[ -z "$path" ]] && path=/
base="https://$host"

echo "════ bypass_matrix $U"
[[ ${#K[@]} -gt 0 ]] && echo "    TLS: -k EXPLICITLY SET (private-CA expected)" || echo "    TLS: verifying (no -k)"
echo "    spacing: ${SLEEP}s single-threaded$([[ "$SLEEP" == "2.0" ]] && echo '  [--slow: prod fintech gate]')"

selftest >/dev/null 2>&1 || { echo "  ⛔ PRE-FLIGHT FAILED — differ not validated; aborting."; exit 1; }
echo "    pre-flight: differ VALIDATED"

BASE_SIG=$(sig "$U")
echo "    baseline: $BASE_SIG  $(head -c 60 "$B" | tr -d '\n\r')"
echo "    (only rows whose CLASS differs from baseline are printed)"

if [[ "$ONLY" == all || "$ONLY" == methods ]]; then echo "  ── methods + override ──"
  for m in POST PUT PATCH DELETE OPTIONS TRACE PROPFIND MKCOL LOCK FOO; do row "method=$m" -X "$m" "$U"; done
  row --cmp-code "method=HEAD" -I "$U"   # bodyless: compare code only
  for h in "X-HTTP-Method-Override: GET" "X-HTTP-Method: GET" "X-Method-Override: GET"; do
    row "override ${h%%:*}" -X POST "$U" -H "$h"; done
fi

if [[ "$ONLY" == all || "$ONLY" == path ]]; then echo "  ── path mutations ──"
  for p in "$path/" "$path/." "$path//" "/.$path" "$path%20" "$path%09" "$path?" "$path??" "$path#" \
           "$path.json" "$path.html" "$path/~" "$path%2e" "${path}%00" "$path;" "$path/..;/" "${path}%2f"; do
    row "path $p" "$base$p"; done
  ROOT_SIG=$(sig "$base/")            # rewrite arm requests $base/ — it needs ITS OWN baseline
  echo "     (rewrite arm baseline = $base/ -> $ROOT_SIG)"
  for h in "X-Original-URL: $path" "X-Rewrite-URL: $path" "X-Override-URL: $path" "X-Originating-URL: $path"; do
    row --base "$ROOT_SIG" "rewrite ${h%%:*}" "$base/" -H "$h"; done
  row "http/1.0" --http1.0 "$U"; row "http/1.1" --http1.1 "$U"; row "http/2" --http2 "$U"
fi

if [[ "$ONLY" == all || "$ONLY" == trust ]]; then echo "  ── trust / forwarding headers (merged from xforward_matrix) ──"
  for h in "X-Forwarded-For: 127.0.0.1" "X-Forwarded-For: 10.0.0.1" "X-Forwarded-For: 192.168.1.1" \
           "X-Forwarded-For: localhost" "X-Forwarded-For: 127.0.0.1, 127.0.0.1" "X-Real-IP: 127.0.0.1" \
           "X-Originating-IP: 127.0.0.1" "Client-IP: 127.0.0.1" "True-Client-IP: 127.0.0.1" \
           "CF-Connecting-IP: 127.0.0.1" "X-Remote-Addr: 127.0.0.1" "X-Client-IP: 127.0.0.1" \
           "X-Cluster-Client-IP: 127.0.0.1" "Forwarded: for=127.0.0.1;by=127.0.0.1" \
           "X-Custom-IP-Authorization: 127.0.0.1" "X-Forwarded-Host: localhost" "X-Forwarded-Proto: http" \
           "X-Forwarded-Port: 80" "X-Forwarded-Server: localhost" "X-Envoy-External-Address: 127.0.0.1" \
           "X-Envoy-Internal: true" "X-Envoy-Original-Path: /" \
           "X-Forwarded-Client-Cert: By=spiffe://cluster.local/ns/default/sa/admin" \
           "Authorization: Bearer null" "Authorization: Basic Og==" "X-Api-Key: 1" "X-Auth-Token: 1" \
           "Referer: $base$path"; do
    row "hdr ${h%%:*}=${h#*: }" "$U" -H "$h"; done
fi

if [[ "$ONLY" == all || "$ONLY" == cors ]]; then echo "  ── CORS / origin reflection (merged from cors_matrix) ──"
  echo "     CRITICAL shape: ACAO reflects attacker origin AND ACAC:true = any site reads authed data"
  for O in "https://evil.example.com" "null" "$base" "${base}.evil.com" "http://$host" "https://sub.$host"; do
    [[ $TRIPPED -eq 1 ]] && break
    : > "$B"; : > "$H"
    "$CURL" -sS -D "$H" -o "$B" -A "$UA" --max-time 15 "${K[@]}" "$U" -H "Origin: $O" >/dev/null 2>&1 || true
    acao=$(awk -F': ' 'tolower($1)=="access-control-allow-origin"{gsub(/\r/,"",$2);print $2;exit}' "$H")
    acac=$(awk -F': ' 'tolower($1)=="access-control-allow-credentials"{gsub(/\r/,"",$2);print $2;exit}' "$H")
    code=$(awk 'NR==1{print $2;exit}' "$H")
    flag=""; [[ "$acao" == "$O" ]] && flag="  ★REFLECTED"; [[ "$acao" == "*" ]] && flag="  (wildcard)"
    [[ "$acac" == "true" && -n "$flag" ]] && flag="$flag +CREDENTIALS ★★★"
    printf '   %-34s http=%-5s ACAO=%-30s ACAC=%-6s%s\n' "$O" "${code:--}" "${acao:--}" "${acac:--}" "$flag"
    waf; sleep "$SLEEP"
  done
fi
echo "════ done$([[ $TRIPPED -eq 1 ]] && echo ' (ABORTED on WAF signal)')"
