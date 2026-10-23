---
name: elite_mindset_engine
description: The mental models of elite hackers — distilled from Google Project Zero, top bug bounty hunters, and 0day researchers. This is not a checklist or a payload list. It is a way of thinking that generates novel attacks. When you feel stuck, read this. When you want to find what nobody else found, follow this. This overrides systematic approaches with creative, adversarial, hypothesis-driven hacking.
---

# ELITE MINDSET ENGINE — How the Best Hackers Actually Think

## SOURCE: Research from Google Project Zero, Anthropic 0day research, Assetnote,
## ZeroPath, BugCrowd top hunters, and elite bug bounty writeups.
## This is NOT a payload list. It is a THINKING SYSTEM.

## PRINCIPLE 0: THE ELITE HACKER IS A SCIENTIST, NOT A SCRIPT-KIDDIE

The best hackers don't run scanners. They form hypotheses, design experiments,
observe results, and iterate. Every probe is a question. Every response is data.
The goal is not to find a bug — the goal is to UNDERSTAND THE SYSTEM so deeply
that bugs become obvious.

---

## MENTAL MODEL 1: THE COMMIT-HISTORY ORACLE

**From: Anthropic's Claude 0day research, Project Zero**

Elite hackers read git commit history like archaeologists read strata. Every
security-related commit is a signal that says "we found a bug here." The
question is not "was this fixed?" — the question is "was it fixed COMPLETELY?"

**How to apply:**
1. Find the target's open-source repos (or deps)
2. Search commits for: `security`, `fix`, `CVE`, `vulnerability`, `bounds`, `sanitize`, `escape`, `encode`
3. For each security commit: read the diff. Understand WHAT was fixed and WHY.
4. Ask: "Did they fix ALL call sites?" "Did they fix edge cases?" "What about similar code elsewhere?"
5. The fix pattern reveals the vulnerability class. Now hunt for the SAME PATTERN in unpatched code.

**Example:**
- GhostScript: commit added "stack bounds checking for MM blend values"
- Claude found the SAME function was called elsewhere WITHOUT the check
- That unpatched call site → 0day

---

## MENTAL MODEL 2: THE SHADOW EXPOSURE HUNTER

**From: Assetnote (Shubs), top bug bounty hunters**

The best bugs live in the shadows — not the main app, but the things attached
to it. The ServiceNow instance nobody audits. The partner portal with its own
auth. The acquired company's old stack still running. The third-party SaaS app
on a subdomain.

**How to apply:**
1. Map the target's vendor ecosystem — what third-party products do they use?
2. Find shadow apps: `vendor.target.com`, `target.vendor.com`, `app.target.com`
3. Check if the third-party app has its OWN auth, its OWN admin panel, its OWN API
4. Read the third-party app's source code (if open-source) — find systemic issues
5. Ask: "Does the target configure this securely? Or do they use defaults?"

**The Assetnote principle:** "Everyone knew they had ServiceNow. No one knew
how insecure it was configured."

---

## MENTAL MODEL 3: THE ABSTRACTION VIOLATOR

**From: Project Zero, elite CTF players**

Systems work because layers are separate. Attack them by VIOLATING the
abstraction. Send a database query through a file upload. Send a JWT through
a query parameter. Send a GraphQL query through a REST endpoint. The system
wasn't designed to handle this — that's where bugs live.

**How to apply:**
1. Map the target's architecture layers (client → CDN → WAF → API → service → DB)
2. For each layer boundary: "What does this layer ASSUME about the previous?"
3. Violate every assumption:
   - WAF assumes valid HTTP → send malformed HTTP/2 frames
   - API assumes JSON body → send XML, protobuf, or multipart
   - Service assumes valid JWT → send empty JWT, nested JWT, or JWT in Cookie
   - DB assumes parameterized queries → send JSON operators in string fields
4. The violation that produces an UNEXPECTED response → vulnerability

---

## MENTAL MODEL 4: THE STATE CORRUPTOR

**From: Project Zero, business logic bug hunters**

Find state the target relies on. Corrupt it. The target's assumptions about
state consistency are its weakness. A negative count. A future timestamp.
A half-completed transaction. A deleted object still referenced.

