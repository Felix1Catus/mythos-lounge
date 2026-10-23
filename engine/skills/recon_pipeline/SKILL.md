---
name: recon_pipeline
description: End-to-end recon methodology for large-scope targets — scope ingestion, vertical mapping, passive asset discovery, live-client RE, lead ranking. Use at hunt start on any program, especially large/multi-app scopes, before striking.
---

# recon_pipeline — scope to ranked strike queue

## OVERRIDE (2026-09-29 — this beats Stages 0–5)
Name one critical-shaped lead and fire its forbidden input in this pass. The error class
on that response is the model. Do not finish SCOPE, MAP, DISCOVER, and MODEL before the
shot. A `DEADENDS` line that stored only an HTTP status is reopened and retested from the
root cause; an infra identity gate with no class flip stays dead. Solo — do not delegate
and do not swarm. The stages below are notes you write from the response, not a gate.

The hunter who "hunts the program" finds nothing. Recon's output is not a host list — it is a
**ranked lead queue** where every lead has a first probe designed. Persist everything under
`~/targets/<prog>/` (scaffold with `bash ~/.claude/mythos/newtarget.sh <prog>`).

At hunt start, load without waiting to be told: `methos_generative_engine`, `zero_day_mindset`, `differential_oracle`, `critical-hunter`, `chain_completer`. Do not wait for "load all mythos skills".

## Stage 0 — KILL_LOG / DEADENDS (no-retread)
Read `STATE/RESUME`, then the target `KILL_LOG.md` and `STATE/DEADENDS.md` (and `~/claude-shared/agents/KILL_LOG.md` on a board seat) FIRST. Do not retread logged dead surfaces. This is hunt-start file #1 — before SCOPE.

## Stage 1 — SCOPE (`STATE/SCOPE.md`)
Parse the program brief: in-scope domains/wildcards/apps, exclusions, acquisitions, special
rules (rate limits, data handling). What's not written is not scoped — never assume.

## Stage 2 — MAP (verticals)
Every distinct app / product / region / tenant-type / acquisition. Rank each by Critical-shape:
does it touch identity mint, money, cross-tenant data, unauth state-write, code exec?
**The untouched vertical is where the P1 hides** — acquisitions, staging, partner integrations,
deprecated-but-live, regional variants. The flagship app was swept by a hundred hunters.
Delegate wide mapping to the `scope-architect` agent; verify its top claims yourself.

## Stage 3 — DISCOVER
- **Passive first:** subdomains (crt.sh, subfinder/amass if installed), cert transparency,
  Wayback/CommonCrawl URL archives, ASN/cloud ranges, GitHub/PROGRAM_35 org leaks.
- **Then live-client RE (higher signal than any wordlist):** pull the real SPA/mobile bundles;
  extract real routes, params, enums, captcha types, OAuth grant_types, role strings, feature
  flags, and anything the JS calls that the UI never exposes (`surface_mine`, `surface-re`).
- Persist raw output to `recon/` — chat-only recon didn't happen.

## Stage 3b — ENUMERATE (big, bbot-driven) — `~/targets/_shared/enum_pipeline.sh <prog>`
On a wildcard / multi-app scope, run the heavy enumeration once, early: `bash
~/targets/_shared/enum_pipeline.sh <prog>` (add `--vuln` for nuclei, `--ports` for portscan,
`--passive` for passive-only, `--top N` for lead count). It is **scope-gated** — it targets
only the in-scope roots parsed from `STATE/SCOPE.md`, so it never strays off-program. bbot
recursively discovers subdomains → web-probes → checks takeover (baddns), and writes the raw
event stream to `recon/enum/<date>/`. Breadth here is justified ONLY because the next stage
ranks it into depth — raw host lists are not findings; the neglected high-rank asset is.

## Stage 3c — RANK-SURFACE — `~/targets/_shared/rank_surface.py <prog>`
`enum_pipeline.sh` calls this automatically; re-run standalone to re-score. It folds bbot's
events into a per-host **bug-likelihood score** and writes `STATE/SURFACE_MAP.md` (full ranked
table) + an auto-block of the top leads in `STATE/LEADS.md`. The score (tunable in the script):
takeover/dangling-CNAME dominates (near-certain finding) · nuclei severity · auth-gated
401/403 (authz surface) · naked origin (no CDN → directly attackable) · hot names
(dev/staging/admin/api/legacy/git/jenkins/…) · non-standard open ports · outdated-tech-with-CVE
· minus a clone penalty so a farm of identical 200s is scored once. There is no canonical
"vuln rank" tool — this is a weighted score over signals bbot already emits. **Work DEPTH from
the top of SURFACE_MAP; do not spray the whole list.**

## Stage 4 — MODEL
Complete `STATE/TARGET_MODEL.md` (skill `target_model`): trust boundaries · identity
establishment and re-check points · money/data/authority flows · component trust chain ·
explicit UNKNOWNs. You attack the model, not endpoints.

## Stage 5 — RANK (`STATE/LEADS.md`)
Every lead scored by Critical-shape, each with: hypothesis (the developer assumption) ·
the ONE violating input · success signal · first-probe status. Top of queue = most
Critical-shaped, not most familiar. Coverage ledger: every swept surface gets instrument +
timestamp + result class — "covered" without those is a lie.

## Exit criteria
Top-3 leads have designed first probes and TARGET_MODEL has no load-bearing UNKNOWNs.
Then strike (skill `critical`, agent `critical-hunter`) — ONE lead at a time.

## Rules
- Breadth timeboxed, depth unbounded. You do the verticals yourself.
- The first live request is how the model gets written.
- Anomalies found during recon get a 3-probe budget on the spot — don't just log them.
