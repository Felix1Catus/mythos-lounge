---
name: logic_level_re
description: Read critical code modules to find bugs in how secrets/inputs are USED — not strings that look like secrets. Use after automated sweeps return "clean" or only known findings; this is where P1s actually live (the report-04 RSA key was found by READING chunk 576, not by a grep).
---

# logic_level_re — read the code, find the logic bug

## Trigger
After automated sweeps (secret_sweep, nuclei, grep) return "clean" or only known findings. A clean grep means "no strings that look like secrets" — it says nothing about CODE THAT USES SECRETS WRONGLY. That code is where the P1 is.

## The core distinction
- Automated secret-grep finds: **strings that look like secrets.**
- Logic-level RE finds: **code that uses secrets/inputs wrongly.**
- The report-04 RSA key was NOT found by `secret_sweep.py` — it was found by *reading* chunk 576 and understanding it `JSON.parse`'d a private key and used it to sign the x-signature header. The detector was added AFTER the key was already known by reading.

## Methodology
1. **IDENTIFY the critical logic modules** (not all JS — the load-bearing ones):
   - Auth flows: login, token refresh, OAuth, OTP, session validation.
   - Payment: price calculation, validation, submission, webhooks.
   - File handling: upload, download, content-type enforcement.
   - Cross-origin: postMessage, CORS, iframe handling.
   - Crypto: signing, encryption, key management.

2. **READ the source — do not grep.** Pretty-print minified bundles first (`js-beautify`/prettier). For each module:
   - Map the data flow: where does user input ENTER? where does it EXIT?
   - Identify trust boundaries: what does the client trust from the server? what does the server trust from the client?
   - Find the interesting sinks/calls: `crypto.sign()`, `fetch()`, `eval()`, `innerHTML`, `postMessage()`, `localStorage`, `JSON.parse(<literal>)`, hard-coded key material.

3. **ASK THE BREAKING QUESTIONS** at each interesting point:
   - Is this validation client-side only? → server-enforcement bypass.
   - Does this header control routing? → confused deputy / cache poisoning.
   - Is a key used for both signing and verification (or shipped to the client at all)? → key confusion / forgeable control.
   - Does the server trust this client value? → parameter tampering.
   - Is this comparison timing-safe? → timing oracle.
   - Does the error differ per failure mode? → user/account enumeration oracle.

4. **PROVE OR DISPROVE — every "looks wrong" gets a targeted probe:**
   - Craft a minimal repro; don't stop at "looks wrong".
   - Content-differential: with vs without the manipulated input (status + body-SHA + preview).
   - Positive control: confirm the manipulation works on a known-vulnerable path before trusting a negative (see `self_audit` / instrument-validation).

## Anti-patterns prevented
- "secret_sweep returned clean, moving on." → Secrets in code ≠ wrong USE of secrets; the RSA key was missed by not reading the code, not by a regex.
- "I grepped for crypto and found nothing." → grep finds strings; RE finds logic in how strings are used.
- "The client-side code is minified garbage." → Pretty-print it, read the entry points, trace from there.
- Trusting a clean automated result without ever reading the auth/payment/crypto module by hand.

## Evidence references (verified on disk)
- `~/targets/PROGRAM_42/STATE/RESUME.md` lines 48-59 — report-04: a full RSA private key (`n,e,d,p,q,dp,dq,qi`) hard-coded + `JSON.parse`'d inline in chunk `576-a69d42de8aa39deb.js` (module 37246, the CAS auth client), RS256-signing the `/api/sms` x-signature header — found by READING the chunk.
- `~/targets/PROGRAM_42/notes/secret_resweep_2026-06-17_PM.md` — the JWK detector was order-dependent and MISSED the real key (fields alphabetical, `d` before `kty`); a grep-only posture would have reported clean. Positive-control validation against the known key chunk is mandatory before trusting a negative.
- The OTP-ATO (report-03) was found by understanding the auth flow's failure modes (captcha fail-open, no brute cap), not by any tool.
> NOTE: the elevation brief cited progress.txt lines 802-805/1660-1667; that file is 530 lines and has no such lines — verified sources are RESUME.md (report-04) + the resweep note above.