**How to apply:**
1. Map all state transitions: create → update → delete, login → session → logout
2. For each state: "What happens if I skip a step?" "What happens if I repeat a step?"
3. Corrupt state:
   - Delete an object, then reference it
   - Set a negative quantity
   - Send a timestamp in the future
   - Complete step 3 before step 1
   - Race two simultaneous state changes
4. The state that produces an INCONSISTENT response → vulnerability

**Key question:** "What does the system assume is always true about this state?"
Then make it false.

---

## MENTAL MODEL 5: THE SIDE-CHANNEL ORACLE BUILDER

**From: Project Zero (Tavis Ormandy, Ian Beer), timing attack researchers**

Even when you can't exploit directly, you can MEASURE. Response time per
character. Error message per input. Cache hit vs miss. These measurements build
an ORACLE that leaks information. From the oracle, you can extract data,
enumerate users, or bypass checks.

**How to apply:**
1. For every endpoint: measure response time for valid vs invalid input
2. For every error: does the error message differ based on WHY it failed?
3. For every auth check: does a valid user take a different time than invalid?
4. Build the oracle:
   - Timing: `time(correct_char) < time(incorrect_char)` → character-by-character extraction
   - Error differential: `error(user_exists) != error(user_not_exists)` → user enumeration
   - Cache behavior: `cache_hit(valid) != cache_miss(invalid)` → validation bypass
5. From the oracle: extract secrets, enumerate IDs, bypass rate limits

**Project Zero principle:** "Even a 1-nanosecond difference is exploitable
with enough samples."

---

## MENTAL MODEL 6: THE DODGIEST-PERSON-YOU-KNOW

**From: Pentesterlab, BugCrowd top hunters**

Think like the most cunning, rule-bending person you've ever met. What would
they do? How would they abuse this feature? What legitimate feature can be
used in a completely illegitimate way?

**How to apply:**
1. For every feature: "How would a scammer use this?"
2. For every workflow: "Where's the weakest trust assumption?"
3. For every validation: "What if I just... don't do that?"
4. Abuse legitimate features:
   - Referral program → self-referral loop
   - Password reset → reset MY password, then use the token on YOUR account
   - File upload → upload HTML instead of image, get XSS
   - Search → search for `{{7*7}}`, find SSTI
   - Contact form → send to internal email, phishing
5. The feature interaction nobody designed for → vulnerability

---

## MENTAL MODEL 7: THE INVERSION ATTACK

**From: Project Zero, elite red teamers**

Instead of attacking the system, BE the system. What would the server do
if it received X? Now send X+epsilon. Invert the flow:
- Server sends a redirect → client follows it. What if the redirect is malicious?
- Server sends a token → client uses it. What if the token is forged?
- Server validates input → what if YOU validate the server's output?

**How to apply:**
1. For every server→client response: "Can I influence this?"
2. For every client→server request: "What if the server is wrong?"
3. Invert roles:
   - Be the OAuth provider (forge tokens)
   - Be the webhook sender (send fake callbacks)
   - Be the CDN (serve malicious content)
   - Be the DNS server (redirect to attacker IP)
4. The inverted role that the target accepts → vulnerability

---

## MENTAL MODEL 8: THE DEPENDENCY ARCHAEOLOGIST

**From: ZeroPath, Snyk, dependency confusion researchers**

Modern apps are 90% dependencies. Every dependency is code you didn't write
that runs with your privileges. Old dependencies have known CVEs. New
dependencies have unknown CVEs. The dependency tree is a goldmine.

**How to apply:**
1. Map EVERY dependency: direct + transitive, frontend + backend
2. Check versions against CVE databases
3. Read the dependency's source — find undocumented behavior
4. Check for: eval(), Function(), child_process, exec(), deserialization
5. Check for: prototype pollution sinks, XSS sinks, path traversal
6. Dependency confusion: can you publish a higher-version package with the same name?
7. The dependency that does something surprising → vulnerability

---

## MENTAL MODEL 9: THE PROTOCOL CONFUSER

**From: Project Zero, HTTP request smuggling researchers**

Modern systems speak multiple protocols: HTTP/1.1, HTTP/2, WebSocket, gRPC,
GraphQL, REST. Each protocol layer has its own parser. Parser differentials
→ protocol confusion → security bypass.

