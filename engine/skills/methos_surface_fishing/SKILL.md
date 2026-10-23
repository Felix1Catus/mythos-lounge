---
name: methos_surface_fishing
description: Surface discovery engine for massive targets (Google, PROGRAM_57, etc.). Find the surfaces nobody else looks at — acquisitions, staging, internal APIs, partner integrations, deprecated services, edge deployments. Fish online passively, then validate live. Never just "enumerate subdomains" — hunt for the WEIRD surfaces where 0days live.
---

# METHOS SURFACE FISHING — Find What Nobody Else Found

## THE PROBLEM WITH NORMAL RECON
`subfinder -d google.com` finds 10,000 subdomains. 9,999 are hardened CDN endpoints.
The 1 that matters is `staging-legacy-api.partner.google.com` — and subdomain
enumerators miss it because it's a CNAME to an acquisition domain.

This skill finds the WEIRD surfaces. The ones that don't show up on wordlists.
The partner integrations. The deprecated services. The staging environments.
The edge deployments. The acquisition infrastructure.

## WHERE THIS SKILL SITS (routing + scope + discipline — read before fishing)
This is the **SURFACE-DISCOVERY front end** to the hunt. It finds WHERE to attack; the engines decide HOW.
- **Phase 4 deep-dive = `methos_generative_engine`** (driver) → `methos_full_vuln_engine` (payload library) →
  `zero_day_mindset` (barriers). Validation results read by **`differential_oracle`** (a 502/404/"blocked" is
  read by response CLASS, not assumed; crt.sh timing out is YOUR instrument, not a target signal — use a CT fallback).
- **NEW ≠ FRUITFUL (the hard lesson).** Finding a host nobody indexes is the easy half. Before you rank or
  deep-dive it, prove it's LIVE with a real attack surface — a 200 with a custom app, not a 404 (parked),
  a 502 (dead backend), or a published Google Sites / static page. A dead backend is not a finding.
- **DEPRECATED CALIBRATION.** "Deprecated = less-maintained = bugs" under-fits mature targets: Google TURNS
  DOWN deprecated products (→ 502/404), it doesn't leave them running-unmaintained. Prioritize **BETA/PREVIEW**
  (live + less-hardened) and **ACQUISITIONS** (old stack still running) over deprecated-and-dead.

**SCOPE GUARD (passive is free; LIVE probing is not).** PASSIVE fishing (search, CT, GitHub, docs) is
unbounded OSINT — fish anything. But **live validation (Phase 2) and deep-dive (Phase 4) only touch
in-scope / authorized-program assets.** Acquisition domains (photomath.com…), partner/reseller portals, and
third-party integrations are frequently OUT of a program's scope until integrated — **verify the program's
scope page BEFORE sending a single live request to them.** The anti-pattern "find surfaces first, scope them
second" applies to DISCOVERY, NEVER to PROBING. The one hard limit (other tenants' data / out-of-scope third
parties) governs; only the human submits.

## PHASE 1: PASSIVE ONLINE FISHING (no interaction with target)

### Source 1: Acquisitions & Partnerships
- Search: `site:google.com acquisition` `site:PROGRAM_57.com acquisition`
- Search: `Google acquired "company" 2024 2025` / `PROGRAM_57 acquired "company" 2024 2025`
- Search Crunchbase: `crunchbase.com/acquisition/google-acquired-company-*`
- For each acquisition: what domains did they own? Do those still resolve? 
  Are they still running the acquired company's stack?

### Source 2: Job Postings (reveal internal architecture)
- Search: `site:greenhouse.io google "backend" OR "API" OR "microservice"`
- Search: `site:lever.co PROGRAM_57 "API gateway" OR "authentication" OR "internal"`
- Search: `site:linkedin.com/jobs "google" "deprecated" OR "legacy" OR "migration"`
- Job postings reveal: internal service names, tech stacks, deprecated systems
  being migrated (the old system = less maintained = bugs)

### Source 3: GitHub & Open Source (find internal service names)
- Search GitHub: `org:googleapis` `org:Azure` — what internal libraries exist?
- Search: `site:github.com/google "internal" "api" "endpoint"`
- Search: `site:github.com/PROGRAM_57 "internal" "service" "host"`
- Look for: service names, endpoint patterns, internal hostnames in config files
- Look for: `.proto` files (gRPC services), `swagger.yaml`, `openapi.json`
- Look for: `.env.example`, `config.yaml` with internal host references

### Source 4: Developer Documentation (find API surfaces)
- `developers.google.com` — what APIs exist? Which are deprecated?
- `docs.PROGRAM_57.com` / `learn.PROGRAM_57.com` — same
- `cloud.google.com/apis` — catalog of all APIs
- `portal.azure.com` — service catalog
- Look for: APIs in beta/preview (less hardened), deprecated APIs (less maintained),
  partner-only APIs (less tested by security community)

### Source 5: Security Research History (find what's already known)
- Search: `site:bugs.xdavidhu.me google` — Google VRP writeups
- Search: `site:blog.google VRP` — Google own disclosures
- Search: `site:msrc-blog.PROGRAM_57.com` — PROGRAM_57 disclosures
- Search: `site:hackerone.com/google` — public disclosures
- What was found before? What was WAI? What patterns repeat?
- Look for: researcher names who find Google/PROGRAM_57 bugs → follow their methods

