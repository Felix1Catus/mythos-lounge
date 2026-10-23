---
name: ai_hunt_stack
description: Program-gated AI hunt tools — FuzzingBrain, oss-fuzz-gen, FuzzMing, Pentest-AI oracle, FuzzyAI, LLMFuzzer, Strix, MCP security servers. Use when the user says aihunt, fuzzingbrain, fuzzming, ptai, fuzzyai, hexstrike, or C1 C6 C7.
---

# ai_hunt_stack

Source lives in `/home/RESEARCHER/tools/ai-hunt/src`. Launcher: `/home/RESEARCHER/tools/ai-hunt/bin/aihunt`.
Brain still wins: one discrimination, error class, no spray. These tools confirm a source hypothesis or grind a local tree. They do not pick the target.

## Gate (every run)
```
/home/RESEARCHER/tools/ai-hunt/bin/aihunt list
/home/RESEARCHER/tools/ai-hunt/bin/aihunt run --program PROGRAM_71 --target api.PROGRAM_71.io pentest-ai
```
A host that is not named in that program's SCOPE file is refused. A path must sit under `targets/<program>` or the tool tree. Hexstrike does not start unless the operator exported `AIHUNT_ALLOW_HEXSTRIKE=1` in that shell.

## Which tool
- **Source C/C++/Java/Python project in hand** — `fuzzingbrain` (Docker) or `oss-fuzz-gen`. Point at the tree, not a URL.
- **Solidity / Foundry** — `fuzzming`.
- **Web finding you already have** — `pentest-ai` (`ptai` if pipx installed it). Oracle re-runs the exploit. No capsule, no finding.
- **AI the program owns** (their model endpoint, in scope) — `fuzzyai` or `llmfuzzer`. Not a jailbreak of this hunter.
- **Recon binaries** — the ones already in `~/go/bin` (httpx, ffuf, nuclei, katana). `mcp-for-security` is unmaintained reference. Do not stand up a second scanner swarm.
- **Hexstrike** — off. 150 tools, autonomous. Only if the operator turns the env flag on for one scoped host.

## After a tool returns
Same as any probe: quote the class, reflect it, name the sibling. A fuzzer crash is a floor. Climb it or write the capsule. Do not file a tool's self-report.
