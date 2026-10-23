# SEAT ENTRY STANDARD — how every target board is laid out
_by: supervisor-claude 2026-09-12. Purpose: a seat entering ANY target knows in <2 min where things
are, what's proven, what's DEAD (never re-probe), which surfaces are queued and when to fire them,
and when to pivot. Reference implementation: `PROGRAM_02/` (the gold board). Less is noise — keep it tight._

## Read order on entry (warm-boot, <2 min)
1. **STATE/CHECKPOINT.md** — the intent head: NOW / GOAL / APPROACH / NEXT / BLOCKERS / FILES. One screen. Fire its NEXT first.
2. **STATE/DEADENDS.md** — dead surfaces + *why* (blocker evidence). **Never re-probe anything here.** This is the anti-time-waste file.
3. **STATE/LEADS.md** — ranked surfaces (Critical-shape first) with: Class · Shape · Gate · status. Has a **"First move NOW"** line and a **"Dead (do not touch)"** tail.
4. **STATE/RESUME.md** — the narrative: phase · PROVEN (probe-backed only) · active thread (floor/ceiling/missing-link) · next · blockers · newest-first log.
5. Deeper only if needed: **TARGET_MODEL.md** (how the server thinks / trust boundaries), **SCOPE.md** (exact in-scope assets + identifier), **CHAIN_LEDGER.md** (finding chains), **COVERAGE.md** (surface×class×status), **JOURNAL.ndjson** (raw auto-trail — truth of last resort).

> Conflict rule: a probe beats any board. CHECKPOINT/RESUME are intent, not ground truth — re-verify one PROVEN line with a fresh probe on entry.

## Canonical STATE/ files (presence = board maturity)
| File | Holds | Seat uses it to… |
|---|---|---|
| CHECKPOINT.md | intent head, `_by:`+ts | warm-boot in one screen |
| DEADENDS.md | killed surfaces + blocker evidence | NOT waste time re-probing |
| LEADS.md | ranked surfaces + gate + first-move | know what to fire and when |
| RESUME.md | phase / proven / floor-ceiling-missing / log | full narrative state |
| TARGET_MODEL.md | trust boundaries, identity/money flows | hunt the delta |
| SCOPE.md | exact assets + required identifier header | stay in-scope |
| CHAIN_LEDGER.md | floor·ceiling·missing per finding | escalate to ceiling |
| COVERAGE.md | surface×class×status, timestamped | find empty cells |

## Root-dir hygiene (reduce seat noise)
Target root holds ONLY: `STATE/`, `notes/`, `evidence/`, `recon/`, `scripts/`, `js/`, and at most ONE current capture file. Loose files, dated scratch, old captures → a subdir. A root with dozens of loose files = noise a seat has to wade through.

## Pivot doctrine (when to move off a surface) — from core law
- **DEADENDS entry** = never re-probe that surface/angle from this position.
- **2-fail rule**: same error class twice on a surface → stop mutating, get ground truth (introspect / capture / diff), don't fire a 3rd guess.
- **Kill criteria**: 2–3 structural bypasses all hitting the SAME infra-level block = egress/edge gate → DEAD; log to DEADENDS, pivot.
- **Entropy-first**: UUIDv4 / 128-bit random token ⇒ prediction DEAD → pivot to structural (binding/race/leak/lifecycle).
- Every finding → floor · ceiling · missing-link; escalate to ceiling before celebrating the floor.

## Status vocabulary for the portfolio index
`ACTIVE` (being hunted now) · `NEXT` (board ready, queued) · `STAGED` (board built, gated on a human unlock) · `DORMANT` (paused, resumable) · `FILED` (report(s) submitted, awaiting triage) · `CLOSED` (resolved/duplicate/WAI — archive).
