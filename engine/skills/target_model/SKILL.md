---
name: target_model
description: Build and maintain STATE/TARGET_MODEL.md — the trust-boundary / identity / money-flow map of the target that tells you where the system STOPS thinking. Use after recon discovery, before striking, and whenever a probe reveals new architecture.
---

# target_model — attack the model, not the endpoint

A target is a set of assumptions its developers never re-examined. The bug IS the assumption.
TARGET_MODEL.md (template: `~/.claude/mythos/templates/TARGET_MODEL.md`) is where those
assumptions are written down so you can feed the machine the exact input each one forbids.

## What the model must answer
1. **Trust boundaries.** List every hop: browser → CDN → edge → API gateway → service → DB ·
   web → mobile backend · tenant → platform · partner → core. For each: what does the receiver
   TRUST from the sender (headers? tokens? signed params? source IP? nothing)?
2. **Identity lifecycle.** Where identity is established (login, OAuth, magic link, SSO) ·
   where it is RE-CHECKED (every endpoint? some? cached?) · where it is ASSUMED (internal
   services trusting gateway headers, microservices with no auth, "internal-only" mounts
   reachable through the proxy). The gap between established and assumed is ATO country.
3. **Money/data/authority flows.** Where prices/quantities/roles/permissions are SET vs
   CHECKED vs CONSUMED. Any field set client-side and consumed server-side without re-derivation
   is a forge candidate.
4. **Component trust chain.** What each component believes about the previous one — especially
   parsers that disagree (proxy vs app path normalization, JSON vs form, unicode handling).
5. **UNKNOWNs.** Every admitted unknown is a probe target. A hidden unknown is a missed P1.

## How to build it
- From: live client bundles (the JS is the honest documentation), observed responses, error
  messages, redirect chains, header behavior, the recon output in `recon/`.
- Every claim in the model carries its evidence (probe id / file path / response class) or is
  marked `[ASSUMPTION — NEEDS PROBE]`.
- Update it the moment any probe reveals architecture. A stale model attacks a target that
  no longer exists.

## How to strike from it
Cross every fact against every primitive (recombination matrix): cross-context replay ·
trust-edge substitution · identity/scope confusion · confused-deputy redirection ·
state/representation mutation · forced-operation abuse · leftover/deprecated surface ·
path & parser asymmetry · TOCTOU · encoding/normalization divergence.
**The absurd-feeling cells are the best leads.** Feed each into `STATE/LEADS.md` with a
designed first probe.
