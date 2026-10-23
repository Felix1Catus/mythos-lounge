# SHAPES — P1 shape library + anomaly taxonomy (read when triaging surfaces/leads)

## THE P1 SHAPE LIBRARY — recognize Criticals fast
When you see the shape, drop everything and probe.

- **Identity mint:** password-set / magic-link / token endpoints not bound to identity proof ·
  session minted via cross-context replay · OAuth grant-type confusion
  (`authorization_code`↔`implicit`↔`client_credentials`) · account pre-creation /
  email-collision · JWT `none`/weak-secret/kid-injection.
- **IDOR:** numeric/UUID key on identity-money-PII object without per-request ownership
  re-check · nested objects riding parent auth · GraphQL node queries · "preview/export/share"
  endpoints that skip the check.
- **SSRF:** anything that fetches a URL — webhooks, importers, URL preview, PDF/image
  generators, RSS, oEmbed, "test connection" — → metadata (169.254.169.254), localhost,
  RFC1918, cloud IAM.
- **Unauth / cross-tenant state-write:** POST/PUT/PATCH/DELETE reachable without auth or
  across orgs · mass-assignment of `role`/`price`/`verified`/`owner` · hidden/debug/admin mounts.
- **Payment/money:** client-side price/currency · negative/fractional quantities · replayed
  success callbacks · race on redeem/refund/transfer (TOCTOU) · coupon stacking.
- **RCE-family:** template injection (error echoes are the tell) · deserialization ·
  upload → execution path · command injection in exporters/converters/notifiers ·
  dangerous eval of "expression" features.
- **Config/infra:** exposed actuator/debug/console · dangling subdomain takeover · permissive
  CORS on authenticated APIs · leaked keys with LIVE scope (prove one minimal call).

An endpoint is interesting in proportion to how much authority it touches and how little it checks.

## ANOMALY TAXONOMY — chase INSTANTLY (3-probe budget before dropping any)
- Status inconsistent across two near-identical inputs.
- Timing delta (~40ms+ = something executed / compared).
- Error too specific: stack trace, version string, SQL fragment, internal hostname.
- An echoed field — reflection is an injection candidate until proven otherwise.
- A header that shouldn't exist: debug flags, internal IPs, `x-*` leaks.
- An endpoint that 500s where its neighbor 404s — it exists and mishandles you.
- Behavior changing with method / content-type / case / encoding — two parsers disagree.
- Anything the JS client calls that the UI never exposes.
- A 403/401 that flips on trivial variation (trailing slash, case, `;`, `%2f`) — a filter; filters have seams.
