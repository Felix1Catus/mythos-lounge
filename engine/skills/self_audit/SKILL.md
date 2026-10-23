---
name: self_audit
description: End-of-work-item meta-cognitive check — did I probe (not assume), persist to disk, and validate my instrument? Invoke after completing any task that involved a probe, analysis, or file modification, before acknowledging completion or moving to the next item. Also invoke when the user says "persist", "presist", "Persist + end", or "Execute, persist, end turn."
---

# self_audit — the 3-question check before "done"

## Trigger
The END of any work item that involved a probe, an analysis, or a file modification — BEFORE telling the user it's done or moving to the next item. Also when the user says "persist", "presist", "Persist + end", or "Execute, persist, end turn."

## The 3 questions
1. **DID I PROBE OR ASSUME?** Re-examine every factual claim just made. Did I run a command to validate it, or reason to it? For any claim reached by reasoning: mark it `[ASSUMPTION — NEEDS PROBE]` and queue a probe before the next work item.
2. **DID I PERSIST BEFORE MOVING ON?** Are results on disk — RESUME.md updated, GAP_PLAN.md status changed, notes/results filed? If not, do PERSIST now. If it isn't on disk, it didn't happen.
3. **DID I VALIDATE MY INSTRUMENT?** If any result was surprising, null, or exciting: did I test the instrument against a known positive before trusting it? If not — halt, validate, then verdict.

## Output
Emit exactly one line:
- `Self-audit: PASS` — all three satisfied.
- `Self-audit: FAIL — <reason>` — and do NOT proceed to the next work item until the named gap is resolved (run the missing probe / persist / instrument-validation first).

## Anti-patterns this prevents
- Theory-closure: declaring something true by reasoning instead of a probe.
- Moving on with results stranded in chat (lost on /clear).
- Trusting an exciting/null result from an unvalidated instrument.
- Saying "done" before the work survived to disk.
