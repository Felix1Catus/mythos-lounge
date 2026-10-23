---
name: research_consult
description: Before quitting a wall or after a proven floor, read ~/research/ then return to the live target and fire the next probe. Use when the user says "read ~/research/", "read /research/", "01-auth-bypass-ato", "09-auth-logic", "before quitting a wall", or "perfect floor, read /research/ then go back".
user-invocable: true
---

# research_consult — read the library, then strike

## Trigger
The user says "read ~/research/", "read /research/", "before quitting a wall", or "perfect floor, read /research/ then go back". Also fire when you are about to quit a wall or after you prove a floor.

## Procedure
1. Stay on the live target. The consult is not a new job.
2. Open the folder that matches the wall class (curated numbered library under `~/research/`):
   - How to finish / 2026 frontier → `00-methodology/`
   - ATO / auth bypass / session mint → `01-auth-bypass-ato/` then `09-auth-logic/`
   - SSRF → `02-ssrf/`
   - IDOR / BOLA → `03-idor-bola/`
   - XSS → `04-xss/`
   - SQLi / GraphQL / ORM leak → `05-sqli-graphql/`
   - RCE / SSTI / Successful Errors → `06-rce/`
   - HTTP parser / desync / smuggling / cache → `07-http-parser-desync/`
   - SAML / SSO / OAuth / OIDC → `08-saml-sso/`
   - Auth logic (deeper) → `09-auth-logic/`
   - CVE PoCs → `10-cve-pocs/`
   - Tooling → `11-tooling/`
   - Recon methodology → `12-recon-methodology/`
   - CTF / labs → `13-ctf-labs/`
   - Web3 / blockchain / wallet policy → `14-web3-blockchain/`
   - Detection hunting → `15-detection-hunting/`
   - Open redirect → `16-open-redirect/`
   - Crypto → `17-crypto/`
   - AI / LLM / MCP / agent hijack → `18-ai-llm-attacks/`
   - Active Directory → `19-active-directory/`
   - File upload → `20-file-upload/`
   - JWT / session → `21-jwt-session/`
   - Race conditions → `22-race-conditions/`
   - Cloud / CI-CD / Firebase / IMDS → `23-cloud-ci-cd/`
   - CMS / WordPress → `24-cms-wordpress/`
   - XXE / XML → `25-xxe-xml/`
   - Deserialization → `26-deserialization/`
   - Privesc → `27-privesc/`
   - Takeover / DNS → `28-takeover-dns/`
   - Mobile / IoT / hardware → `29-mobile-iot-hardware/`
   - RE / malware → `30-re-malware/`
   - Supply chain → `31-supply-chain/`
   - postMessage / client-side → `32-postmessage-clientside/`
   Master index: `~/research/INDEX.md`. Term not in the numbered folders: `bash ~/.claude/mythos/rquery.sh <term>`.
3. Read enough to extract ONE transferable bypass, encoding, or control-gap. Do not summarize the library.
4. Return to the live target in the same turn. Fire the next probe using that knowledge.
5. Persist one line on the target (what you read, what you will try). Then strike.

## Rules
- Research is fuel for the next probe, not a substitute for probing.
- Do not quit the wall after reading. The read is the input to the retry.
- Do not dump the library. One folder, one new attack.
- Brain still wins: one discrimination, error class, next request. The folder is knowledge for that request.
- Published source on the live target → skill `source_first` (M1–M8) in the same pass.
