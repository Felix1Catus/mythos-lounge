---
name: chain_completer
description: Take a finding that is "confirmed but not weaponized" (a controllable input, a wrong-looking behavior, a partial auth bypass) and drive it to proven end-to-end impact. Use when you found a thing but haven't proven impact, or catch yourself saying "that needs a session, skip it."
---

# chain_completer — turn a primitive into proven impact

## Trigger
Any finding that is confirmed but NOT weaponized: you control an input, you see a behavior that looks wrong, or you have a partial auth bypass — but impact is not proven end-to-end. Also fires the instant you think "I found a thing but didn't chase it" or "that needs a session, skip it."

## Why this finds P1s
A proven primitive with unproven impact is a P4 write-up and a triager rejection ("channel-reachable ≠ exploited"). The same primitive, chained one link further to a confidentiality/integrity/financial effect, is the P1. The gap between them is usually ONE probe you talked yourself out of running.

## Methodology
For EACH unconnected chain on the current target:
1. **LIST proven links** — each with its evidence path (script + output on disk). Be concrete: "DNS resolves from Google IP — `attack/x.sh` output".
2. **LIST unproven links** — each with the SPECIFIC blocker, not a vague "hard".
3. **CLASSIFY each unproven link:** `PROBE-ABLE now` / `SESSION-GATED` / `RESOURCE-BLOCKED`.
4. **PROBE-ABLE → execute immediately.** Do not defer. The whole point is the link you can run right now and keep skipping.
5. **SESSION-GATED → enumerate the EXACT unlock conditions** (which session, how obtained, what it then unlocks). No vague-out. A precise unlock list is itself the deliverable.
6. **RESOURCE-BLOCKED → `[STATUS: BLOCKED]` with the reason** (geo-egress, 2nd account, carrier filter). Never dress a blocker as a negative.
7. **Fan out the generalization.** If a primitive worked once, test whether it generalizes (other hosts, other params, other verticals) BEFORE concluding "scoped/RBAC-gated" — that conclusion from a single test is the recurring miss.

## Common P1 chain templates (web apps)
- Unauth file read → enumerate the id/window → pull the *target's* files → sensitive PII (ID/face/KYC).
- OTP/captcha fail-open → CAS/session token → WebSocket subscribe → cross-user event stream.
- Leaked API key → fan across the gateway mesh → content-differential per host (with vs without key) → which host *honors* it.
- Client-controlled header (x-city-id / x-tenant) → confused deputy → cross-tenant data read.
- Client-side price floor → is it server-enforced? → price manipulation (hand to `business_logic_breaker`).
- File upload → content-type bypass → stored XSS → admin panel.
- Leaked private key → reproduces a real prod signature → forge the anti-abuse header → unauth abuse at scale.

## Anti-patterns prevented
- "I found a thing but didn't chase it." → Every finding gets chained to a proven impact or an explicit blocker.
- "That needs a session, skip it." → Enumerate the EXACT unlock; never vague-out a SESSION-GATED link.
- "I assumed it doesn't generalize." → Fan out and test; one negative test is not a generalization.
- Reporting the primitive as the finding (config-only / channel-reachable) → triager quotes it back as the rejection.
- Theory-closing a link you could actually probe right now.

## Evidence references (verified on disk)
- `~/targets/PROGRAM_42/STATE/GAP_PLAN_2026-06-17.md` — `## CHAINS` (line 135); A3 (line 47) cargo `X-Api-Key` fan-out across the 210-host mesh tested against too few upstreams; B1 (line 114) `x-city-id` cross-tenant reads — "mechanism proven, exploit never run" (died with the session); router registry → sensitive backends never path-probed.
- `~/targets/PROGRAM_42/STATE/RESUME.md` — report-04 chain: leaked RSA key → reproduces real prod x-signature → forge unauth SMS (PROBE-ABLE link completed); report-03 OTP fail-open → CAS token → (session-gated) WS subscribe.
- `~/targets/PROGRAM_42/notes/secret_resweep_2026-06-17_PM.md` — example of fanning a primitive across all bundles/hosts before concluding negative.
> NOTE: the elevation brief cited progress.txt lines 129-147/133-137; that 530-line session log has no such lines — verified source is GAP_PLAN_2026-06-17.md §CHAINS + B1/A3 as above.