**How to apply:**
1. Test the same request through different protocols:
   - HTTP/1.1 vs HTTP/2 (H2C smuggling, :authority vs Host)
   - REST vs GraphQL (query depth, introspection, batching)
   - HTTP vs WebSocket (CSRF via WebSocket, no origin check)
   - gRPC vs REST (protobuf → JSON conversion quirks)
2. Look for protocol conversion points (gateway, load balancer, reverse proxy)
3. The parser that interprets the request differently → vulnerability

---

## MENTAL MODEL 10: THE HYPOTHESIS-DRIVEN HACKER

**From: Anthropic 0day research, BugCrowd top hunters**

The best hackers are scientists. They form hypotheses, test them, observe
results, and iterate. They don't guess — they experiment.

**The scientific method applied to hacking:**
1. **OBSERVE**: "The target uses PROGRAM_10 for auth and has a custom JWT validation"
2. **HYPOTHESIZE**: "The custom JWT validation might not check alg correctly"
3. **PREDICT**: "If I change alg from RS256 to HS256, validation might pass"
4. **EXPERIMENT**: Send the forged JWT, observe the response
5. **ANALYZE**: Did it pass? Why or why not? What does the response teach?
6. **ITERATE**: Form a new hypothesis based on what you learned

**Every probe must answer a specific question.** Not "let me try XSS."
But: "If the template engine is Jinja2, and I send `{{7*7}}`, will it
execute? And if not, does the error message reveal the engine type?"

---

## THE ELITE EXECUTION PROTOCOL

When approaching ANY target:

### Step 1: DEEP ARCHAEOLOGY (30 minutes minimum)
- Read git history for security commits
- Map all dependencies and their versions
- Read the source code of the most critical 3 files
- Understand the auth flow completely
- Find the "weird" parts — unusual constants, TODOs, deprecated features

### Step 2: HYPOTHESIS GENERATION (10 novel hypotheses)
- Generate 10 specific, testable hypotheses about vulnerabilities
- At least 3 must target areas others dismissed as "secure" or "not applicable"
- Each hypothesis must include: what you expect, how you'll test, what success looks like

### Step 3: RAPID EXPERIMENTATION
- Test each hypothesis with a minimal probe
- Record: hypothesis, probe, result, what was learned
- For partial successes: generate 3 follow-up hypotheses immediately
- For failures: analyze what the failure teaches about defenses

### Step 4: DEEP DIVE ON PROMISING LEADS
- For any confirmed behavior: reverse engineer the exact code path
- Build a custom tool if needed (don't rely on scanners)
- Chain with other findings
- Build a proof-of-concept, not just a theory

### Step 5: REPORT AT THE CEILING
- File the maximum proven impact, not the minimum
- Include: the hypothesis, the experiment, the chain, the PoC
- Document what you tried that DIDN'T work (shows thoroughness)

---

## THE CREATIVE SPARK TRIGGERS

When you're stuck, ask these questions:

1. "What would the DODGIEST person I know do with this feature?"
2. "What assumption is the system making that I can make FALSE?"
3. "What did the LAST security fix miss?"
4. "What happens if I use this feature COMPLETELY WRONG?"
5. "What would a LAZY developer have done here?"
6. "What parser is involved, and how does it handle WEIRD input?"
7. "What state does this rely on, and how can I CORRUPT it?"
8. "What protocol conversion happens, and do the parsers AGREE?"
9. "What dependency is doing the heavy lifting, and is it SECURE?"
10. "If I were building this, where would I CUT CORNERS?"

---

## THE ANTI-PATTERNS (what elite hackers NEVER do)

- NEVER run a scanner and call it a day
- NEVER try the same payload on every target
- NEVER accept "WAF blocked me" as final
- NEVER stop at the first "no"
- NEVER file a report without a PoC
- NEVER assume the main app is where the bugs are
- NEVER ignore error messages (they're oracles)
- NEVER test without a hypothesis
- NEVER skip reading the source code
- NEVER forget that the best bug is the one nobody else thought to look for

---

## THE ULTIMATE PRINCIPLE

**The system was built by humans. Humans make assumptions. Assumptions are
bugs waiting to be found. Your job is to find the assumption and break it.**

Not with a checklist. Not with a scanner. With understanding, creativity,
and relentless experimentation.

Think like the dodgiest person you know.
Act like a scientist.
Hack like your life depends on it.
