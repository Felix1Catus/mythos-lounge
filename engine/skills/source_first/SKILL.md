---
name: source_first
description: Deep source audit of one published codebase — fork/version diff, patch-gap, trusting-client/malicious-server, second-path authz, forgotten-auth, secret-to-sink. Use when the target ships source, SDK, APK, WASM, or a fork; when the user says source-first, M1, M3, incomplete fix, or trusting client.
---

# source_first — read the tree, then confirm with one probe

Canonical: `~/targets/_shared/HUNTING_METHODOLOGY_SOURCE_FIRST.md`.
Brain: `~/.grok/rules/CRITICAL_HUNTER.md`. This skill does not run a recon stage before the shot.
If the client's bytes and the server's sentence already name the crack, send that request.
Pull a method below when the class has not moved and the tree is in hand.

## Trigger
Source is published (repo, SDK, mobile APK, WASM, fork, vendored copy). User says "source-first", "M1"–"M8", "incomplete fix", "trusting client", "malicious server".

## Tools (absolute paths)
- `/home/RESEARCHER/.local/bin/rea`
- `/home/RESEARCHER/.local/bin/jadx`
- `git diff` / `diff -r` for fork-vs-upstream and version N-vs-N-1

## Methods (pick ONE, confirm with a probe)
- **M1 fork/version diff** — removed guards, flipped export flags, un-backported fixes.
- **M2 patch-gap** — they fixed the PoC path; take the sibling branch to the same sink.
- **M3 trusting-client** — wire value used to size, index, bound, fetch, or pick an alg, unvalidated.
- **M4 second-path authz** — same object, two routes; one checks, one does not (BOLA/BFLA).
- **M5 forgotten-auth** — sibling endpoints skip the gate.
- **M6 secret-to-sink** — tokens in telemetry, logs, RUM, source maps.
- **M7 legacy/optional surface** — compat flags, debug, nopriv, old transports.
- **M8 mobile exported/runtime-registered** — exported receivers, deeplinks, JS bridges.

## Rules
- Probe confirms a source hypothesis. It does not discover by spraying.
- Impact must be self-evident (read/write/crash/code/lockout). Framing-only bugs → chain first.
- Depth over breadth: one component, not five programs.
- Tenant-data line still holds. Own accounts fire.
