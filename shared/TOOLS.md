# TOOLS.md — pinned absolute paths for recon/security tooling (verified 2026-07-30)

**RULE (I1 scar): always invoke by ABSOLUTE PATH. Never bare `httpx`, `subfinder`, etc.**
`which -a httpx` → `~/.local/bin/httpx` (Python HTTP lib CLI, `#!/usr/bin/python3`) resolves
FIRST and silently breaks recon flags (`-l`, `-silent`, `-status-code`). The real
ProjectDiscovery httpx is `~/go/bin/httpx`. A third decoy exists at `/usr/local/bin/httpx`.

## Functional verification (this is what PASS means — not --version)

| tool | absolute path | verified by | result |
|---|---|---|---|
| httpx (ProjectDiscovery) | `/home/RESEARCHER/go/bin/httpx` | `echo https://example.com \| httpx -silent -status-code` | `[200]` ✓ |
| subfinder | `/home/RESEARCHER/go/bin/subfinder` | `-version` | v2.14.0 ✓ |
| nuclei | `/home/RESEARCHER/go/bin/nuclei` | `-version` | v3.7.1 ✓ |
| dnsx | `/home/RESEARCHER/go/bin/dnsx` | `echo example.com \| dnsx -silent -a` | resolves ✓ |
| katana | `/home/RESEARCHER/go/bin/katana` | `-version` | v1.2.1 ✓ |
| ffuf | `/home/RESEARCHER/go/bin/ffuf` | `-V` | 2.1.0-dev ✓ |
| crlfuzz | `/home/RESEARCHER/go/bin/crlfuzz` | `-version` | 1.4.0 ✓ |
| dalfox | `/home/RESEARCHER/go/bin/dalfox` | `version` | banner ✓ |
| gowitness | `/home/RESEARCHER/go/bin/gowitness` | `version` | banner ✓ |
| gau / anew / assetfinder / dnstake | `/home/RESEARCHER/go/bin/<name>` | no -version flag; run without args for usage | present ✓ |
| curl | `/usr/bin/curl` | `--version` | present ✓ |
| playwright (py) | python3 import | `import playwright` | OK (site-packages py3.12) ✓ |

## KNOWN TRAPS

- `httpx` bare → Python lib CLI. ALWAYS `~/go/bin/httpx`.
- `naabu` — NOT INSTALLED (`~/go/bin/naabu` missing). Don't plan on it.
- `/usr/local/bin/httpx` — third httpx, unverified; ignore.
- 57 tools in `~/go/bin` — `ls ~/go/bin` for the full arsenal (Gxss, VhostFinder,
  Web-Cache-Vulnerability-Scanner, brutespray, cdncheck, csprecon, gitdorks_go,
  github-endpoints, github-subdomains, gotator, hakip2host, inscope…).
- Python venv libs for probelib (pycryptodome): `~/targets/_shared/pylibs` (auto-path-inserted).
- Before ANY null/negative from a tool-based sweep: `python3 ~/targets/_shared/probelib.py`
  (self-test: 3 arms, PASS required) + one known-good host through the actual tool.

## MYTHOS INSTRUMENTS (Claude audit 2026-07-31 — all self-testing, absolute paths)

