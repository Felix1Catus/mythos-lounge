# PIPELINE — the 7-stage hunt + proof ladder (read at hunt start / stage transitions)

1. **SCOPE** — program scope/exclusions/acquisitions → `STATE/SCOPE.md`. Exit: every in-scope
   asset class listed; nothing assumed.
2. **MAP** — verticals, apps, regions, acquisitions → `STATE/TARGET_MODEL.md` skeleton.
   Exit: verticals ranked by Critical-shape.
3. **DISCOVER** — subdomains, certs, archives, ASN, cloud; then LIVE CLIENT RE — JS bundles,
   mobile, API schemas. Exit: real routes/params extracted, not wordlist guesses.
4. **MODEL** — complete TARGET_MODEL: trust boundaries, identity mint points, money/data
   flows, what trusts what. **PLATFORM PRIMER lives here (see AGENTS.md Block A).**
   GATE: no striking until ≥3 trust boundaries + ≥1 identity or money flow mapped.
5. **RANK** — leads scored by Critical-shape → `STATE/LEADS.md`. Exit: top-3 leads have first
   probes designed (hypothesis + single input + success signal).
6. **STRIKE** — hypothesize the developer assumption → design the ONE input that violates
   exactly it → probe → read the response CLASS → NO: re-attack with a DIFFERENT primitive;
   YES: don't file — CHAIN. Class rotation closing-checklist per `creativity.md`.
7. **PROVE** — proof ladder to end-to-end impact, then `report_draft` at the proven floor.

## Proof Ladder
R0 lead → R1 anomaly (positive-controlled differential) → R2 primitive (controllable
behavior) → R3 boundary crossed (auth/tenant/origin/privilege) → R4 end state (session
minted / data read / money moved / code run) → R5 narrative (reproducible, evidenced).
- Report at the highest PROVEN rung. Never claim n+1 from n.
- Floor < Critical ⇒ missing link is the mandatory next work item.
- Every rung-up attempt logged in `STATE/CHAIN_LEDGER.md`.

## Large-scope protocol
Decompose program → verticals → surfaces → endpoints → params; hunt ONE ranked lead at a
time. Breadth timeboxed (parallel sub-agents), depth unbounded. Coverage ledger in LEADS.md:
instrument + timestamp per surface, or "covered" is a lie. Sub-agent output is a lead,
never a verdict — re-probe top leads yourself.
