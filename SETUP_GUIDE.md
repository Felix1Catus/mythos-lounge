# SETUP GUIDE — MYTHOS + Lounge

This installs the agent OS for a Unix-like box (Linux / WSL2 / macOS). The scripts assume
a `$HOME`-rooted layout. Wherever you see `RESEARCHER`, substitute your own username — the
bundle was scrubbed and uses `/home/RESEARCHER/...` as a placeholder in a few config paths.

## 0. Prerequisites

- `python3` >= 3.8, `bash`, `rsync`, `git`
- `flock` (util-linux) — lounge locking; `inotifywait` (inotify-tools) optional (poll fallback)
- An agent CLI with a hook system. Built for **Claude Code** (`SessionStart`, `PreToolUse`,
  `PreCompact`, `Stop` hooks + `~/.claude/settings.json`). Any CLI with equivalent lifecycle
  hooks works; you wire the same scripts to the equivalent events.

## 1. Place the trees

The scripts reference fixed home paths. Easiest is to mirror the original layout:

```bash
# from inside the unpacked bundle:
mkdir -p ~/.kimi-code ~/.claude ~/.grok ~/targets/_shared

cp -r engine/kimi-mythos      ~/.kimi-code/mythos
cp -r engine/claude-mythos    ~/.claude/mythos
cp -r engine/grok-rules/*     ~/.grok/rules/            # CRITICAL_HUNTER.md, HUNTER_V5.md
cp -r engine/skills           ~/.claude/skills          # 25 skills
cp -r lounge                  ~/targets/_shared/lounge
cp    shared/*                ~/targets/_shared/

cp    engine/CLAUDE.core.md   ~/.claude/CLAUDE.md       # the always-loaded core
cp    engine/MYTHOS_CLAUDE_OS.txt ~/MYTHOS_CLAUDE_OS.txt
chmod +x ~/.kimi-code/mythos/*.sh ~/.claude/mythos/*.sh ~/targets/_shared/lounge/*.sh ~/targets/_shared/*.sh 2>/dev/null
```

> If you want a different root than `~/.kimi-code` / `~/.grok`, grep the scripts for those
> paths and adjust — they are hardcoded in a handful of `session_start.sh` / doctrine lines.

## 2. Wire the hooks

`engine/hooks-config/settings.json` shows the exact hook block. Merge its `"hooks"` section
into your `~/.claude/settings.json` and replace `/home/RESEARCHER/` with your `$HOME`:

```bash
sed "s#/home/RESEARCHER/#$HOME/#g" engine/hooks-config/settings.json > /tmp/mythos-settings.json
# then merge /tmp/mythos-settings.json "hooks" into ~/.claude/settings.json (jq or by hand)
```

Hooks and what they do:
| Event | Script | Purpose |
|---|---|---|
| SessionStart | `mythos/session_start.sh` | print the creed + warm-boot pointer into context |
| PreToolUse (Bash) | `mythos/pretooluse_guard.py` | safety guard + auto-journal every tool call |
| PreCompact | `mythos/precompact.sh` | checkpoint before context is summarized |
| Stop | `mythos/stop_guard.sh` / `persist_nudge.sh` | nudge "did you PERSIST?" before ending |

### Bug-hunting hooks (12, wired in `hooks-config/settings.json`)

Doctrine-enforcing guards that travel with the `mythos/` dir (the `cp -r` above copies them).
`mythos_hooklib.py` is their shared library; `active_target` is resolved next to the script,
so the same files work in both the kimi and claude editions. All fail OPEN (a parse/IO error
never blocks a tool call).

| Hook | Event | Doctrine | Action |
|---|---|---|---|
| `scope_sentry.py` | PreToolUse | tendon 4 | BLOCK a request to an out-of-scope/excluded host (reads `STATE/SCOPE.md`) |
| `deadend_guard.py` | PreToolUse | L3 / P05 | BLOCK re-probing a logged L3 infra gate / already-tried method (`DEADENDS.md`) |
| `entropy_gate.py` | PreToolUse | L2 | BLOCK brute/fuzz of an identifier logged high-entropy in `STATE/ENTROPY.md` |
| `instrument_selftest_gate.py` | Pre+PostToolUse | P03 | BLOCK trusting probelib before a self-test PASS this session |
| `secret_sink.py` | Pre+PostToolUse | M6 | log captured secrets (redacted, sha256) + BLOCK exfil of one to an off-scope host |
| `error_oracle.py` | PostToolUse | P10 | log status+class to `ERROR_ORACLE.ndjson`; flag a same-status class flip |
| `evidence_autolog.py` | PostToolUse | P01/P14 | auto-save req/resp of mutation-2xx / 5xx / redirects to `evidence/auto/` |
| `two_fail_loosener.py` | PostToolUse | L1 / P02 | on the 2nd identical class per surface, nudge the untried axes |
| `liveness_watchdog.py` | PostToolUse | P04 | nudge on first 401/403 after an authed req, and every ~25 authed reqs |
| `ceiling_gate.py` | Stop | P11 | BLOCK ending with a proven floor but no ceiling/missing-link in `CHAIN_LEDGER.md` |
| `recon_diff.py` | PreToolUse | M1/M2 | BLOCK the first live probe of a source-available target (`STATE/SOURCE.md`) until diffed |
| `pow_detector.py` | PostToolUse | divergence | flag a proof-of-work / signed-body / JS-challenge response — intercept the SPA's submit, don't guess envelopes |

