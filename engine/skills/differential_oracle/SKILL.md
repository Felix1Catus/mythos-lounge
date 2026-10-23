---
name: differential_oracle
description: Build truth from differentials — decide whether a boundary/blocker/null result is REAL or an instrument artifact, and turn response differences into an exploitable oracle. Use the instant you're about to believe a status code, a "blocked", a "clean/nothing-found", or any surprising/null result. This is the instrument-validation + control-discriminator engine that separates real defenses from your own broken probe.
---

# differential_oracle — make the response prove it, not the status line

## WHERE THIS SKILL SITS (routing)
The **instrument** layer of the hunt. The other engines GENERATE attacks; this one
DECIDES whether a result is real and EXTRACTS signal from differences:
- `methos_generative_engine` (driver) generates novel attacks → when one returns a
  surprising/null/blocking result, **fire this** before believing it.
- `zero_day_mindset` (barriers) says "403 ≠ final" → this tells you *whether the 403 is
  even a real defense* and *what response class hides behind it*.
- `self_audit` Q3 ("did I validate my instrument?") → this is the HOW.

## TRIGGER (fire the moment any of these is true)
- You're about to write/believe a state claim from a **status code** ("403 = blocked",
  "401 = auth works", "200 = vuln").
- A result is **surprising, null, uniform-blank, or exciting** ("nothing found",
  "all blocked", "every key invalid", "it's geo-walled").
- You want to know if a boundary is a **real defense or your own probe** (wrong UA, bad
  regex, truncated payload, stale cache, wrong host).
- You have two responses that *look* the same (or different) and need to know if the
  difference is **semantic** or **noise**.
- You want to turn a behavior into an **oracle** (existence, validity, ownership, role).

## THE CORE LAW
**The boundary is in the RESPONSE BODY and its CLASS, never in the status line.**
Different status codes can wrap identical semantics; identical status codes can wrap
distinguishable classes. Closing a probe on the status code alone is theory-closure.

## STAGE FLIP — if you already have this, stop the procedure and use it
Two identical HTTP statuses with different error codes are two internal stages.
Positive-control the canonical blocked input first (`policy_violation`). Then one
structural variant (case, encoding, type, sibling key). If the variant's class is later
in the pipeline (`invalid_data` / `Insufficient balance` after `policy_violation`), the
check between them did not fire. That flip is the proof. You do not need the side effect
to show the skip. Do not walk the six steps below before believing a flip you already hold.
The six steps are for when you do not yet have two classes.

## METHOD — 6 steps (only when the class has not flipped yet)

### 1. ESTABLISH THE BASELINE
Capture the *known* points before varying anything:
- a **known-NEGATIVE** (what a refusal looks like: no token / wrong value / nonexistent id)
- a **known-POSITIVE** (what success looks like — your own valid token/id/resource)
If you don't have a known-positive, **get one or plant one** before trusting any null.

### 2. VARY EXACTLY ONE THING
Hold everything constant; change a single variable (the audience claim, the id, the UA,
one header, one byte). A differential is only interpretable if one variable moved.

### 3. CLASSIFY BY RESPONSE CLASS, NOT CODE
Record for every response: status, **body fingerprint** (exact string / hash), length,
content-type, timing, redirect target, key headers. Bucket into *semantic classes*:
- e.g. `AUD-REJECT` ("Audiences not allowed") vs `SIG-REJECT` ("verification fails") vs
  `EXPIRED` ("Jwt is expired") vs `MESH-DROP` ("RBAC: access denied") — four different
  truths that могут all be HTTP 401/403. The class is the signal.

### 4. BUILD THE DISCRIMINATOR (the control that splits the hypothesis)
Design the input whose two outcomes mean two different things:
- **garbage-vs-real:** if `aud=garbage → "not allowed"` but `aud=courier → "Invalid auth
  token"`, courier PROVABLY passed the audience gate (the split is the proof).
- **exists-vs-not:** if `id=real → slow/200-shape` and `id=fake → fast/404-shape`, you
  have an existence oracle.
- **control arm:** for any timing/differential anomaly, add an arm that SHOULD reproduce
  it if it's a confound. If the control reproduces the "anomaly" → it's noise → NEGATIVE.

### 5. VALIDATE THE INSTRUMENT AGAINST THE KNOWN-POSITIVE  ← the step everyone skips
Before trusting a **null** ("nothing found") or a **surprise** ("all blocked"):
- run the SAME instrument against the known-positive. If it doesn't light up on a thing
  you KNOW is there, the instrument is broken — fix it, re-run, THEN verdict.
- uniform-blank / uniform-fail across a whole sweep = **suspect the instrument first**
  (wrong UA → CloudFront 403; kty-anchored regex → misses an alphabetised JWK; `#` in a
  data: URL → truncated payload; stale body in /tmp → misread).

### 6. CONFOUND CONTROL → VERDICT
Name the specific confound that could explain the result; design the arm that isolates
it; run it. Only after the confound is killed do you render REAL / NEGATIVE / ORACLE.
Disclose near-misses ("I almost recorded a false positive — [confound]").

## DIFFERENTIAL TYPES (the palette)
| type | vary | the oracle it builds |
|---|---|---|
| **content-differential** | input value | semantic class hides behind same code (auth/ownership boundary) |
| **stage-differential** | token validity stage (aud/sig/exp) | WHERE in the pipeline rejection fires → how deep you penetrate |
| **existence/timing** | real vs fake id | enumeration oracle (user/resource exists) |
| **error-differential** | failure mode | user-enum / validity oracle from distinct error strings |
| **control-discriminator** | real vs garbage | proves a specific gate was passed (not a generic reject) |
| **instrument-control** | your probe vs a known-positive | proves your tool works before you trust a null |
| **cache/ETag** | repeat / vary key | cache-poisoning / deception reachability |

## WORKED EXAMPLE (real, this workspace)
intercity ic3-gw: `aud=intercity → "Audiences not allowed"` but `aud=courier → "Jwt
verification fails"` and `aud=garbage → "Audiences not allowed"`. The garbage-vs-courier
split (step 4) PROVED courier passes the audience gate — a cross-product confused-deputy —
where status code alone (all 401/403) said nothing. Earlier the same session: bare-UA →
CloudFront 403 looked like a geo-wall; the instrument-control (browser-UA → 200, step 5)
proved it was MY probe, not a target defense. Both verdicts came from differentials, not codes.

## ANTI-PATTERNS THIS KILLS
- "403, so it's blocked" / "200, so it's vuln" — status-code closure.
- Trusting "nothing found" from a sweep you never ran against a known-positive.
- Recording a timing/differential win without a confound-control arm.
- Optimistic-first parsing (seeing the win you want); re-read conservatively.
- "Those two responses are the same" — without hashing the bodies.

## OUTPUT (persist)
A small matrix: variable × response-class, the discriminator that split it, the
instrument-validation result, the confound you killed, and the one-line verdict
(REAL boundary / instrument-artifact / ORACLE built). Cross-ref into RESUME/notes.
