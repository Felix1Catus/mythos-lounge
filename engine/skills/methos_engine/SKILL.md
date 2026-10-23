---
name: methos_engine
description: The universal adaptive attack engine — reverse-engineer any target, try hundreds of angles, learn from every response, chain findings creatively. This IS METHOS. It overrides the systematic MYTHOS instinct with a creative, relentless, adaptive hunter mindset. Use on EVERY target, EVERY finding, EVERY barrier. Never stop at the first NO.
---

# METHOS ENGINE — Universal Adaptive Attack Engine

## OVERRIDE (2026-09-29 — this beats Phase 1–5 below)
This file is a palette, not the hunt. Do not reverse-engineer a stack, run an 80-row matrix,
or finish the exhaustion checklist before the shot. Replay the real client. Read the error
class, not the status. Canonical refusal, then one structural variant. A later class means
the check between them was skipped — escalate that. If the client's body and the server's
sentence already name the crack, send that one request. Do not pad it to seven. Seven axes
apply only while the class is still the one the author expected. Pull a row from below only
when the class has stopped moving. Solo. Do not ask the user.

## WHERE THIS SKILL SITS (routing — read first)
This is the **breadth angle-LIBRARY**: 80 concrete attack angles across 8 trust-boundary
classes. It is a *palette to pull from*, NOT a checklist to run top-to-bottom (running 7
of 80 and stopping is the documented failure mode that created `methos_generative_engine`).
- **Driver = `methos_generative_engine`**: deconstruct the target's architecture, then INVENT
  target-specific attacks — reaching into THIS library for primitives to recombine.
- **Barriers = `zero_day_mindset`**: when a specific wall (403/JWT/auth/crypto) blocks you.
- **Instrument = `differential_oracle`**: when you must decide if a result/boundary is REAL.
Use this skill as the recombination palette + the Phase-5 exhaustion checklist — not as the
primary loop. The primary loop is generative.

## What This Is
MYTHOS follows checklists. METHOS hunts. MYTHOS persists results. METHOS
relentlessly adapts its attack until it finds the hole or exhausts every
angle. This skill overrides the cautious, systematic instinct with a
creative, aggressive, adaptive one.

## Trigger
- Starting recon on ANY new target
- About to move on from ANY finding (the class has not moved — loosen one axis, do not list ten first)
- Hit ANY barrier (403, auth gate, algorithm mismatch, rate limit, WAF)
- The words "DISPROVEN", "BLOCKED", "can't", "doesn't work" enter your mind
- About to say "swept, clean, moving on" (the class has not moved — loosen one axis)
- ANYWHERE, ANYTIME — this is the default mode

## PHASE 1: REVERSE ENGINEER THE TARGET
Palette. Do not run this before the request. Replay the real client in the same pass as the shot.

### Step 1: What Technology Stack?
- Framework? (Next.js, React, Vue, Angular — from build output, chunk names)
- Build system? (Webpack, Vite, Rollup — from chunk hashes, manifest format)
- API style? (REST, GraphQL, gRPC, WebSocket — from fetch calls)
- Auth system? (JWT, OAuth, cookie, API key, mTLS — from client code)
- Infrastructure? (CloudFront, Istio/Envoy, nginx, AWS — from headers, TLS cert)
- Backend language? (Node/Python/Java/Go — from error messages, response times)

### Step 2: Map the Data Flows
Trace EVERY user-input to server-response path:
1. Where does user input enter? (URL param, form field, header, body, cookie, WebSocket)
2. What does the CLIENT do with it? (validation, sanitization, encoding)
3. How does it reach the SERVER? (which endpoint, which method, which content-type)
4. What does the SERVER do with it? (parse, validate, query, transform, store)
5. Where does it exit? (response, error message, log, side effect)

### Step 3: Find the Trust Boundaries
Every place where one system trusts another:
- Client trusts server response? → inject malicious response
- Server trusts client input? → parameter tampering
- Service A trusts Service B? → confused deputy, SSRF
- Gateway trusts backend? → cache poisoning, header injection
- Auth system trusts issuer? → JWT forgery, algorithm confusion
- File system trusts upload? → path traversal, RCE

### Step 4: Map the Attack Surface by Behavior
Not just endpoints — **behaviors**:
- Where does the app handle MONEY? (payment, pricing, refunds, credits)
- Where does the app handle IDENTITY? (login, register, auth, tokens, sessions)
- Where does the app handle FILES? (upload, download, preview, import, export)
- Where does the app handle ADMIN? (dashboard, config, user management, moderation)
- Where does the app handle EXTERNAL DATA? (webhooks, OAuth, API callbacks, RSS)
- Where does the app handle CROSS-ORIGIN? (CORS, postMessage, iframe, redirects)