`entropy_gate`, `secret_sink` and `recon_diff`'s block paths stay dormant until
`STATE/ENTROPY.md` / `STATE/SCOPE.md` / `STATE/SOURCE.md` are filled — zero friction before
then. Self-test: `python3 test_hooks.py` (52 assertions: block/allow, side-effects, and a
garbage-stdin fail-open smoke for all 12).

### Enumeration phase (bbot → ranked attack surface)

`shared/enum_pipeline.sh` + `shared/rank_surface.py` add a big, scope-gated enumeration stage
that feeds the hunt a ranked surface instead of a flat host list (wired into the
`recon_pipeline` skill as Stage 3b/3c).

Install bbot without sudo (works even on a system Python too new for bbot — uv fetches its own):
```bash
uv tool install bbot --python 3.12
```
(If `uv` is absent: `curl -LsSf https://astral.sh/uv/install.sh | sh`.)

Run it (targets ONLY the in-scope roots from `STATE/SCOPE.md`):
```bash
bash ~/targets/_shared/enum_pipeline.sh <prog>
```
Flags: `--vuln` (nuclei), `--ports` (portscan), `--passive` (no active web), `--top N`. It
runs bbot (subdomain-enum + web probe + baddns takeover), then `rank_surface.py` scores every
host by bug-likelihood → `STATE/SURFACE_MAP.md` + a top-N auto-block in `STATE/LEADS.md`. Score
weights live in `rank_surface.py`. Self-test: `bash ~/targets/_shared/enum_pipeline.sh --selftest`.

## 3. Scaffold a target

```bash
bash ~/.kimi-code/mythos/newtarget.sh myprogram
# creates ~/targets/myprogram/{STATE,scripts,notes,results,evidence,recon,reports}
# STATE/ seeded from templates: SCOPE, TARGET_MODEL, LEADS, CHAIN_LEDGER, RESUME, GAP_PLAN, DEADENDS
```

Fill `STATE/SCOPE.md` with the program's **authorized** scope before probing anything.

Daily use:
```bash
bash ~/.kimi-code/mythos/mtarget.sh myprogram   # set active target
bash ~/.kimi-code/mythos/resume.sh myprogram    # warm-boot: checkpoint + journal tail + re-verify
```

## 4. Lounge (multi-agent, optional)

```bash
bash ~/targets/_shared/lounge/install.sh --program myprogram --seats 2
bash ~/targets/_shared/lounge/watch_feed.sh --program myprogram   # live board
bash ~/targets/_shared/lounge/stop.sh --program myprogram
```

`seatlib.py` is the per-seat API (claim a cell, post a hypothesis, reflect, take next).
Read `lounge/MACHINE.md` (GROUND → hypo → shot → reflect) and `lounge/LOUNGE_PROTOCOL.md`.

## 5. Verify the install

```bash
python3 ~/targets/_shared/probelib.py            # self-test must PASS before you trust it
bash    ~/targets/_shared/lounge/test_lounge.py  # lounge unit test
```

## Notes for the developer picking this up

- **The doctrine is the product.** `engine/CLAUDE.core.md` + `grok-rules/*.md` encode years of
  earned rules (ground-truth-first, kill-criteria, server-sentence-same-pass, P01–P14). Read
  them before refactoring scripts — the scripts exist to enforce the doctrine.
- **Everything is files.** No database. State, memory, journals (excluded from this bundle),
  and findings are all plain text/ndjson so any agent or human can read them.
- **Example receipts were scrubbed** to opaque `PROGRAM_xx` tokens — the mechanism is intact,
  the target identity is not. See `REDACTION_NOTES.md`.
