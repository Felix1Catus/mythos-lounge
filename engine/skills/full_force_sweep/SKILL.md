---
name: full_force_sweep
description: Comprehensive full-force secret/key/API-exposure sweep that PROVES exploitability (not just disclosure). Use when the user says "full force" or "sweep everything for secrets/keys/APIs."
---

# full_force_sweep — full-force secret/key sweep + prove-it

## Trigger
The user says "full force", "sweep everything for secrets/keys", or "find every exposed key/API."

## Pre-execution checklist
- [ ] GROUND: read target STATE files; know what's already swept/closed.
- [ ] Scope filter ready: in-scope (enrolled program) vs third-party (do NOT mass-target third parties).
- [ ] Bug-bounty header set; rate ~5 req/s default.
- [ ] Instrument validated against a KNOWN positive (step 2) BEFORE trusting any negative.

## Methodology (from attack/secret_sweep.py + attack/cargo_key_fanout.sh)
1. **Broad catalog scan, confidence-tiered:** HIGH = PRIVATE KEY, **JWK with RSA private `d`**, AKIA, GCP SA `private_key_id`, sk_live/rk_live, Stytch `secret-live`, GitHub PAT, Slack, SendGrid; MED = Twilio SK/AC, basic-auth URLs, x-api-key, secret_hash; LOW (usually public) = AIza, pk_live, public-token, PROGRAM_75 DSN, OAuth client_id, JWT, generic key=value. Scan mmap bodies AND on-disk bundles. Dedupe + redact.
2. **Instrument-validation (LOCKED lesson — the JWK false-negative):** the sweep once MISSED a known RSA-private JWK because the regex was too strict → it would have falsely reported "clean." ALWAYS confirm the catalog catches a planted known positive (the `"kty":"RSA"…"d":"…"` shape, a fake `AKIA…`) before believing a negative.
3. **Prove exploitability — never report "key exists":** a disclosed key is config-only (N/A) until you show it WORKS. Use the content-differential method (`cargo_key_fanout.sh`): request each candidate endpoint WITH and WITHOUT the key; compare status + body-SHA + preview. A real differential (with != without) = the key is honored = access, not just disclosure.
4. **Escalation ladder on 403 / inert:** don't stop at the first 403 — escalate past weak walls (spoof Referer, Origin, User-Agent; try sibling hosts/regions). For Google **AIza** keys: a key restricted on one API may be live on another — fan out across APIs; and test the **Firebase / Identity-Toolkit** path (`signupNewUser`, `getProjectConfig`, `verifyPassword`) to convert "key found" into "account/project action."
5. **Scope triage:** keep findings on enrolled-program hosts; tag third-party leaks out-of-scope (note, don't mass-target). Triage by scope + exploitability before writing anything.

## Output
- Categorized HIGH→LOW hit list (deduped, redacted) + the differential results proving which keys are LIVE
- `ESCALATION_GAPS.md` entries for each live key with the proven primitive

## Anti-patterns this prevents
- Reporting a key/endpoint that merely EXISTS (config-only = rejected; "never submit until fully exploited").
- Trusting "nothing found" from an unvalidated instrument (the JWK false-negative).
- Stopping at the first 403 instead of running the escalation ladder.
- Concluding "key restricted" after testing ONE API (AIza keys are per-API — fan out).
- Mass-targeting third-party hosts outside the enrolled program.