## PHASE 2: THE ADAPTIVE ATTACK MATRIX
Palette. Pull one row when the class has not moved. This matrix does not run before the request.

### Matrix Row 1: Authentication Bypass (10 angles)
1. Direct: brute force, credential stuffing, weak passwords
2. Session: predict session IDs, session fixation, concurrent login
3. Token: JWT alg:none, algorithm confusion, JWK injection, kid traversal
4. OAuth: redirect_uri manipulation, state parameter bypass, scope escalation
5. Social: OAuth account takeover, third-party identity provider bypass
6. Reset: password reset token prediction, reset token reuse, host header injection
7. Registration: duplicate account creation, admin privilege escalation on register
8. Guest: anonymous token escalation, guest→user promotion
9. Error: 500 error token leak, verbose error oracle, timing attack on login
10. Protocol: downgrade to HTTP, remove auth header, empty auth header

### Matrix Row 2: Authorization Escalation (10 angles)
1. IDOR: manipulate object IDs (sequential, UUID pattern, predictable)
2. BOLA: access other users' collections (change user_id in request)
3. Role: change role parameter (admin=true, role=1, is_staff=yes)
4. Path: access admin endpoints (/admin, /api/admin, /_/admin, /.hidden)
5. Method: PUT/DELETE/PATCH on resources you only have GET on
6. Parameter pollution: duplicate params (?id=1&id=2), array params (?id[]=1&id[]=2)
7. Mass assignment: add extra fields to POST body (is_admin, role, permissions)
8. GraphQL: introspection query, query depth attack, field suggestion
9. Header injection: X-Original-User, X-Forwarded-For, X-Real-IP, X-User-ID
10. JWT claim manipulation: add admin claims, change aud, modify scope

