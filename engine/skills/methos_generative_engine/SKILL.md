---
name: methos_generative_engine
description: The generative adaptive attack engine. Not a checklist — a creative force. Deeply reverse-engineer the target's architecture, then INVENT attacks nobody else thought of. When all known angles fail, that is when the real work begins. Override for MYTHOS/METHOS v1.
---

# METHOS GENERATIVE ENGINE — Creative Attack Force

## OVERRIDE (2026-09-29 — this beats the five steps below)
Do not write eight architecture questions, then invent ten attacks, then execute them.
The server's error class is the architecture. Replay the real client, send the one input
that class forbids, and read the new class. Same status, later class = the check between
them was skipped. Escalate that in this pass. The loop below is what you open when the
class has stopped moving. At least 7 shots on the angle, each a different axis. File the
proven floor and keep driving the ceiling — do not claim a ceiling you have not stood on.
Solo. Do not ask the user.

## WHERE THIS SKILL SITS (routing — read first)
This is the **DRIVER** — the primary creative loop for any target/finding/barrier. It runs the
hunt and pulls the others in as resources:
- **`methos_engine`** = the 80-angle breadth palette · **`methos_full_vuln_engine`** = the deep 2026 payload library → primitives + payloads to recombine in STEP 2.
- **`zero_day_mindset`** = barrier-bypass ladders → call it when STEP 3 hits a specific wall.
- **`differential_oracle`** = the instrument → call it the moment STEP 3 returns a surprising,
  null, or "blocked" result, before you believe it (and to read what hides behind a status code).
If you're unsure which hunting skill to use, use THIS one; it dispatches the others.

## THE CORE INSIGHT (why v1 failed)
METHOS v1 had 80 angles in a matrix. Claude tried 7 and stopped. Why?
Because running a checklist is not creativity. A real 0day researcher doesn't
follow a matrix — they develop DEEP INTUITION about the target and then think
of things the matrix never included.

This engine forces that intuition. It replaces the checklist with a creative
process that generates novel attacks based on architectural understanding.

## THE GENERATIVE LOOP (this is the engine)

### STEP 1: ARCHITECTURAL DECONSTRUCTION (not surface scanning)
Don't enumerate endpoints. Don't grep for patterns. **Understand how the
target THINKS.**

For the target, answer these questions IN WRITING (persistence is mandatory):

1. **What is this app's CORE JOB?** (courier matching? ride bidding? payment
   processing? document verification?) — the core job is where the money is

2. **What does the client TRUST from the server?** (JWT? cookie? config?
   price values? validation rules? signature keys?) — every trust is an attack

3. **What does the server TRUST from the client?** (price? user ID? role?
   validation result? uploaded file metadata? CORS origin?) — every trust is
   an attack

4. **Where does MONEY or IDENTITY flow?** (payment create, price set, bid
   accept, order complete, token mint, session create) — follow the money

5. **What is the WEAKEST seam?** (where two systems touch: client↔API,
   API↔gateway, gateway↔backend, backend↔database, service↔service) — seams
   are where bugs live

6. **What is the target FORCED to do?** (reCAPTCHA before auth? OTP via SMS?
   file upload for KYC? real-time WebSocket for chat?) — forced operations
   are complex and complexity breeds bugs

7. **What is UNUSUAL about this architecture?** (why does intercity have its
   OWN auth instead of shared CAS? why is there a KYC document checker host?
   why does the client get price min/max from server but validate client-side?
   — unusual = under-tested = bugs)

8. **What would BREAK this app in the most SURPRISING way?** (not the
   obvious SQL injection or XSS — what would nobody expect? a pricing bug
   that pays drivers negative amounts? a KYC bypass that approves fake IDs?
   a chat injection that impersonates support?)

### STEP 2: ATTACK GENERATION (the creative force)
Based on your architectural understanding, generate 10 NOVEL attacks that
are SPECIFIC to this target's unique architecture. Not generic SQL injection.
Not "try XSS." Attacks that ONLY work because of how THIS target is built.

For each attack:
- Name it (one sentence)
- Why it works (architectural reason)
- How to test it (specific probe)
- What success looks like
- What the target's defense probably is

MANDATORY: At least 3 of the 10 attacks must exploit something the prior
analysis called "DISPROVEN", "BLOCKED", or "not a vulnerability." This is
where creativity lives — the things everyone else dismissed.

#### HOW to generate novel attacks (recombination — novelty is a method, not luck)
Novelty is not "think harder." It is **(architectural fact from STEP 1) × (primitive) →
candidate attack nobody wrote down.** Cross every STEP-1 fact against the primitives below;
the surprising cells are your 10. (Today's cross-product confused-deputy came from exactly
this: STEP-1 fact "one CAS issuer signs all products" × primitive "cross-context replay" →
"replay a courier token at the rider gateway" → proven.)

**The recombination grid — for each STEP-1 fact, ask each primitive:**
- **Cross-context replay** — take a credential/id/token/signature valid HERE and present it
  THERE (other product, vertical, region, tenant, role, environment). What still accepts it?
- **Trust-edge substitution** — at a seam (client↔BFF↔gateway↔backend), swap what one side
  assumes the other validated (audience, ownership, price, role, recaptcha-result, file-type).
- **Identity/scope confusion** — the field that scopes a token to a thing (aud, iss, kid, tenant
  id, project id) — does every consumer enforce it the SAME way? Map per-endpoint.
- **Deputy redirection** — a server that fetches/forwards on your behalf (BFF, image optimizer,
  webhook, importer, renderer): can you steer its target or smuggle your input into its upstream?
