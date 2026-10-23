---
name: business_logic_breaker
description: Attack user-facing state machines (orders, payments, subscriptions, bidding, matching, scoring) for missing-guard business-logic bugs — the kind with direct financial impact. Use when a target has workflows with state transitions, especially price/finance flows where the frontend "enforces" the rule.
---

# business_logic_breaker — break the state machine, not the code

## Trigger
Target has user-facing workflows with state transitions: orders, payments, subscriptions, bidding, matching, scoring, ride/offer negotiation. Every state machine is a candidate business-logic bug — and these often out-impact technical vulns financially.

## Why this finds P1s
Business-logic bugs are invisible to scanners and rare among competitors because they require understanding the *product*. The bug is almost never the feature — it's the MISSING guard between two states the designer never imagined an attacker would chain.

## Methodology
1. **MAP THE STATE MACHINE.**
   - List every state an entity can hold (order: created → accepted → in_progress → completed → cancelled).
   - List every transition between states.
   - For each transition: who/what triggers it? (user, provider, system, timer, webhook).

2. **FIND THE MISSING TRANSITIONS** (the illegal edges the server may not block):
   - Can a completed order be cancelled? → refund-after-completion.
   - Can a cancelled order be re-opened? → resurrection.
   - Can an in-progress order be accepted by a SECOND provider? → double-spend / double-assign.
   - Does price re-validate at EVERY transition, or only at creation?

3. **TEST THE EDGE CASES:**
   - Race conditions: two concurrent requests transitioning the same entity (order double-create, OTP code reuse, concurrent `checkauthcode`, refresh-token concurrent double-spend).
   - Negative flows: skip a required step — does the next step still proceed?
   - Concurrent modification: user edits price while provider accepts.
   - Idempotency: same request twice → same result, or two effects?

4. **PRICE / FINANCE SPECIFIC** (if applicable):
   - Is `price_min`/`price_max` server-enforced or client-side only? (Send below floor / negative / zero / huge.)
   - Can price be modified AFTER matching/acceptance?
   - Are discounts/coupons validated server-side? Stacking? Reuse?
   - Currency conversion handled consistently across endpoints?
   - Can a payment be re-attempted with different parameters (amount/card/currency)?

## How to prove (not just assert)
- Every illegal transition / price manipulation gets a LIVE probe with a content-differential (accepted vs rejected) and the resulting server state read back.
- Race conditions: fire N concurrent requests (own account / authorized) and check for >1 success or inconsistent state. This is a case where bursting past the courtesy rate is justified — the proof REQUIRES concurrency.
- Stay on your own entities/accounts; never mutate another tenant's order. Financial side-effects (real charges/refunds) are human-gated — frame the risk and get explicit OK before executing an irreversible transition.

## Anti-patterns prevented
- "It's just a workflow, not a security issue." → Logic bugs often carry higher financial impact than technical ones.
- "The frontend enforces it." → Frontend enforcement is not enforcement; re-send the request directly.
- "That's a feature, not a bug." → The bug is the MISSING guard, not the feature.
- Concluding "server enforces price" without ever sending a below-floor request.

## Evidence references (verified on disk)
- `~/targets/PROGRAM_42/STATE/GAP_PLAN_2026-06-17.md` — B4 (lines 118-119): orders/create server-side **price-floor** (the core mechanic) is UNVERIFIED — `price_min/max` client-side only, server enforcement untested (blocked by session death); + `payment_method_id` int IDOR + create-time mass-assignment (`price_bad`/`price_floor`/`pay_idor` modules).
- `~/targets/PROGRAM_42/STATE/RESUME.md` — report-03: concurrent `auth_id` validity CONFIRMED (concurrency = N independent mutexes = N× brute throughput) — a race/idempotency finding in the OTP state machine; race_idem (order double-create) staged but never run.
- PROGRAM_42's whole product is a bid/negotiation state machine (rider names a price → driver accepts/counters) — the canonical business-logic target.
> NOTE: the elevation brief cited progress.txt lines 148-153/144; that 530-line session log has no such lines — verified source is GAP_PLAN_2026-06-17.md B4 + RESUME.md report-03 as above.
