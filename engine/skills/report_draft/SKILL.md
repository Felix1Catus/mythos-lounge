---
name: report_draft
description: Draft a bug-bounty report against the LOCKED report-writing rules (inline evidence, no step labels, never pre-concede impact, no under-bar standalone, WAI prefile gate). Use when the user says "draft this" / "file this" / "write it up" for a confirmed finding.
---

# report_draft — engineer-grade report against the LOCKED rules

## Trigger
The user says "draft this", "file this", "write it up", or "report" for a confirmed finding.

## Pre-execution checklist
- [ ] The finding is FULLY EXPLOITED — a live PoC was run and impact observed (not "could/would/if I had creds"). If not: STOP, keep hunting, do not draft.
- [ ] You can name a concrete CONFIDENTIALITY or INTEGRITY impact with evidence. If the strongest honest claim is availability/reliability/"behavior differs" → do NOT file standalone; fold as §X of the parent.
- [ ] Raw evidence is on disk: exact commands, HTTP status+body, SHA256s, sizes, output strings.
- [ ] Bypass/policy/authz reports: ran `bash ~/.claude/mythos/prefile_gate.sh <report.md>` and it is not HOLD. Exit 2 = do not draft-as-fileable. A conceded "ban all X is the only complete control" is WAI. A raw/unnameable primitive (raw-sign, secp256k1, 7702, ALLOW *) is not governed by content clauses by design. Receipt: PROGRAM_95 2026-10-13 P5 (fc15102d, 0e1f2489).

## The 4 LOCKED rules (no exceptions — every program)
1. **Inline evidence for every claim.** The triager verifies every claim WITHOUT opening any attachment. Quote SHA256s, sizes, source lines, exact output, mount lines, HTTP status+body, error strings inline. "Captured output shows X" without quoting X is a violation.
2. **No internal step labels as evidence pointers.** Never "Reproduce: STAGE 5". Use (a) exact command, (b) one sentence on what it does, (c) exact expected output quoted, (d) one sentence on what it proves. Attached scripts: first 3 docstring lines = what it proves / expected output / meaning.
3. **Never pre-concede the impact ceiling in the opener.** "Filing as P{N}", "Severity", "Summary", and first paragraph lead with the trust boundary that IS crossed (service / other tenant / wrapper-product user — never "my own sandbox"). ALL disclaimers ("not an escape", "no cross-tenant", "gVisor held", "not a confidentiality break") go in a "What this report does NOT claim" section LOWER in the body. **Born from AE1 (515695470) + M3 (515754412): both rejected with the triager quoting the report's own opener back.**
4. **Don't file under-bar findings standalone.** Availability/robustness-only with no confidentiality/integrity claim → fold into the parent (M3 should have been §X of E1).

## Methodology
1. Draft the opener LAST — after the findings — so it leads with proven impact, not hedges.
2. Each finding: mechanism-first prose → exact repro command → quoted expected output → claim mapping. One command, one expected output, one meaning, all in the body.
3. Put "What this report does NOT claim" BELOW the findings (honest scoping, never in the opener).
4. Engineer-grade test: a smart engineer who never heard of the project reproduces from the body alone, without opening a script. If they must open a script to understand the finding, the report failed.
5. Opener checklist before saving: leads with the boundary crossed? zero concession in the severity line? "does NOT claim" sits below findings? first 3 sentences name a specific impact + boundary + affected party?

## Triager-ready repro (user feedback 2026-07-30 — make it EASY on them)
The triager is a stranger with 15 minutes. The repro must run as-is.
1. **Setup block first, zero assumed context:** exact account/role needed and how to get it
   (signup path, email-verify, team to join), how to obtain the token (`Authorization: Bearer
   $TOKEN` — where to copy it from: dev tools → application → MMAUTHTOKEN, or the login
   response), the base URL as a variable. Every placeholder marked `<<like-this>>`.
2. **Copy-paste runnable:** real `curl` commands (or exact HTTP requests), one per step, in
   order, each on its own fenced block — never prose-described requests. Variables defined
   once at top (`BASE=`, `TOKEN=`, `RUN=`) so steps are paste-and-go.
3. **60-second version up top:** the minimal 3–5 commands that prove the crossed boundary,
   before the full chain. A busy triager who runs only these must see the bug.
4. **Each step four parts, plain words:** what this does (1 sentence, no jargon) → the
   command → the exact expected output (quoted) → what that proves (1 sentence). Explain the
   *why* — what the server should have done vs what it did — so the triager learns the bug,
   not just the recipe.
5. **Gotchas inline:** any non-obvious requirement discovered during testing (e.g. a required
   `operationName`, a mandatory field, timing/wait) goes in the step itself, marked
   "Note:", so the repro can't silently fail for them.
6. **Cleanup steps included:** how to undo anything the repro changes (leave/undo/revert),
   so the triager doesn't leave the target dirtied.

## Anti-patterns this prevents
- Pre-conceding the ceiling in the opener (the AE1/M3 rejection pattern).
- Filing availability-only findings standalone.
- "Captured output shows X" without quoting X.
- STAGE/Phase/Step labels a triager can't resolve.
- Drafting before the chain is fully exploited live.
- Filing a conceded-secure-config / unnameable-primitive as a bypass (PROGRAM_95 WAI).