- **State/representation mutation** — send the value in a form the validator didn't expect
  (string-vs-number, array-vs-scalar, negative, overflow, future-date, half a token, null).
- **Forced-operation abuse** — the thing the app MUST do (OTP, recaptcha, KYC upload, realtime
  socket): complexity → fail-open, race, replay, or skip.
- **Disabled/leftover surface** — a key/route/flag/field that exists but "isn't used" by the
  client (server-only secret in client config, dev fixture in prod, declared-not-enforced policy).
- **Asymmetry** — two paths to the same resource (BFF vs direct gateway, v1 vs v2, mobile vs web,
  GET vs POST): they rarely validate identically — diff them.

For each surprising cell write the 5-field attack (name / why / probe / success / likely defense).
If a cell is "DISPROVEN", that's a MANDATORY pick — re-attack it with a *different* primitive than
the one that disproved it (the disproof tells you which primitive the defense expects).

### STEP 3: EXECUTE AND ADAPT
Run the 10 generated attacks. For each result:
- Success → chain it, escalate it, file it
- Partial success → what did you learn? generate 3 follow-up attacks
- Failure → what did the failure teach you about the target's defense?
  use that knowledge to generate a bypass attack
- Confusing result → instrument validation, then reinterpret

The rule: **every result generates at least one new attack.** Never end a
probe without a follow-up angle.

### STEP 4: THE BREAKTHROUGH PROTOCOL (when nothing works)
When all 10 attacks fail, do NOT stop. This is when the real work begins.

Execute this protocol IN ORDER:

1. **Re-read the code with fresh eyes** — look for the ONE line that
   doesn't make sense. The weird constant. The unusual function call.
   The comment that says "TODO: fix this."

2. **Inversion attack** — instead of attacking the system, BE the system.
   What would the server do if it received X? Now send X+epsilon. What
   would the client do if it received Y? Now craft malicious Y.

3. **Abstraction violation** — find where the target assumes layers are
   separate. Send a database query through a file upload. Send a JWT
   through a query parameter. Send a GraphQL query through a REST endpoint.
   Violate the abstraction boundary.

4. **Feature interaction** — find two features that were never meant to
   interact. Enable both simultaneously. Chat + file upload. Payment +
   referral. OAuth + anonymous access. Features interact in surprising ways.

5. **State corruption** — find state that the target relies on. Corrupt it.
   Delete half a JWT. Send a price as a string instead of number. Set a
   negative count. Send a future timestamp. Corrupted state reveals
   assumptions.

6. **Side channel** — measure everything. Response time per character.
   Error message per input. Cache hit vs miss. The target leaks information
   through timing, errors, cache behavior, and differential responses.
   Build an oracle from the side channel.

7. **Third-party dependency** — what libraries does the target use? What
   versions? What CVEs? What undocumented behaviors? Every dependency is
   a potential entry point.

8. **Configuration archaeology** — what config values exist? What do they
   control? What happens if you change them? Feature flags. Debug modes.
   Test endpoints. The config reveals what the developers thought about.

9. **Protocol confusion** — does the target accept multiple protocols?
   HTTP/1.1 vs HTTP/2. WebSocket vs HTTP. gRPC vs REST. GraphQL vs REST.
   Each protocol may validate differently.

10. **The "what if everyone is wrong" attack** — what if the accepted
    wisdom about this target is wrong? What if the 403 isn't really RBAC?
    What if the JWT validation isn't really JWT validation? What if the
    price validation is client-side everywhere? Test the fundamental
    assumptions.

### STEP 5: CHAIN OR FILE
For every confirmed finding, build the chain:
- What else does this give me access to?
- What other finding does this combine with?
- What is the maximum impact I can prove?

Then file at the proven ceiling, not the floor.

## THE CREATIVE MANDATES (non-negotiable)

1. **NEVER run a checklist** — generate attacks from understanding
2. **NEVER accept DISPROVEN at face value** — the disproof is data for a new attack
3. **NEVER stop at 10 attacks** — every result generates a follow-up
4. **ALWAYS ask "what would surprise me?"** — surprising = under-tested = bug
5. **ALWAYS exploit the target's unique architecture** — generic attacks find generic bugs
6. **ALWAYS follow the money** — payment, identity, KYC, admin = highest impact
7. **ALWAYS violate assumptions** — the target assumes X; test what happens when X is false
8. **THE BARRIER IS NEVER THE END** — it is the beginning of understanding the defense
9. **IF YOU HAVEN'T SURPRISED YOURSELF, YOU HAVEN'T TRIED**
10. **MYTHOS DISCIPLINES THE REPORT — METHOS DESTROYS THE TARGET**

## EXECUTION ORDER
1. Architectural deconstruction (8 questions — IN WRITING)
2. Generate 10 novel attacks (at least 3 from "DISPROVEN" areas)
3. Execute all 10, adapt based on results
4. If all fail → breakthrough protocol (10 more angles)
5. Chain findings, file at ceiling
6. PERSIST everything — especially the failed attacks (they teach)

## ANTI-PATTERNS DESTROYED
- "I ran the matrix and found nothing" → the matrix was wrong, generate new attacks
- "DISPROVEN means stop" → DISPROVEN means "try a different approach"
- "I understand the architecture" → you understand until you probe
- "The barrier is the end" → the barrier is the beginning
- "Systematic is enough" → systematic finds the floor, creativity finds the 0day
- "I already checked that" → check it differently
- "That doesn't make sense as an attack" → exactly — nobody else tried it