### Matrix Row 3: Injection & Code Execution (10 angles)
1. SQL: classic ' OR 1=1, UNION SELECT, time-based blind, error-based
2. NoSQL: {$ne: null}, {$gt: ''}, {$where: 'this.password.length > 0'}
3. Command: ; ls -la, `whoami`, $(cat /etc/passwd), && calc.exe
4. SSTI: {{7*7}}, ${7*7}, <%= 7*7 %>, #{7*7}
5. XPath: ' or '1'='1, ]/parent::node(), count(/child::node())
6. LDAP: *)(uid=*))(&(uid=*
7. XML: XXE, XInclude, DOCTYPE entity expansion
8. CSV: formula injection (=cmd|'/C calc'!A0)
9. HTTP Header: CRLF injection (%0d%0a), Host header injection, X-Forwarded-Host
10. Deserialization: Java ysoserial, Python pickle, PHP unserialize, Node serialize

### Matrix Row 4: Information Disclosure (10 angles)
1. Verbose errors: stack traces, SQL errors, path disclosure, framework version
2. Debug endpoints: /debug, /trace, /actuator, /env, /config, /swagger, /api-docs
3. Backup files: .bak, .old, .orig, .swp, .save, ~, .zip, .tar.gz
4. Source maps: .js.map reveals full source code (download ALL .map files)
5. Directory listing: /uploads/, /assets/, /backup/, /tmp/, /logs/
6. Parameter reflection: reflected XSS, template injection via query params
7. Timing oracle: time-based user enumeration, time-based boolean extraction
8. Error differential: different error messages for different failure modes
9. Header leakage: Server, X-Powered-By, X-Backend-Server, X-Request-ID
10. Cache inspection: Cache-Control, ETag analysis, CDN cache poisoning probe

### Matrix Row 5: Input Validation Bypass (10 angles)
1. Encoding: URL encode (%2f), double encode (%252f), Unicode (%c0%af), overlong UTF-8
2. Case: ADMIN, Admin, aDmIn, case-insensitive filesystem bypass
3. Null byte: filename.php%00.jpg, path%00traversal
4. Alternative syntax: ../ vs ..%2f vs %2e%2e%2f vs ....//
5. Length: oversized input, empty input, boundary values (MAX_INT, 0, -1)
6. Type juggling: 1 vs "1" vs true vs "true" vs 1.0 vs [1]
7. Content-Type: application/json → text/plain → application/xml → multipart/form-data
8. Boundary: CRLF variations, missing boundary, extra boundary, nested multipart
9. Order: reverse parameter order, duplicate params with different values
10. Whitespace: tab, newline, vertical tab, non-breaking space, zero-width chars

### Matrix Row 6: Business Logic Abuse (10 angles)
1. State machine: skip steps (checkout without cart), repeat steps (double-apply coupon)
2. Race condition: two simultaneous requests (double-spend, TOCTOU)
3. Price manipulation: negative price, zero price, overflow price, precision issue
4. Quantity abuse: -1 quantity, MAX_INT quantity, fractional quantity
5. Time manipulation: backdate, future-date, expire sessions early
6. Workflow bypass: access step 3 without completing step 1 and 2
7. Feature abuse: use premium feature without subscription, rate limit bypass
8. Notification abuse: email bombing, SMS flooding, webhook spam
9. Referral abuse: self-referral, referral cycle, unlimited referral credit
10. Cancellation abuse: cancel after receiving benefit, partial refund trick

### Matrix Row 7: Client-Side Attacks (10 angles)
1. XSS: reflected, stored, DOM-based, mutation XSS, prototype pollution
2. CSRF: missing token, predictable token, token in GET, token reuse
3. postMessage: targetOrigin=*, no origin check, wildcards, object injection
4. CORS: misconfigured origin, null origin, credential reflection
5. Clickjacking: X-Frame-Options bypass, frame-busting script detection
6. Open redirect: //evil.com, /\/evil.com, /%5Cevil.com, ?next=evil
7. DOM clobbering: form name collision, anchor href manipulation
8. Prototype pollution: __proto__, constructor, prototype chain poisoning
9. Local storage: read sensitive data, token theft, session hijacking via storage
10. Service worker: malicious SW registration, cache poisoning via SW

### Matrix Row 8: Infrastructure Attacks (10 angles)
1. DNS: subdomain takeover, dangling CNAME, DNS cache poisoning
2. CDN: cache deception, cache poisoning, edge server manipulation
3. WAF: bypass via encoding, oversized payload, chunked encoding, protocol smuggling
4. Load balancer: host header poisoning, path-based routing abuse, stickiness bypass
5. Container: exposed Docker API, Kubernetes API, etcd, kubelet
6. Cloud metadata: 169.254.169.254 (AWS IMDS), 192.0.0.254 (GCP), cloud-init
7. SSRF: internal service scanning, metadata access, cloud API access
8. Reverse proxy: request smuggling (CL.TE, TE.CL), hop-by-hop header abuse
9. TLS: certificate pinning bypass, SNI injection, ALPN confusion
10. Network: port scanning via SSRF, internal service enumeration, VPC probing

## PHASE 3: THE LEARNING LOOP
Every response is data. Adapt based on what you learn.

### Response Analysis Protocol
For EVERY response you get, extract:
1. Status code (200, 301, 302, 400, 401, 403, 404, 500, 502, 503)
2. Content-Type header
3. Server/technology headers
4. Response body hash (for differential analysis)
5. Response time (for timing attacks)
6. Error message content
7. Redirect target
8. Set-Cookie header
9. CORS headers
10. Cache headers

### Pattern Recognition
When you see:
- **403 on some paths but not others** → RBAC pattern, enumerate the boundary
- **Different 404 bodies** → some hit application, some hit gateway (content-differential)
- **500 on malformed input** → potential injection point
- **Different response times** → timing oracle exists
- **Verbose errors** → information disclosure goldmine
- **Different auth errors** → user enumeration via error differential
- **Redirect after auth** → open redirect potential
- **Set-Cookie on unauth request** → session manipulation
- **CORS headers present** → CORS misconfiguration
- **Cache headers inconsistent** → cache poisoning

### Adaptation Rules
1. If direct attack fails → try indirect (different endpoint, different context)
2. If one encoding fails → try 5 others (URL, double-URL, Unicode, base64, HTML entities)
3. If auth blocks → try unauth paths, guest access, error leaks, OAuth
4. If WAF blocks → try encoding, fragmentation, protocol smuggling, oversized payload
5. If rate limit → try distributed requests, header variation, path variation
6. If one tool finds nothing → run 5 different tools (different logic, different patterns)
7. If algorithm A fails → try algorithm B, C, D, E, F (confusion, downgrade, none, etc.)
8. If client-side validation → test server enforcement (bypass client validation)
9. If server-side validation → test validation logic (edge cases, type confusion)
10. If everything fails → reverse engineer the code and find the logic flaw

## PHASE 4: THE CHAIN BUILDER
Every finding is a link. Build chains of 2, 3, 4 links.

### Chain Templates
| Link 1 | + | Link 2 | = | Impact |
|--------|---|--------|---|--------|
| Info disclosure (version, tech stack) | + | Known CVE for that version | = | RCE |
| Auth bypass (weak OAuth) | + | Admin endpoint discovery | = | Full admin access |
| IDOR (user enumeration) | + | Weak password reset | = | Account takeover chain |
| File upload (no validation) | + | Path traversal | = | RCE via uploaded shell |
| SSRF (internal access) | + | Cloud metadata endpoint | = | Cloud credentials |
| JWT alg confusion | + | Refresh token endpoint | = | Permanent session |
| Cache poisoning | + | XSS payload | = | Stored XSS for all users |
| Verbose error | + | SQL injection | = | Data exfiltration via errors |
| CORS misconfig | + | Admin API | = | Admin actions from attacker's site |
| Rate limit bypass | + | Credential stuffing | = | Mass account takeover |

### Chain Discovery Method
1. List ALL findings (even LOWs, even informational)
2. For each finding, ask: "what other finding could I chain this with?"
3. For each pair, ask: "what access/capability does link 1 give me for link 2?"
4. For each viable chain, execute the chain end-to-end
5. Prioritize chains by: ease of execution × impact severity

## PHASE 5: THE EXHAUSTION PROTOCOL
Palette. A target is not done because a count was not met. Done is an infra identity gate with no class flip, or the next request is named.

### Palette checklist (not a gate before the request)
- [ ] The error class moved, or method, host, and scheme share one infra identity gate
- [ ] Ran the full adaptation matrix on every barrier
- [ ] Checked for chains between all findings (pairwise check)
- [ ] Reverse engineered the auth system completely
- [ ] Reverse engineered the payment/price system completely
- [ ] Tested every input point with at least 5 payloads
- [ ] Checked every endpoint with at least 3 HTTP methods
- [ ] Downloaded and analyzed ALL source maps (.js.map)
- [ ] Checked for debug/endpoints (/actuator, /swagger, /graphql, etc.)
- [ ] Enumerated ALL subdomains (passive + active + permutation)
- [ ] Checked ALL verticals/apps in the ecosystem
- [ ] Tried all encoding/escaping variants on injection points
- [ ] Tested for race conditions on state-changing operations
- [ ] Checked for prototype pollution in all JSON inputs
- [ ] Analyzed ALL response headers for leakage
- [ ] Checked for CORS misconfiguration on all API endpoints

### Mandatory Persistence
Every angle tried gets recorded:
- What was tried
- What the result was
- What was learned about the target's defenses
- What the next adaptation should be

Store in: notes/methos_engine_[target]_[date].md

## THE METHOS MANDATE

1. **NEVER accept the first NO** — it's just the first data point
2. **One request if the crack is named** — seven axes only while the class is still the author's
3. **EVERY response is intelligence** — analyze, adapt, retry
4. **CHAIN everything** — two LOWs become one P1
5. **Client bytes and the server sentence, same pass** — do not write the model down before the request
6. **THE BARRIER IS THE TARGET** — 403 means there's something worth protecting
7. **TOOLS ARE EXPENDABLE** — write scripts, throw them away, write better ones
8. **PERSIST THE FAILURES TOO** — they teach what the target defends against
9. **A repeated class is missing knowledge** — loosen one axis; do not pad to a count
10. **MYTHOS IS THE FOUNDATION — METHOS IS THE WEAPON**

## ANTI-PATTERNS PREVENTED
- "Clean sweep, moving on" → the class has not moved; loosen one axis
- "403 = blocked" → 403 = protected asset = try harder
- "No injection point found" → loosen one axis the parser did not expect
- "One finding, one report" → chain it, escalate it, combine it
- "I understand the auth system" → you read the code; send the one request that violates the assumption
- "The WAF blocked me" → the WAF is the target now, bypass it
- "Algorithm mismatch = dead end" → find what the algorithm DOES match
- "Session required = skip" → every session gate has a hole
- "I already enumerated" → enumerate differently (different wordlist, different tool, different approach)
- "Systematic is enough" → systematic finds the floor, creativity finds the ceiling

## EXECUTION ORDER
When this skill triggers:
1. Send the request the client's body and the server's sentence already name.
2. If the class is still the author's, loosen one axis from the palette below.
3. Read the new class. A later class on the same status is the skipped check.
4. Chain the floor to the ceiling in the same pass.
5. The checklist above is a palette. It does not run before the request.
6. PERSIST the class ladder.

================================================================================
                    METHOS ENGINE — INSTALL AND ACTIVATE
================================================================================

This is not an optional skill. This is the upgrade from systematic to
adaptive, from floor-finding to ceiling-seeking. Every target gets this
treatment. A barrier is a class, not a count. Every finding gets chained.

The difference between a $500 bug and a $10,000 bug is often just one
more angle tried.
