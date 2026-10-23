# P01 EVIDENCE_FIRST — kills U1 (evidence-blindness), U8 (ritual)

**TRIGGER:** Before ANY new probe wave.

**RULE:** Before any new probe wave, grep `~/targets/<prog>/evidence/` and `scripts/` for
the path/shape/param you are about to request. If a real-client capture exists, the
client's path/params/body win over docs, memory, or guesses. State in one line which
evidence file justifies the wave. No line → the wave is a U1 violation.
Order of truth: **live capture > client JS/mobile > own prior artifacts > docs > memory > guess.**
