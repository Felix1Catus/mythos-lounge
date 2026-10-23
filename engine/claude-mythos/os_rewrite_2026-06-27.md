# OS section-by-section rewrite (option A) — 2026-06-27 — running log

**Goal:** enhance the always-loaded OS (`~/.claude/CLAUDE.md`) + source manual (`~/MYTHOS_CLAUDE_OS.txt`)
for novelty / bypass / digging / better testing — section by section, each round RESEARCHER-approved.
Backups per round in `~/.claude/backups/os_2026-06-27*/`. CLAUDE.md mirrored to account2 (parity kept).
Manual is a single shared `~/` file. Validate every round (rules count, structure intact, parity).

## ROUND 1 — DONE (2026-06-27, apply-then-show)
- CLAUDE.md Hard **Rule 7 sharpened** (+ "positive-control EVERY load-bearing negative; multi-lever → assume
  ≥1 broken probe") and **new Rule 8: READ THE RESPONSE CLASS, NOT THE STATUS CODE** (→ `differential_oracle`).
- Manual §2 mirrored (Rule 7 sharpened + Rule 8 added, RULE/WHY/PRACTICE form, #18 + cross-product WHYs).
- Manual **§8 dead stub** ("Decision Framework cont'd — intentionally left blank") **repurposed** →
  "8. INSTRUMENT & DIFFERENTIAL DISCIPLINE" (artifact catalog + 6-step differential method).
- Validated: CLAUDE.md 7→8 rules, manual 7→8 rules, 0 "left blank", Core Loop/Language intact, parity.

## ROUND 2 — DONE (2026-06-27, draft-approved-then-apply)
- CLAUDE.md **new `## [SEC] Offense Doctrine` section** (after Decision-Framework [SEC], before Anti-Patterns):
  skill dispatch (generative=driver / methos_engine=palette / zero_day=barriers / differential_oracle=instrument
  + tactical playbooks) + 6-point doctrine (reverse-engineer · recombination · barrier-is-target · never-first-NO ·
  chain-to-ceiling · read-the-bundles).
- Manual **new `10. THE OFFENSE DOCTRINE`** (before Quick Ref, no renumber) — long-form: full recombination
  primitives list + bypass ladder + the intercity cross-product WHY.
- Validated: CLAUDE.md 8→9 sections, manual §10 present, §8/§9/Quick-Ref intact, parity, sizes 8811→11312 /
  33126→38011.

## ROUND 3 — DONE (2026-06-27, apply-then-show)
- CLAUDE.md §1 + manual §1 Core Loop enriched WITHOUT changing the 5 steps: PROBE now "capture the
  response class, vary one thing, differential-ready"; ANALYZE now "classify by response class, not the
  status line (Rule 8), compare to baseline/control, name the confound"; VALIDATE now "positive-control
  every load-bearing negative (Rule 7)". Validated: 5-step diagram intact, 9 sections, parity.

## ROUND 4 — DONE (2026-06-27, apply-then-show, manual-only)
- Manual §3 PHASE:EXECUTION gained `PATTERN: Offense-in-the-Loop (recombine, then ladder past the wall)` —
  5-step in-loop move (recombine angle → ≥5-bypass ladder → read the wall via §8 differential → DISPROVEN≠done
  re-attack with a different primitive → persist failures + chain). Cross-refs §8, §10, the 3 engine skills.
  No duplication of the primitive list (points to §10). Validated: Three-Layer + Script-to-File intact,
  19 PATTERN blocks, 38011→40256B. CLAUDE.md untouched (manual-only round).

## ROUND 5 — DONE (2026-06-27, apply-then-show, CLAUDE.md + dedupe)
- Anti-Patterns: added **Status-code closure** + **Single-engine misfire**.
- CONSOLIDATED the R2 overlap: removed the duplicate [SEC] "403 ≠ final" bullet (Offense Doctrine §3 now owns
  barrier-bypass, enriched with the referer/origin/UA/method/path/encoding examples it absorbed). [SEC]
  "Confirmed impact only" now points to §3 for bypass mechanics.
- RECONCILED a real floor/ceiling clash: [SEC] said "file at the proven FLOOR", Offense pt5 said "file at the
  proven CEILING" (opposite words, same action) → both now "file at the **highest severity you've proven**"
  (no overclaim above, no pre-concession below). Line-78 intro "floor/ceiling" metaphor left intact (deliberate).
- Validated: 9 sections, [SEC] 6→5 bullets, '403'-as-standalone-bullet gone, Hard Rule 8 intact, parity, 12083B.

## ROUND 6 — DONE (2026-06-27, apply-then-show)
- CLAUDE.md §3 Self-Correction: new bullet **"Stuck ≠ stop — recombine"** (the done/blocked/DISPROVEN feeling
  is the recombination trigger, not the exit: check the wall is real via differential_oracle, then recombine
  fact×untried-primitive, re-attack DISPROVEN with a different primitive). + differential_oracle routed into
  the Confound-control bullet. Now 5 bullets, 2 differential_oracle refs.
- Manual §4 Self-Correction Protocol: new `PATTERN: Stuck-Is-The-Trigger (recombine, don't stop)` (5-step:
  trigger→suspect-the-wall→recombine→bypass-ladder→only-then-status). Now 6 patterns. §5 banner intact.
- Validated: CLAUDE.md 9 sections, parity; manual §4 6 patterns, Theory-Closure + §5 intact.

## ROUND 7 — DONE (2026-06-27, apply-then-show)
- CLAUDE.md State Architecture: new **MEMORY.md (account index)** bullet — one-line pointers, under load
  budget or it partially loads, one pointer per topic file, no orphans/over-long hooks.
- CLAUDE.md Relationship-to-memory: added **[[feedback_instrument_artifact_discipline]]** to the authoritative
  link list (target confirmed on disk) + new **Operational skill layer** line (generative=driver / methos_engine=
  palette / zero_day=barriers / differential_oracle=instrument + tactical).
- Manual §5: new **INDEX HYGIENE** note (applies to RESUME.md / STATE/INDEX.md / account MEMORY.md). LAYER 1-5 intact.
- Validated: 9 sections, parity, no dangling link, §6 banner intact.

## ROUND 8 — DONE (2026-06-27, apply-then-show)
- Both Language sections gained 3 signal phrases: "The barrier is the target." · "Stuck is the trigger, not
  the exit." · "Read the class, not the code." (manual §9 as full PHRASE/Use-when entries).

## FINAL CONSISTENCY PASS — DONE (2026-06-27) — ALL PASS
- Manual sections **1→10, no gaps/dupes**; every `Section N` xref (6/8/10) resolves; manual 8 RULEs + Rule 7/8
  refs resolve; all 10 backtick skill-names exist as dirs; CLAUDE.md 9 sections, 'proven ceiling' clash = 0;
  acc1==acc2 parity. (Caught + fixed a broken check-grep that required literal "THE" and false-missed the
  repurposed §8 — instrument artifact, not a real defect.)
- `mythos-verify` (5/5 PASS): CLAUDE.md, settings.json + both SessionStart hooks, mythos memory + rate posture
  + MEMORY index, output-style + commands, source manual — all intact.

## ✅ OPTION (A) COMPLETE — 8 rounds + final pass. CLAUDE.md 7951→13398B, manual 29802→42666B.
Backups: `~/.claude/backups/os_2026-06-27{,_r2..r8}/`. Both files mirrored to account2 (CLAUDE.md) / shared (manual).
- Then: full read-through pass for cross-ref consistency (mythos-verify).

## KNOWN FLAGS
- account2 `MEMORY.md` (25.4KB) has DIVERGED from this store's (now 18.8KB) — left untouched, separate brain.
- R2's deliberate minor redundancy (Offense pts 3&5 vs Decision-Framework [SEC]) → RESOLVED in R5 (dedupe + floor/ceiling reconcile).
