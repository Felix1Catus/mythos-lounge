---
name: cross_vertical_map
description: Map a target's FULL multi-app/vertical ecosystem before hunting, so you attack the untouched verticals where P1s hide — not just the one app everyone else swept. Use when starting recon on any target with multiple apps/products/regions, or when tempted to say "I already swept the main app."
---

# cross_vertical_map — hunt the ecosystem, not the one app

## Trigger
Starting recon on any target with multiple apps / products / verticals / regions (ride-hailing + cargo + intercity + payments + admin), OR the moment you catch yourself thinking "I already swept the main app." You swept ONE vertical; the ecosystem is the target.

## Why this finds P1s
Competitors converge on the obvious flagship app. The P1s sit in the sibling verticals nobody mapped — same backend, *different* client build, *different* auth flow, *weaker* validation. The bug is in the seam between verticals that share infrastructure but not controls.

## Pre-execution checklist
- [ ] GROUND: read the target's `STATE/RESUME.md` + `GAP_PLAN*.md` — know which verticals are already MAPPED vs UNTOUCHED.
- [ ] Scope confirmed per vertical (in-scope / out-of-scope / unknown) before any live fetch.
- [ ] Bug-bounty header set; rate ~5 req/s default.

## Methodology
1. **INVENTORY every named app in the ecosystem.**
   - Sources: subdomain enum (crt.sh/gau/amass), marketing/landing pages, app-store listings (iOS+Android), support/help docs, the in-scope asset list.
   - For each: web frontend vs native-only? region(s)? scope status (in / out / unknown)?
   - Output a table: `vertical | host(s) | web?/native? | region | scope | status{MAPPED|PARTIAL|UNTOUCHED}`.

2. **MAP each vertical's API surface INDEPENDENTLY.** Do not assume the flagship's surface generalizes.
   - Root HTML → JS bundles → `_buildManifest` → **BFS recurse into lazy chunks** (real auth/keys live in lazy/page chunks — see `logic_level_re`).
   - Per vertical, catalog: unauth endpoints, auth flow (OTP/OAuth/token-refresh), file upload, payment, chat/realtime (Centrifugo/WS).
   - Cross-reference shared backends: pull any service/router registry (e.g. an unauth `/api/router` that lists the mesh) to see which verticals hit the SAME gateway/storage/processor.

3. **IDENTIFY the untouched verticals.** Mark each MAPPED / PARTIAL / UNTOUCHED. The UNTOUCHED rows are the priority — that's where competitors haven't looked. Dark/regionally-unreachable hosts (geo-WAF 403) count as UNTOUCHED, not closed — note the egress needed.

4. **GAP REPORT — the seams between verticals that share a backend but differ in client/controls:**
   - Same API gateway, **different auth** → confused deputy (one vertical's looser client trusts a header the other validates strictly).
   - Same storage, **different access controls** → cross-tenant read.
   - Same payment processor, **different validation** → price manipulation / webhook abuse.
   - Same OTP/CAS backend, **different captcha enforcement** → the ATO chain ports across verticals (forged-sig on the lax client → unauth OTP).
   - Write each seam as a concrete next probe and hand it to `chain_completer`.

## Anti-patterns prevented
- "I already swept the main app." → You swept ONE vertical. List the ecosystem; most rows are UNTOUCHED.
- "That's native-only, skip it." → Native webviews ship JS bundles too; the native gateway may be pinned but the web sibling often is not.
- "The API is the same everywhere." → Different client builds hit different endpoints with different auth — map each independently.
- Treating geo-dark hosts as closed. → They're UNTOUCHED-pending-egress, the richest unmapped surface.

## Evidence references (verified on disk)
- `~/targets/PROGRAM_42/STATE/GAP_PLAN_2026-06-17.md` — line 144: "Only the COURIER/delivery vertical was hunted; RIDER ride-hailing + intercity (core product + price-bid mechanic) untested." A1 (line 20) rider/payment/chat mining; A7 (line 93) rider+intercity surface BLOCKED on geo-egress.
- `~/targets/PROGRAM_42/STATE/RESUME.md` — line ~128: ~65% of in-scope hosts dark (regional CIS/LATAM egress); `/api/router` registry = 210 internal hosts / 73 modules across verticals (lines 96-105).
- The cross-vertical seam pattern (cargo vs couriers sharing the cas OTP backend with different captcha enforcement) is the basis of report-04's x-signature chain.
> NOTE: the elevation brief cited progress.txt lines 119-127/125 for this; those line numbers do not exist in that 530-line session log — the verified source is GAP_PLAN_2026-06-17.md as above.
