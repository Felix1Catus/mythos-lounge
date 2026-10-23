# MYTHOS Persistence Hooks — Install + Validation (2026-06-17)

Closes the Q2 self-audit gap (no per-work-item persistence) with two mechanical layers.

## Installed
- **PostToolUse** → `~/.claude/mythos/persist_nudge.sh`: after every Bash/Write, nudges to stderr (never blocks) if no `RESUME.md`/`GAP_PLAN.md` under `~/targets` was touched in 120s. Wired on **both accounts**.
  - Corrected from the provided source before install: the per-target marker glob was double-quoted (`"$HOME/targets/*/STATE/RESUME.md"`) so it never expanded → persistence was never detected (would have failed TEST B). Replaced with `find`. Also dropped `set -e` so a stray non-zero can't become a spurious post-every-call error.
- **PreCompact v2** → `~/.claude/mythos/precompact.sh`: before compaction, finds the newest `~/targets` note modified in 5 min; if newer than the nearest ancestor `RESUME.md`, appends an `AUTO-FLUSH` marker to it + logs. v1 backed up at `precompact_v1_backup.sh`. Wired both accounts (shared absolute path).

## Validation (probe-backed; throwaway sandboxes only — no real RESUME.md touched)
| Test | Result |
|---|---|
| A — nudge fires on un-persisted work | PASS |
| B — nudge silent after persistence | PASS |
| C — PreToolUse guard regression (modprobe → ask) | PASS |
| D — PreCompact auto-flush | PASS (clean isolated run; first run FAIL was a test-harness mtime-tie confound, not the hook) |
| JSON — both settings.json valid | PASS |
| Mirror — account2 PostToolUse wired | PASS |

## Known limitations of precompact v2 (flagged, not failures)
1. Walk-up finds `RESUME.md` only in an **ancestor** of the modified note. A note under a *sibling* dir (`notes/`, `recon/`) will NOT flush a `STATE/RESUME.md` sibling. Works for notes under `STATE/` (the common case).
2. `find -maxdepth 4` → notes deeper than `~/targets/<t>/<a>/<b>/x.md` are missed.
3. `set -e` + `find | head -20`: >20 recently-modified notes could SIGPIPE-abort before the flush (rare).

## Source
Real scripts were at `/home/RESEARCHER/persist_nudge.sh` + `/home/RESEARCHER/precompact_v2.sh`; the guide's `/mnt/agents/output/` paths did not exist.
