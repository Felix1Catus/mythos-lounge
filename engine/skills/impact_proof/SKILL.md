---
name: impact_proof
description: End-to-end impact confirmation protocol — climb the proof ladder from confirmed primitive to attacker-meaningful end state to report-ready narrative, with minimal-victim-record discipline and a logged chain ledger. Use whenever a finding is real but impact is not yet proven, and before drafting any report.
---

# impact_proof — from "real behavior" to "proven impact"

Confirmed behavior is not impact. Impact is what a triager pays for. Climb the ladder one rung
at a time; never claim a rung you haven't stood on; log every rung-up attempt to
`~/targets/<prog>/STATE/CHAIN_LEDGER.md`.

```
R0 lead        untested shape/anomaly
R1 anomaly     confirmed differential (positive-controlled — not an instrument artifact)
R2 primitive   controllable behavior held
R3 boundary    trust boundary IS crossed (auth context / tenant / origin / privilege)
R4 end state   attacker-meaningful result PROVEN (session minted, data read, money moved, code run)
R5 narrative   what a real attacker does with R4 — written, reproducible, evidence inline
```

## The climb protocol
1. **Restate the floor** in one sentence with its evidence pointer.
2. **Name the next rung and the single missing link.**
3. **RE the consumer** — the real client's code that mints/redeems/grants/renders using your
   primitive.
4. **Climb one rung** — mint/forge/obtain the link; prove the end state with the MINIMAL
   demonstration. One variable per probe; read response classes.
5. **R4 discipline:** cross-user proof = ONE minimal victim record, never mass-exfil. Restore
   any state you changed (refund/delete/revert) and read-back verify the restore. Secrets and
   tokens → `chmod 600` evidence files, referenced by path, never printed to chat.
6. **Write R5** — preconditions → steps → result → scale (how many victims, how much money,
   how repeatable). A triager must be able to reproduce from your notes alone.

## Before declaring any rung
- Re-read every claim; each maps to a captured response. Unmapped claims come out or get probed.
- Positive-control every load-bearing negative encountered during the climb.
- Save raw requests/responses under `evidence/` — the report is only as strong as its captures.

## If the ceiling won't break
≥5 structurally-different attempts at the missing link, each logged with what it taught, then
file the proven floor cleanly with the gap NAMED (never claimed). A filed floor beats an
imagined ceiling — and the ledger is exactly where the next session resumes the climb.

Then: `report_draft` — opener leads with the boundary that IS crossed; disclaimers BELOW the
findings; zero concession language in the severity line.