| tool | absolute path | self-test | verified 2026-07-31 |
|---|---|---|---|
| probe.sh — the one correct curl | `/home/RESEARCHER/targets/_shared/probe.sh` | `--selftest` | 2/2 PASS (known-good 200 · known-dead 000) |
| bypass_matrix.sh — method+path+trust+CORS, one instrument | `/home/RESEARCHER/targets/_shared/bypass_matrix.sh` | `--selftest` | 2/2 PASS (200\|559 vs 404\|559 — same size, different code) |
| selfprod.sh — CL-B self-prod protocol | `/home/RESEARCHER/.claude/mythos/selfprod.sh` | run on any prog | PASS (surfaced PROGRAM_69's 306KB unopened file + unrun APK) |
| rquery.sh — ~/research retrieval (14,060 files, full corpus, ~0.4s) | `/home/RESEARCHER/.claude/mythos/rquery.sh` | `--cats` | PASS |
| probelib | `/home/RESEARCHER/targets/_shared/probelib.py` | `python3 probelib.py` | 3/3 PASS, egress 197.37.236.75 |

**probe.sh replaces hand-rolled curl.** It mechanically enforces: mktemp+truncate per run ·
`000` = CONNECTION result, body suppressed, never stored beside a verdict · `--ip` forces
`--resolve` so SNI survives HTTPS-by-IP · `-k` is an explicit `--insecure-ok` decision echoed
in every class line. Proof of the SNI fix (2026-07-31): URL rewritten to IP →
`curl: (35) sslv3 alert handshake failure`, `000`; `probe.sh --ip` → `200 | sni=example.com@172.66.147.243`.

**httpx re-verified 2026-07-31 — the shadow is still live and still wins PATH:**
`which -a httpx` → `~/.local/bin/httpx` (python lib) **first**, then `~/go/bin/httpx` (real),
then a third at `/usr/local/bin/httpx`. Absolute path always.

## AUDIT / SELF-REPAIR INSTRUMENTS (unified audit 2026-07-31 — all self-testing)

| tool | absolute path | self-test | verified 2026-07-31 | prevents |
|---|---|---|---|---|
| `mine_user_msgs.py` — extract real human turns (or my own output, `--role assistant`) from Claude transcripts, filtering hook/reminder/tool_result noise | `/home/RESEARCHER/targets/_shared/audit/claude/mine_user_msgs.py` | `--selftest` | PASS (2-arm: keeps 2 human msgs, drops reminder + tool_result + assistant text) | U2 |
| `metrics.py` — recomputable stack health numbers over ALL transcripts (corrections/100, autonomy streak, CL-A verdict lint, compactions) | `/home/RESEARCHER/targets/_shared/audit/claude/metrics.py` | run it; 164 files / 1,856 turns in ~10 s | PASS | U11, U3 |
| `install_protocols.sh` — (re)materialise P01–P14 after any clobber | `/home/RESEARCHER/.claude/mythos/install_protocols.sh` | self-verifies 14/14 + `Kills:`/`Trigger:` headers | PASS 14/14 | U11 |
| `pretooluse_guard.py` — PreToolUse safety guard | `/home/RESEARCHER/.claude/mythos/pretooluse_guard.py` | `--selftest` (11 block-arm / 10 allow-arm) | PASS both arms | escape-harness, sibling-kill |

**The allow-arm is the point.** A guard that blocks authorised read-only work is not safe, it is
broken — its own self-test caught two false positives this audit (`cat /proc/sys/kernel/*` recon,
`dd if=file of=file`). Guard reads the WHOLE Bash string, so a command that merely *mentions* a
blocked pattern is blocked; build such strings in a file, not as a shell literal.

## PROGRAM TOOLS (durable, with self-tests; U-class tagged)
- `~/targets/PROGRAM_53/scripts/mmapi.sh` — authed community.PROGRAM_53.com API helper
  (`--selftest` = known-answer users/me 200+id; GET/POST arms). Prevents U1/U7/U2.
  Added 2026-07-30 (was 6+ inline TOKEN=... heredocs per session).
- `~/targets/_shared/manus_bridge/manus_mcp_bridge.py` — MCP stdio bridge exposing the Manus
  v2 API (task.create/sendMessage/listMessages/confirmAction) as Claude Code tools
  `manus_create_task`/`manus_send_message`/`manus_list_messages`/`manus_confirm_action`.
  Own venv at `~/targets/_shared/manus_bridge/.venv` (mcp 2.0.0 + httpx; system pip is
  PEP-668-locked). Contract verified against the live `openapi_v2.json`
  (`https://open.manus.ai/docs/v2/openapi_v2.json`), not guessed: base `https://api.manus.ai`,
  auth header `x-manus-api-key`. Self-tested 2026-08-12: real stdio JSON-RPC handshake +
  `tools/list` returns all 4 + a live `tools/call` against api.manus.ai returned a clean
  structured `401 unauthenticated` on a dummy key (proves URL/header/body shape, not just
  import). **Reads MANUS_API_KEY from env only — never hardcode a key in this file or in
  `claude mcp add`'s stored config with a key that has ever been pasted into a chat
  transcript; rotate first.** Register: `claude mcp add manus --transport stdio --env
  MANUS_API_KEY="$MANUS_API_KEY" -- ~/targets/_shared/manus_bridge/.venv/bin/python3
  ~/targets/_shared/manus_bridge/manus_mcp_bridge.py`, then restart Claude Code.

## REA (reverse-engineer-anything) + local node22 + jadx — added 2026-10-15 (_by: claude_)
- **node22** (REA requires node ^22.19 / ^24.11 / >=26; box node is v20.20.2, too old). Local,
  no sudo: `/home/RESEARCHER/targets/_shared/tools/node22/bin/node` (v22.23.3), npm 10.9.9. Do NOT put
  node22/bin on the global PATH (would shadow system node v20 for every other tool).
- **rea** (`rea-agents` 6.5.0, MIT) — global-installed under node22
  (`.../node22/lib/node_modules/rea-agents`). CLI wrapper pins node22:
  `/home/RESEARCHER/.local/bin/rea` (on PATH). Self-test = `rea mcp doctor` → `healthy: true`,
  207 tools / 6 prompts observed, stdio adapter, stderr empty (PASS 2026-10-15). `rea doctor`
  for engine readiness. The CLI is usable in-shell immediately.
- **REA as MCP (207 native tools)** registered USER scope (all projects/targets):
  `claude mcp add --scope user rea -- /home/RESEARCHER/targets/_shared/tools/node22/bin/node \
   /home/RESEARCHER/targets/_shared/tools/node22/lib/node_modules/rea-agents/scripts/rea.mjs --mcp`
  → `claude mcp get rea` = ✔ Connected. **Loads only at Claude Code STARTUP — needs a RESTART
  before the mcp tools appear in a session.** Remove: `claude mcp remove rea -s user`.
  (`.claude.json` backed up to `.claude.json.bak-rea-*` before the add.)
- **REA engine gaps (need sudo/apt or a specific jar, NOT installed):** hopper, ghidra
  (`GHIDRA_INSTALL_DIR`), ida (`REA_IDA_MCP_CONFIG`), REA's own jadx tool
  (`REA_JADX_MCP_JAR` = caller-supplied `jadx-headless-mcp 0.7.1` jar; REA won't download it).
  JS/web-bundle + many analysis tools work without them.
- **jadx 1.5.6** (standalone decompiler, Java 21 OK, no sudo): bin at
  `/home/RESEARCHER/targets/_shared/tools/jadx/bin/jadx`, symlinked `/home/RESEARCHER/.local/bin/jadx`
  (on PATH). Self-test `jadx --version` → `1.5.6` (PASS 2026-10-15). This is the normal jadx
  CLI (independent of REA's jadx-headless-mcp integration above).
