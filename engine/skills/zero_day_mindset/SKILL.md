---
name: zero_day_mindset
description: The creative attacker mindset — reverse-engineer the target, try hundreds of angles, never accept a barrier at face value. When something is "blocked" or "disproven", this is where the real work begins. Use when you feel like stopping, when the finding feels "complete", or when you hear yourself say "DISPROVEN", "BLOCKED", or "can't".
---

# zero_day_mindset — the creative attacker

## OVERRIDE (2026-09-29 — this beats the phases below)
If two responses to the same call share an HTTP status and differ in error class, that flip
is the crack. Canonical refusal first. Escalate the skipped stage. Do not list ten angles
before using a flip you already hold. The ladders below are the palette for when the class
does not move. If the client's body and the server's sentence already name the crack, send
that one request. Do not pad it to seven. Seven axes apply only while the class is still
the one the author expected. Loosen one axis. Do not ask the user. Solo.

## WHERE THIS SKILL SITS (routing — read first)
This is the **barrier-bypass LIBRARY**: concrete escalation ladders for a *specific wall you
already hit* (403/RBAC, JWT/alg-mismatch, auth-gate, crypto-key-with-no-obvious-use). Fire it
when you're stuck at one barrier and the class has not moved and one loosened axis is the next request.
- **Driver = `methos_generative_engine`**: runs the whole hunt; calls into this when it hits a wall.
- **Breadth palette = `methos_engine`**: the 80-angle library to recombine from.
- **Instrument = `differential_oracle`**: before you trust that the barrier is REAL (not your own
  broken probe) and to read WHAT response-class hides behind the 403 — pair it with this skill.
Rule of thumb: `differential_oracle` tells you *whether* the wall is real and what's behind it;
*this* skill gives you the ladder to climb *over* it.

## Trigger
- You just declared something DISPROVEN or BLOCKED
- You found a finding and are about to move on (STOP — escalate creatively first)
- You see a barrier (403, RBAC, auth gate, algorithm mismatch)
- The target uses JWT, crypto, auth, file upload, WebSocket, or any complex system
- You feel like the work is "done" (it's never done — there's always another angle)

## Core Principle
**The front door is never the only door. A failed attack is data — adapt and try again.**

Every "NO" teaches you something about the target's defenses. That knowledge is ammunition for the next attack. A 403 tells you there's something worth protecting. An algorithm mismatch tells you there are multiple algorithms in play. A JWT rejection tells you the token parser is live.

## METHODOLOGY: The Relentless Loop

### Phase 1: REVERSE ENGINEER THE TARGET
Palette. Do not run this before the request. The client's bytes and the server's sentence are collected in the same pass as the shot.

1. **Map the architecture from client code:**
   - What libraries are used? (jsonwebtoken? jose? elliptic? node-rsa?)
   - What algorithms are referenced? (even if not the one you expected)
   - What endpoints are called? (not just the ones in the manifest — grep ALL fetch/XHR/axios calls)
   - What auth flow does the client EXPECT? (trace the login → token → refresh → API call chain)

2. **Deconstruct the auth system:**
   - Where does the token live? (localStorage key name, cookie name)
   - How is it attached to requests? (Authorization header? Cookie? X-Token?)
   - What does the client do on 401? (refresh? redirect? retry?)
   - Is there a refresh endpoint? What does it expect?

3. **Find the seams:**
   - Where do two systems touch? (client ↔ API, API ↔ gateway, gateway ↔ backend)
   - Where do different verticals share infrastructure?
   - What config values control behavior? (feature flags, API hosts, version flags)

### Phase 2: THE BARRIERS ARE THE TARGET
When you hit a barrier, don't retreat — study it:

**403 RBAC / istio-envoy:**
- Try: different HTTP methods (GET → POST → PUT → PATCH → OPTIONS)
- Try: path normalization (/api/v1/orders → /api/v1/orders/ → /api/v1/orders// → /api/v1/orders/.)
- Try: path traversal (/api/v1/orders/../users)
- Try: uppercase/lowercase variants (/API/v1/orders)
- Try: alternative content-types (application/json → text/plain → application/x-www-form-urlencoded)
- Try: adding/removing headers (X-Forwarded-For, X-Original-Host, X-Envoy-Expected-Rq-Timeout-Ms)
- Try: method override (X-HTTP-Method-Override: PUT with POST body)
- Try: huge request body (some WAFs skip body checks on oversized requests)
- Try: chunked transfer encoding

**JWT rejected / algorithm mismatch:**
- Try: alg:none (remove signature, set alg to "none")
- Try: algorithm confusion (sign with RSA private key but set alg to HS256, use pubkey as HMAC secret)
- Try: JWK header injection (embed a public key in the JWT header, sign with its private key)
- Try: kid manipulation (empty kid, null kid, kid from another service, path traversal in kid)
- Try: changing the issuer to match (you saw the error says "Jwt issuer is not configured" — enumerate issuers)
- Try: signing with the leaked key but setting alg to EdDSA anyway (some parsers ignore alg mismatch)
- Try: key ID confusion (if you find a JWKS elsewhere, use its kid with your forged key)
- Try: JWT with empty payload
- Try: nested JWT (JWT inside JWT)
- Try: oversized JWT (some parsers have buffer issues)

**Auth gate / session required:**
- Try: the refresh endpoint without auth (some accept any refresh token)
- Try: guest/anonymous token flows
- Try: social auth (OAuth, Google, PROGRAM_06) — sometimes has weaker validation
- Try: password reset flow (often weaker than login)
- Try: registration flow (create account → get token)
- Try: error responses (sometimes 500 errors leak tokens)
- Try: timing the auth (race condition on token creation)

**Algorithm mismatch (e.g., EdDSA vs RSA):**
- The key doesn't sign THAT token — but what ELSE does it sign?
- Check: TLS client certificates (mTLS between services)
- Check: request signing (AWS SigV4 style? HMAC with derived key?)
- Check: webhook signatures (PROGRAM_87-style signature verification)
- Check: file/object signing (S3 signed URLs, cloud storage)
- Check: inter-service gRPC/Protobuf signing
- Check: GraphQL query signing
- Check: internal API request signing (x-signature pattern like couriers)
- Check: code signing (app updates, firmware)

**Crypto key found but "can't forge tokens":**
- What can you SIGN with it? (JWTs to other services, internal requests)
- What can you DECRYPT with it? (encrypted cookies, session data)
- Can you derive other keys from it? (HKDF, key derivation)
- Can you use it for SSRF? (sign a request to an internal service)
- Can you confuse a parser with it? (RSA key as EdDSA key — some parsers are confused)

### Phase 3: ADAPTATION — THE TRY-EVERYTHING MATRIX
Palette. Pull one row when the class has not moved:

| Angle | Tried? | Result | Next adaptation |
|-------|--------|--------|----------------|
| Direct exploitation | | | |
| Cross-vertical replay | | | |
| Algorithm confusion | | | |
| Header injection | | | |
| Path normalization | | | |
| Parameter pollution | | | |
| Type juggling | | | |
| Race condition | | | |
| SSRF via the finding | | | |
| Information disclosure amplification | | | |
| Denial of service via the finding | | | |
| Chain with another finding | | | |
| Protocol downgrade | | | |
| Encoding bypass (base64url vs base64 vs hex) | | | |
| Size/length manipulation | | | |
| Null byte / Unicode injection | | | |
| JSON parsing quirks | | | |
| XML external entity (if XML involved) | | | |
| GraphQL introspection + mutation | | | |
| WebSocket frame manipulation | | | |
| postMessage origin bypass | | | |
| CORS misconfiguration exploitation | | | |
| Content-Type confusion | | | |
| Cache poisoning via the finding | | | |

### Phase 4: CREATIVE CHAINING
Two findings together are worth more than either alone:

- Private key + internal host config = forge inter-service requests
- reCAPTCHA site key + auth flow = programmatic account creation
- JWT alg:none possibility + refresh endpoint = permanent session
- File upload + path traversal = remote code execution
- Info disclosure + predictable ID = BOLA/BAC
- Error message differential + timing = user enumeration oracle

Always ask: **"What if I combine this finding with..."**

## ANTI-PATTERNS (what this skill prevents)

- "DISPROVEN" after trying ONE method (you tried one angle, not all angles)
- "BLOCKED" after hitting the front door (you didn't check the back door, window, chimney)
- "Algorithm mismatch = dead end" (the key signs SOMETHING — find what)
- "No JWKS = no forgery" (JWKS is one of 15 ways to use a key)
- "Client doesn't use it = server-only" (servers talk to each other — forge server-to-server)
- "Session-gated = skip" (every session gate has a bypass: refresh, guest, OAuth, error leaks)
- "403 = final" (403 is the START of the attack, not the end)
- "I already swept it" (you swept with one tool, one time — sweep with 10 tools, 10 times)

## PALETTE — axes, not a count

The list below is a palette. It does not run before the request. If the client's body and the server's sentence already name the crack, send that one request. A repeated class is missing knowledge until method, host, and scheme share one infra identity gate. These are different axes, not a count you finish first:

1. Direct exploitation (the obvious way)
2. Cross-context (different vertical, different endpoint, different auth context)
3. Algorithm confusion (if crypto involved)
4. Protocol manipulation (headers, encoding, content-type, method)
5. Path manipulation (normalization, traversal, case variation)
6. Timing/race (does order matter? can you race?)
7. Information leakage (does it leak data even if it blocks?)
8. Chain with other findings (combine with something else you found)
9. Reverse the flow (server→client instead of client→server, or vice versa)
10. Abuse legitimate features (use the feature in a way it's not meant to be used)

A repeated class is not finished, and it is not a count. Loosen one axis, or send the request the server sentence already named.

## WHEN TO STOP (the only valid reasons)

1. Method, host, and scheme share one infra identity gate and the error class did not flip
2. You've proven the finding has no viable escalation with the current information
3. The cost of trying more angles exceeds the expected value (time vs. likelihood)
4. You've filed the finding and are moving to the next target

"I tried one thing and it didn't work" is NOT a valid reason to stop.
"The algorithm doesn't match" is NOT a valid reason to stop.
"The prompt said to move on" is NOT a valid reason to stop.

## EXECUTION ORDER

When this skill triggers:
1. State the barrier you hit or the finding you want to escalate
2. Send the request the client's body and the server's sentence already name. Do not list angles first.
3. If the class is still the one the author expected, loosen one axis and read the new class.
4. For each class: what stage did the server just name?
5. On a class flip, chain that skipped check. Floor, ceiling, missing link.
6. Stop only on an infra identity gate with no class flip. Name the next request otherwise.
7. PERSIST the class ladder (the failures teach too)

================================================================================
                    THIS SKILL OVERRIDES THE CAUTION INSTINCT
================================================================================

The existing OS says "don't overclaim." This skill says "don't under-try."
Both are true. The report must be honest — but the exploration must be
relentless. Find everything first, then scope the report honestly.

The difference between a P2 and a P1 is often just one more angle tried.