### Source 6: Certificate Transparency & DNS
- crt.sh: search for `%.google.com` `%.googleapis.com` `%.gstatic.com` `%.goog`
- crt.sh: search for `%.PROGRAM_57.com` `%.azure.com` `%.windows.net` `%.msftncsi.com`
- Look for: unusual subdomains, wildcard certs revealing internal patterns,
  cert subject alternative names exposing service names

### Source 7: Third-Party Integrations (the weakest link)
- Search: `"powered by Google" site:*.com` — find sites using Google services
- Search: `"powered by PROGRAM_57" site:*.com` — same
- Partner portals, reseller portals, developer portals — often less hardened
- Google Workspace Marketplace apps, Azure Marketplace apps

### Source 8: Deprecated & Legacy (where 0days live)
- Search: `site:code.google.com` — still alive? what's there?
- Search: `site:googlecode.com` — deprecated but may still resolve
- Search: `site:google.io` `site:google.dev` `site:google.page` — alt TLDs
- Search: `site:googleusercontent.com` — user content hosting (XSS goldmine)
- Search: `site:appspot.com` — App Engine apps (often abandoned)
- Search: `site:azurewebsites.net` — Azure web apps (often dev/staging)
- Search: `site:cloudapp.azure.com` — Azure cloud services
- Search: `site:sharepoint.com` — SharePoint instances (often misconfigured)

### Source 9: Error Pages & Leakage (passive recon from errors)
- Search: `"Traceback" site:google.com`
- Search: `"Server Error" "PROGRAM_57" site:azure.com`
- Search: `"Error 404" "nginx" site:google.com` — reveals backend servers
- Search: `"Powered by" site:google.com`
- Search: `inurl:apikey site:google.com` — key leakage (passive search only)
- Search: `inurl:.env site:google.com`
- Search: `inurl:config.json site:PROGRAM_57.com`

### Source 10: ASN & IP Ranges (find the edges)
- Google AS15169 — what IP ranges? What services on edge IPs?
- PROGRAM_57 AS8075 — same
- Shodan/Censys: `net:35.192.0.0/12` (Google Cloud) `net:13.64.0.0/11` (Azure)
- Look for: non-standard ports, unusual services, dev/staging markers

## PHASE 2: SURFACE VALIDATION (probe what's alive)

From Phase 1, you'll have 50-200 candidate surfaces. Validate:

1. **Resolve & reach**: does it resolve? HTTP 200? What's the tech stack?
2. **Tech fingerprint**: Wappalyzer-style detection from response headers
3. **Auth gate check**: unauth access? what auth type? (JWT, cookie, API key, OAuth)
4. **API discovery**: `/api`, `/v1`, `/graphql`, `/swagger`, `/openapi.json`
5. **Interesting endpoints**: `/health`, `/debug`, `/config`, `/admin`, `/internal`

Write a validation script that probes all candidates:
- Rate limited (≤5 req/s)
- Browser UA
- X-Bug-Bounty header
- Records: status code, content-type, server header, body hash, response time
- Flags: unusual status codes, verbose errors, debug endpoints, open admin

## PHASE 3: RANKING — What To Attack First

Rank each validated surface by:
1. **Uniqueness**: how many other researchers have looked at it? (lower = better)
2. **Tech stack complexity**: complex stacks = more bugs (Next.js + GraphQL + microservices > static HTML)
3. **Auth requirements**: unauth > guest > user > admin (lower barrier = more to explore)
4. **Business impact**: payment > identity > data > display (follow the money)
5. **Deprecation age**: older = less maintained = more bugs

## PHASE 4: DEEP DIVE (point METHOS at the top 3)

For the top 3 surfaces, run the full METHOS engine:
1. Architectural deconstruction
2. 10 novel attack generation
3. Execute + adapt
4. Breakthrough protocol if needed
5. Chain and file

## THE CREATIVE MANDATES FOR SURFACE FISHING

1. **THE ACQUISITION IS THE SURFACE** — acquired companies keep their old stack
2. **THE PARTNER PORTAL IS THE WEAKEST LINK** — less hardened than main product
3. **DEPRECATED ≠ DEAD** — deprecated services are less maintained = bugs
4. **ALT TLDS ARE GOLDMINES** — google.dev, google.page, google.io — who checks these?
5. **USER-GENERATED CONTENT HOSTING = XSS** — googleusercontent, blob.core.windows.net
6. **JOB POSTINGS REVEAL ARCHITECTURE** — internal service names in job descriptions
7. **GITHUB REPOS LEAK INTERNAL HOSTS** — config files, .env, deployment scripts
8. **ERROR PAGES LEAK STACK INFO** — traceback, server headers, framework version
9. **ASN EDGES ARE UNGUARDED** — non-standard ports, dev markers, staging environments
10. **IF EVERYONE ENUMERATES SUBDOMAINS, NOBODY FINDS THE REAL SURFACE**

## EXECUTION ORDER
1. Phase 1: Run all 10 passive fishing sources (online research)
2. Phase 2: Validate candidates live (probe with script)
3. Phase 3: Rank by uniqueness × complexity × impact
4. Phase 4: Deep dive top 3 with full METHOS engine
5. Phase 5: Persist everything to notes/methos_surface_fishing_[target]_[date].md

## ANTI-PATTERNS DESTROYED
- "Just enumerate subdomains" → that's what everyone does
- "Start with the main domain" → the main domain is the most hardened
- "Look at APIs first" → look at acquisitions, partners, and deprecated first
- "Only test what's in scope" → find surfaces first, scope them second
- "If it's not on a wordlist, it doesn't exist" → wordlists find what everyone finds
