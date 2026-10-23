# REDACTION NOTES — what was removed/scrubbed from this bundle

This bundle is the **framework**, not an operating hunter's live workspace. The following
was deliberately excluded or scrubbed so it is safe to share.

## Fully EXCLUDED (never copied in)

- All **journals** (`*.ndjson`), logs (`*.log`), and session markers (`stop_nudged_*`, `active_target`).
- All per-target **STATE/** directories and findings (SCOPE, RESUME, CHECKPOINT, LEADS, CHAIN_LEDGER, etc.).
- The **memory store** (user/feedback/project notes).
- Credential / key files (`key_verification.md`, `key_leakage_audit*`, `*.key`, `*.pem`, `*api_key*`).
- `__pycache__/`, `*.pyc`, `*.bak*`.

A post-build secret scan (OpenAI `sk-`, Google `AIza`, bearer tokens, PEM blocks) returned **clean**.

## SCRUBBED (content kept, identity removed)

- **Distinctive target names** (103 programs: the real brand/program names in doctrine receipts
  and example scripts) -> opaque tokens `PROGRAM_01 .. PROGRAM_NN`, whole-word, case-insensitive.
  The *mechanism* of each example survives; the *identity* does not. (The reverse legend was
  NOT included — it stays with the bundle's author.)
- **Personal identifiers** -> generic: researcher handle, email, name, and `/home/<user>/` ->
  `/home/RESEARCHER/`.

## NOT auto-scrubbed — review before wide distribution

These program names collide with ordinary English / technical terms, so a blind replace would
corrupt the doctrine. They were left in place. Occurrence counts and what they actually are:

| token | count | what it actually is here (sampled) |
|---|---:|---|
| `box` | 78 | almost all generic: "sandbox", "blackbox", "toolbox" |
| `clear` | 77 | generic verb: "clear state", "clear criteria" |
| `google` | 123 | mostly Anthropic skill text ("Google Docs/Drive/Sheets") + 1 Google-Cloud IP range; **not** the author's VRP findings (those were excluded with memory/STATE) |
| `meta` | 44 | generic: "meta-prompting", AWS `meta-data` SSRF endpoint, `--meta` flag |
| `arc` | 14 | generic: "architecture", "search" fragments |
| `wallet` | 13 | generic crypto-wallet prose + a couple of EUDI-wallet references |
| `blend` | 10 | generic verb |
| `mutate` | 7 | generic: "mutate structure" (fuzzing technique) |
| `0x` | 6 | generic hex prefix |
| `misc` | 6 | generic |
| `cb` | 3 | generic abbreviation |

**Recommendation:** these are overwhelmingly generic. If you want zero residual target flavor,
skim the `wallet`/`google` hits (the only ones that ever point at a real program context) and
hand-edit. Everything else is ordinary technical vocabulary.

## If you spot a leak

Tell the author. The scrub is best-effort on a corpus full of common-word program names; it is
not a guarantee. Treat the bundle as "cleared for a trusted collaborator," not "cleared for public."
