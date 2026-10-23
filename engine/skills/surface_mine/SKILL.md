---
name: surface_mine
description: Discover attack surface and extract secrets/keys/endpoints from a data dump, mobile capture (.mmap), or bundle directory. Use when the user provides a *.txt cURL/HAR dump, a mitmproxy .mmap, or a recon/bundle directory to analyze or "mine".
---

# surface_mine — surface discovery from data dumps

## Trigger
The user hands you a `*.txt` cURL/HAR dump, a mitmproxy `.mmap` capture, an APK/JS bundle directory, or says "mine this / map the surface / what's in this dump."

## Pre-execution checklist
- [ ] GROUND: read the target's `STATE/RESUME.md` + `DEAD_ENDS.md` + `ESCALATION_GAPS.md` first — know what is already mined and closed.
- [ ] Probe the input exists: `ls -la`, `file`, `wc -l` / `wc -c`.
- [ ] Confirm scope (in-scope host/program) and set the bug-bounty header (e.g. `X-Bug-Bounty: <handle>`).
- [ ] Rate posture: ~5 req/s (0.2s/req) for live fetches; burst only if a finding's proof needs it.

## Methodology (extracted from attack/fresh_pull.py + attack/secret_sweep.py)
1. **Pull live surface (web app):** fetch each app root HTML → derive Next.js `buildId` / `_buildManifest` → BFS-fetch EVERY referenced `.js`, **recursing into fetched JS to catch LAZY chunks** (real keys hide in lazy chunks, not the HTML — proven on PROGRAM_42 report-04). Save to `recon/fresh_<date>/<app>/`. Cap ~300 files/app.
2. **Extract bodies from captures:** for a `.mmap`, decode every req+resp body for ALL intercepted hosts (target AND third parties) → `recon/mmap_bodies/<host>/` for reuse.
3. **Scan the credential catalog** (`secret_sweep.py`), confidence-tiered: HIGH = provider secret classes (PRIVATE KEY, JWK RSA `d`, AKIA, GCP SA, sk_live, Stytch secret); MED; LOW = usually-public (AIza, pk_live, JWT, generic key=value). Dedupe, redact.
4. **Known-vs-new triage:** for every hit/endpoint, grep ALL state files — `DEAD_ENDS.md`, `SUBMISSION_QUEUE.md`, `SESSION_LOGS/`, **and `ESCALATION_GAPS.md`** (the recurring miss) — to split NEW surface from already-worked.
5. **Escalation-gap check:** for each NEW high/med hit ask "what does this let me DO?" and log a concrete next probe in `ESCALATION_GAPS.md`. Something that only "exists" is not a finding (see `full_force_sweep` to prove keys live).
6. **Positive-control validation:** before trusting "clean / nothing found", confirm the instrument catches a KNOWN positive. Uniform-blank is usually a broken instrument, not a clean target.

## Output
- `recon/fresh_<date>/` (bundles) + `recon/mmap_bodies/` (decoded bodies)
- Categorized hit list (HIGH→LOW) with host/file + redacted value
- New `ESCALATION_GAPS.md` entries, each with a concrete next probe

## Anti-patterns this prevents
- Scanning only HTML and missing lazy-loaded chunks where real keys live.
- Reporting "key/endpoint exists" as a finding (config-only = N/A).
- Trusting "nothing found" with no positive control (false-negative from a too-strict regex).
- Re-mining closed surface because the known-vs-new sweep skipped ESCALATION_GAPS.
- Fetching with no rate limit / no bug-bounty header.
