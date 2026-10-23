# 3-CRITICALS HUNT RULE — dynamic · PROGRAM_20 · PROGRAM_74
_by: RESEARCHER directive · 2026-10-15 · full autonomy granted (no pings until 3 Criticals)

## Stop rule (the ONLY terminal condition)
Produce **3 NEW Criticals** across {dynamic, PROGRAM_20, PROGRAM_74}. Count only NEW (unfiled) Criticals with report+PoC on disk.

## Target set (PROGRAM_71/PROGRAM_20/dynamic all exhausted → switched out; escape applied)
- dynamic   — EXHAUSTED (vendor PATCHED rawSign: same hash now uninspectable_context_denied, global; D15 digest-bound; D13 broken-feature; evmUserOperation unblind-guessable). SWITCHED -> PROGRAM_89.
- PROGRAM_20  — EXHAUSTED (Lead 9 cross-tenant DISPROVEN: account lookup is project-scoped; Wallet Secret is portal/TEE-only, not API-returned; travelRules session-gated; B1 needs funding). SWITCHED -> PROGRAM_46.
- PROGRAM_74   — NEW (escape-swap). GOAL Critical money/auth/cross-customer/RCE. Bearer l7lmK8 live. AGENT RUNNING.
- PROGRAM_46 — NEW (escape-swap, replaces PROGRAM_20). GOAL Critical RCE/authz/IDOR. Unauth-RCE-on-Core lead. AGENT RUNNING.
- PROGRAM_89 — NEW (escape-swap, replaces dynamic). GOAL Critical mass-data/authz. R1 prior data-leak + chatbot prompt-injection + api.super-id.net. AGENT RUNNING.
- PROGRAM_71     — EXHAUSTED (transact=WAI, listener=OOS, MFA=Medium server-enforced). DROPPED.

## Loop / lantern (unchanged)
hunt -> escalate High->Critical -> chain small findings -> report+PoC -> next lead -> regenerate -> repeat.
Scope+WAI+impact = lantern. Never fabricate. Full autonomy — never stop, never ask, workarounds first.

## Escape
If any of the 3 is genuinely exhausted, switch it for another in-scope program and continue (PROGRAM_71->PROGRAM_74 already done).

## Accounting (0/3 NEW Criticals)
- dynamic:  0 (D15 in flight)
- PROGRAM_20: 0 (Lead 9 in flight)
- PROGRAM_74:  0 (fresh hunt)
