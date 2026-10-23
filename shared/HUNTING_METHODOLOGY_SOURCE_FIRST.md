# SOURCE-FIRST HUNTING - methodology shift for all hunters
_by: claude (audit seat) · 2026-10-16 · distribute to all solos (grok / kimi / dsclaude) + RESEARCHER._
_Derived from a dataset: ~90 HackerOne public disclosures from the last ~30 days (`~/targets/activity.txt`), read as evidence of what actually pays, where, and how it was found. Every external reference verified 2026-10-16 (section 8)._

---

## 0. Why this doc exists (the honest problem)
We have spent weeks black-box probing programs whose source is PUBLISHED, and trying to force sign-only, framing-dependent bugs past "working-as-intended" walls (PROGRAM_71 decode-depth #4064515, ALLOW-* family). That is the low-yield quadrant. The disclosure data says the people getting paid right now do something different and repeatable. This doc is the shift. Follow it.

## 1. The evidence (what ~90 disclosures this month actually are)
Counted and categorized from the feed:
- **~65 of ~90 are deep SOURCE audits of a SINGLE codebase, usually by ONE person**, attacking a trusting client from a malicious server or a parser with crafted input.
  - curl: ~40 reports, ~20 by one hunter (giant_anteater). Connection-identity reuse (Negotiate / mTLS / client-cert bleeding across origins), HSTS store corruption, cookie-jar erasure, protocol state-machine confusion (TFTP / IMAP / FTP), UAF. No payloads - a malicious server and a careful read of the C.
  - MariaDB: ~25 reports, ~4 hunters (fg0x0, lukas_kupczyk, vortfu, ...). Server-controlled length / count / offset / iteration-count trusted by the client -> stack overflow, integer underflow, OOB read, CPU-exhaustion. Plus legacy/compat features (#mysql50#, DATA DIRECTORY) and orphaned-grant privesc.
- **The web-app wins cluster into 3 shapes, all found by MAPPING surface, not spraying:**
  1. Authz-asymmetry / second path: one resource, two routes, one route enforces the check and the other does not. bbPress private content via REST-by-ID while the list query filters it; Nextcloud OIDC enforced in browser flow but not bearer token; Monero restricted-ZMQ bypasses restricted-HTTP caps; Nextcloud cross-user lock via absolute DAV path; Nextcloud Circles IDOR. THE most repeated paying web shape.
  2. Forgotten auth: an endpoint that should be authed is not. Essity unauth self-registration into a supplier portal; Essity unauth chat API (read/write/delete anyone's history); WordPress nopriv AJAX.
  3. Secret to a telemetry sink: HackerOne Code leaked live password-reset tokens to Datadog RUM and to Segment (two separate reports).
- **The tells that told them where to look (this is the gold):**
  - "Incomplete fix for CVE-X" / "regression in 8.22.0" / "still allows X after PR #58754" -> they re-audited a PATCH and found it partial, or diffed a VERSION and found a guard removed.
  - "Upstream has the guard, this copy does not" -> Amplify velocity-template (upstream added prototype-chain guards, the vendored copy did not). Our own C22 is exactly this (upstream `RECEIVER_NOT_EXPORTED` -> German fork `RECEIVER_EXPORTED`).
  - Any value read "from the server / from the wire" used to size an allocation, index a buffer, bound a loop, or drive a fetch, WITHOUT validation.
- **Severity reality:** a clever Android local bypass paid $150 (Nextcloud PIN-via-back-button); an IDOR that leaked data paid $15,000 (HackerOne). Impact clarity beats cleverness. The resolved bugs have self-evident impact: I read data I should not, I crashed it, I ran code, I locked you out.

## 2. The mindset shift (five shifts, in priority order)
1. **Source-first, not black-box.** When the source is published (common_codes is fully published; so are most libs), READ it. Live probing is for confirming a hypothesis the source gave you, not for discovering the bug by poking.
2. **Trusting-client / malicious-server model.** The richest memory-safety and trust-confusion bugs live where a client trusts data a server (or a peer, or an attestation, or a status list, or a `request_uri`) sent it. Flip the usual direction: assume you control the server/peer, and hunt what the client does with your bytes. Ref: curl threat model, CVE-2020-8284 (section 8).
3. **Self-evident impact only.** Stop building reports whose impact needs a framing argument to land (that is how PROGRAM_71 decode-depth died). Pick bugs where the triager sees the impact without being argued into it.
4. **Depth over breadth.** The winners mine ONE component for weeks (giant_anteater=curl, fg0x0=MariaDB connectors). Stop spreading across 5 programs. Pick the richest source-available, highest-payout target and go deep.
5. **Variant / patch / diff thinking.** Bugs cluster. A fixed bug has siblings the fix missed; a fork lags its upstream's security fixes; a refactor regresses an old fix. Ref: Project Zero - half of 2022 in-the-wild 0-days were variants of earlier bugs, and vendors routinely patch only the PoC path (section 8).

---

## 3. THE METHODS
Each method: Indicator (when to reach for it) / Method / Why it pays / Evidence (feed) / Reference / How to run / common_codes mapping.

### M1 - Variant analysis + fork/version diff
- **Indicator:** the target is a FORK, a vendored copy, or has version history / an upstream reference implementation.
- **Method:** mechanically diff fork-vs-upstream and version N-vs-N-1 for removed guards, flipped export/permission flags, loosened validation, un-backported security fixes. Then model the bug as a query and sweep for every sibling.
- **Why it pays:** forks lag upstream security fixes; refactors regress old fixes; one query finds the variants manual review misses.
- **Evidence:** Amplify velocity-template (upstream had prototype-chain guards, copy did not); our C22 (one flipped `RECEIVER_EXPORTED` flag vs upstream); the curl "regression in 8.22.0" cluster.
- **Reference:** Project Zero 2022 in-the-wild 0-day analysis (variants); GitHub multi-repository variant analysis + CodeQL (section 8).
- **How to run:** `git diff` fork against the upstream tag; for a non-git copy, clone upstream and `diff -r` the shared module; grep every security-relevant primitive (export flags, permission args, `validate`, `verify`, `check`, `isTrusted`, bound checks) and compare both sides. Promote every one-sided difference to a lead.
- **common_codes:** diff the whole `de-eudi-wallet-{android,ios,backend}` fork against `eu-digital-identity-wallet` upstream. C22 came from ONE file; run it across all three repos, for every flipped flag / removed guard / loosened check. HIGH yield, pure source read.

### M2 - Patch-gap / incomplete-fix re-audit
- **Indicator:** the program or a dependency has recent security commits, a changelog, or published CVEs.
- **Method:** for each recent fix, re-test the exact bug AND the sibling code paths the fix did not touch. Ask "did they fix the bug, or only the PoC's path?"
- **Why it pays:** vendors block the demonstrated path, not the class. Ref: Project Zero.
- **Evidence:** Weblate incomplete fix for CVE-2022-23915 (Mercurial argument injection, re-exploited -> new CVE-2026-86035); curl "Secure=1 cookie flag bypasses the 8.22.0 fix"; Rails ActionText "still allows javascript: after PR #58754."
- **Reference:** Project Zero (section 8).
- **How to run:** pull the component's security advisories / recent commits touching parsing, auth, validation; read the fix diff; construct the input that takes the OTHER branch to the same sink.
- **common_codes:** re-audit the trust-critical libs' recent fixes - `at.asitplus.warden:makoto 1.2.0` (attestation validation), `com.authlete:http-message-signatures 1.8` (RFC 9421), nimbus-jose-jwt, bcpkix - and the fork's own commit history.

### M3 - Trusting-client / server-controlled-value audit (the curl/MariaDB recipe)
- **Indicator:** a client, SDK, connector, or app parses data from a server / peer / token / attestation / status-list / signed-request it did not generate.
- **Method:** enumerate every value read from the wire and used to (a) size an allocation, (b) index/offset a buffer, (c) bound a loop, (d) drive a fetch (a URL), (e) choose an algorithm, (f) set an iteration/work count. For each, ask "what if a malicious server sends this unvalidated or absurd?"
- **Why it pays:** this is where the memory-safety, DoS, and trust-confusion bugs in this entire feed live, and the impact is self-evident (crash / OOB / leak / infinite work).
- **Evidence:** the whole curl + MariaDB-connector cluster - server-controlled `field->length` -> stack overflow; malicious handshake version string -> integer wrap -> heap OOB; server-controlled PBKDF2 iteration count -> 1.07e9 rounds CPU-DoS; curl PASV response -> client connects to attacker IP (CVE-2020-8284).
- **Reference:** curl threat model 2022; libcurl security docs; CWE-20 / CWE-130 / CWE-400 (section 8).
- **How to run:** stand up a malicious server / mutate captured responses (we have mitmproxy + REA `inspect_web_network_capture`); send out-of-range lengths, counts, iteration counts, negative-coercible values, absurd URLs; watch the client.
- **common_codes:** the wallet is a client that trusts enormous server-sent crypto material - MDVM tokens, App Attest / key attestation, status lists, RFC 9421 signatures, OpenID4VP `request_uri`s. Audit each: does the wallet/backend bound-check server-sent lengths/counts, validate the `request_uri` scheme/host BEFORE fetching (RFC 9101 says it fetches it - C22 proved it fetches an attacker URL), enforce `created`/`expires` on RFC 9421 sigs, pin attestation anchors? This is the real Extreme surface.

### M4 - Second-path authz-asymmetry inventory (BOLA / BFLA / transport parity)
- **Indicator:** a sensitive operation is reachable more than one way (REST vs batch vs automation vs webhook vs alternate transport vs by-ID vs query vs signed-vs-token vs browser-vs-API).
- **Method:** build a COMPLETE inventory of every way to invoke each sensitive op, then diff whether the authz/validation is byte-identical on each path. The bug is the path that forgot the check.
- **Why it pays:** the single most repeated paying web shape in the feed; impact is self-evident (read/modify another user's object).
- **Evidence:** bbPress REST-by-ID vs query filter; Nextcloud OIDC bearer vs browser; Monero restricted-ZMQ vs restricted-HTTP; Nextcloud absolute-DAV-path cross-user lock; our own PROGRAM_71 path-splits and C22 (broadcast path vs gated activity path).
- **Reference:** OWASP API Security Top 10 2023 - API1 BOLA, API5 BFLA, API3 BOPLA; PortSwigger access-control (method-based + user-id-parameter labs) (section 8).
- **How to run:** list routes/methods/transports (source + OpenAPI + client RE); for each sensitive object/function, enumerate the alternate invocations; two-account diff each; change HTTP method; swap an object id in a non-authz'd position.
- **common_codes:** the backend is a multi-component trust fabric (RWSCA / WPB / MDVM / StatusList / PNS). Inventory every op across components and ask: does component A accept component B's instance id? Does a by-id fetch skip the filter the list applies? Does the RFC 9421-signed path enforce the same gate as a token/session path? (Tenant line: one minimal victim record only.)

### M5 - Forgotten-auth sweep
- **Indicator:** any multi-endpoint surface, especially secondary/admin/internal/nopriv endpoints.
- **Method:** enumerate every endpoint and find the ones that skip auth entirely or skip the gate their siblings apply.
- **Why it pays:** self-evident, often Critical, trivially demonstrated.
- **Evidence:** Essity unauth self-registration -> live vendor data; Essity unauth chat API; WordPress `nopriv` AJAX handlers returning draft/private posts; R3 default-empty join key -> full Artifactory admin.
- **Reference:** OWASP WSTG; OWASP API Top 10 (section 8).
- **How to run:** route inventory from source/client; hit each unauthenticated and with a low-priv token; flag any that return real data or mutate.
- **common_codes:** sweep the backend route table; the `/challenge` unbound-nonce behavior already shows some endpoints mint without parsing - enumerate the rest.

### M6 - Secret-to-sink (telemetry / logs / analytics)
- **Indicator:** the app integrates analytics/RUM/telemetry/logging, or puts tokens in URLs.
- **Method:** trace every secret/token (reset, verification, session, registration) and check whether it reaches a telemetry SDK, a log, a URL query, or an error body.
- **Why it pays:** live single-use credential in a third-party sink = account takeover with self-evident impact.
- **Evidence:** HackerOne Code -> Datadog RUM and -> Segment (two reports); the IDOR whose 403 body still leaked the object ($15k).
- **Reference:** CWE-532, CWE-200 (section 8).
- **common_codes:** the capture shows a `telemetry.*.youniqx` host. That host is OOS as a TARGET, but if the in-scope app/backend EMITS a token or PII to it (URL or payload), the bug is in the in-scope component. Grep captured flows + source for tokens reaching telemetry / logs.

### M7 - Legacy/compat + optional-plugin surface
- **Indicator:** the target has legacy-compat features, optional plugins/modules, or "advanced" features off the happy path.
- **Method:** hunt the code nobody reviews - compat shims, optional engines, secondary apps.
- **Why it pays:** guards are weakest where usage is rare. Evidence: MariaDB #mysql50# aliases, DATA/INDEX DIRECTORY, HandlerSocket, CONNECT engine; the entire Nextcloud cluster is APPS (Circles, Deck, files_lock, Photos, Collectives), not core.
- **common_codes:** the non-happy-path flows - resume vs present, re-registration, recovery, the `vci.resume.eudi.action` broadcast (also exported, under-examined in C22).

### M8 - Mobile exported / runtime-registered component audit (the C22 class)
- **Indicator:** an Android/iOS app with IPC surface (receivers, services, activities, deep links, content providers).
- **Method:** enumerate exported components AND runtime-registered receivers (the latter do NOT appear in the manifest - they need code/runtime analysis), then review each handler for a missing permission/gate.
- **Why it pays:** real control-bypass class; but see severity note - local/same-device bugs are LOW unless they reach credentials or data, so chain to data impact or keep severity honest.
- **Evidence:** C22 (exported runtime receiver, no permission, upstream protects it); Nextcloud PIN-via-back-button ($150, the anchor for "local bypass is low").
- **Reference:** OWASP MASTG MASTG-TEST-0366 (exported unprotected receivers), MASWE-0063; Android "insecure broadcast receiver" risk doc; CWE-926/927 (section 8). MASTG explicitly notes runtime `Context.registerReceiver` receivers are invisible in the manifest - C22 is exactly that.
- **How to run:** jadx + `mcp__rea__inspect_android_package` / `search_android_classes`; grep `registerReceiver`, `exported`, `<intent-filter>`; trace each handler to its sink; then decide if it reaches data (raises severity) or stays local (keep it LOW).

---

## 4. Tooling (on this box, ready)
- **REA MCP** (`mcp__rea__*`, loaded after restart) + CLI (`~/.local/bin/rea`): `inspect_android_package` / `search_android_classes` / `inspect_android_method` (Android), `analyze_web_bundle` / `inspect_web_network_capture` (needs `REA_MITMDUMP_COMMAND=/home/RESEARCHER/targets/common_codes/tools/mitmdump`) / `compare_source_to_bundle` / `extract_artifact`. See `~/targets/common_codes/notes/REA_ATTACK_GUIDE.md`.
- **jadx 1.5.6** `~/.local/bin/jadx` - DEX decompile (needs an APK on disk).
- **git diff / `diff -r`** - the M1 workhorse. Clone the upstream, diff the fork.
- **Semgrep / ripgrep** - cheap variant analysis: model the bug as a pattern, sweep the repo. For the server-controlled-value audit, grep allocation/index/loop/fetch sinks fed by wire values.
- **CodeQL (MRVA)** - heavier variant analysis across a codebase; model a known bug as a query, find siblings. (Not installed here; use ripgrep/Semgrep locally, or note it as the upgrade path.)
- **mitmproxy 12.2.3** `~/targets/common_codes/tools/mitmdump` + ngrok - the malicious-server / mutate-captured-response harness for M3.

## 5. Target playbooks
### 5a - common_codes (PRIMARY - commit depth here)
Richest fit: full source published, a client that trusts massive server-sent crypto material, a multi-component trust fabric, Extreme $15-40k. Run in this order:
1. **M1 whole-repo fork diff** (all 3 repos vs upstream) - pure source read, already produced C22.
2. **M3 trusting-client audit** - the attestation (makoto 1.2.0) + RFC 9421 (authlete 1.8) + status-list + `request_uri` fetch paths. The real Extreme.
3. **M4 second-path authz inventory** across RWSCA/WPB/MDVM/StatusList/PNS.
4. **M2 patch re-audit** of the libs + fork history.
5. M5/M8 sweeps as surface is mapped.
Pre-file gates still bind (sanctions screening, closes-AI-reports, HIGH dup) - but those are FILING gates; hunt freely. Lead every report with self-evident impact.

### 5b - PROGRAM_71 (stop forcing the wall)
Decode-depth family is WAI-dead (#4064515, see `~/targets/PROGRAM_71/STATE/DEADENDS.md`). Keep only the live canonicalization/extractor-divergence reports (#4063518 Tron is the paid-vein class; #4051915 Tempo is MODERATE, comment staged). Do NOT file more sign-only framing bugs. Energy moves to common_codes.

### 5c - new-target intake (general)
Before probing: is the source published? (-> M1/M3 first). Is it a fork? (-> M1). Does a client trust server data? (-> M3). Multiple paths to one op? (-> M4). Only black-box? Then map surface (M4/M5) before any spray.

## 6. Operating rules for all hunters (binds every solo)
- Depth over breadth: one target, one component, mined fully, beats five shallow sweeps.
- Self-evident impact only: if the impact needs a framing argument, it is not ready - chain it to data/code/crash/lockout first.
- Source-first: read the published code; use live probes to CONFIRM, not to discover.
- Honest severity, file at the proven floor, name the ceiling. Local/same-device = LOW unless it reaches data.
- Survive a WAI wall ONLY via "no correct config exists" - and know that even that was overruled once (PROGRAM_71 decode-depth); it is not guaranteed.
- Persist every step; read-before-persist; `_by:` + timestamp; never clobber another solo's STATE.
- Tenant-data line: cross-user proof = ONE minimal victim record. Human-gated: submissions, prod writes, destructive actions, out-of-scope, non-RESEARCHER creds.

## 7. One-line summary
Stop poking. Read the fork, diff it against upstream, hunt what the client does with a malicious server's bytes, inventory every second path to each sensitive op, and only file bugs whose impact a triager sees without being argued into it.

## 8. References (verified 2026-10-16)
- Project Zero, 2022 in-the-wild 0-day analysis (variants of prior bugs; root-cause/variant/patch/exploit analysis; vendors patch only the PoC path): https://projectzero.google/2022/06/2022-0-day-in-wild-exploitationso-far.html
- GitHub, Multi-repository variant analysis (MRVA) with CodeQL: https://github.blog/security/vulnerability-research/multi-repository-variant-analysis-a-powerful-new-way-to-perform-security-research-across-github/ ; CodeQL: https://codeql.github.com/
- OWASP API Security Top 10 (2023) - API1 BOLA, API5 BFLA, API3 BOPLA: https://owasp.org/www-project-api-security/
- PortSwigger Web Security Academy, Access control vulnerabilities (method-based, user-id-parameter labs): https://portswigger.net/web-security/access-control
- OWASP WSTG (Web Security Testing Guide): https://owasp.org/www-project-web-security-testing-guide/
- OWASP MASTG - exported/unprotected broadcast receivers MASTG-TEST-0366: https://mas.owasp.org/MASTG/tests/android/MASVS-PLATFORM/MASTG-TEST-0366/ ; MASWE-0063 Insecure Broadcast Receivers: https://mas.owasp.org/MASWE/MASVS-PLATFORM/MASWE-0063/
- Android developer, Insecure broadcast receiver risk: https://developer.android.com/privacy-and-security/risks/insecure-broadcast-receiver
- curl threat model 2022 (Trail of Bits / OpenSSF): https://curl.se/docs/audit/threatmodel-2022.pdf ; libcurl security: https://curl.se/libcurl/c/libcurl-security.html ; CVE-2020-8284 (PASV response makes curl connect to attacker-chosen IP)
- RFC 9421 HTTP Message Signatures (Feb 2024): https://www.rfc-editor.org/rfc/rfc9421
- RFC 9101 (JWT-Secured Authorization Request / JAR; defines `request_uri` semantics): https://www.rfc-editor.org/rfc/rfc9101
- OpenID for Verifiable Presentations 1.0 (wallet fetches the request by following `request_uri`): https://openid.net/specs/ (openid-4-verifiable-presentations-1_0)
- EU Digital Identity Wallet Architecture and Reference Framework (ARF): https://github.com/eu-digital-identity-wallet/eudi-doc-architecture-and-reference-framework
- CWE-20 (Improper Input Validation), CWE-130 (Improper Handling of Length), CWE-400 (Uncontrolled Resource Consumption), CWE-532 (Info Exposure through Logs), CWE-926/927 (Improper Export of Android App Components): https://cwe.mitre.org/
