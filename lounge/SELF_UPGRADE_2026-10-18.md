# Lounge self-upgrade — 2026-10-18

Operator: RESEARCHER. Role: bug bounty hunter. Scope: PROJECT LOUNGE toolkit + hooks it owns.
Autonomy: full. Approver for risky items: RESEARCHER.

## Mission Statement

The lounge is the table that lets two hunter agents work the same enrolled program
in the same minute without firing the same request. Good work is a sibling axis
that lands on the peer's last error class before the turn dies. Never: hijack a
solo hunt, leak secrets into `feed.md`, file a report, or freeze a seat on a
status code.

Settings used: ROLE=hunter · MISSION=Criticals/0days/chains · SCOPE=lounge toolkit,
bashrc aliases, mythos hooks that `exec`/`call` live_talk · AUTONOMY=full.

## Inventory Map (one line, one verdict)

```
instructions/
  LOUNGE_PROTOCOL.md           KEEP   exact-cell mutex, GATE, no submit
  MACHINE.md                   TUNE   --klass aligned this morning
  PAYPAL_TEST_2026-10-18.md    KEEP   receipts that earned the mutex
  AUDIT_2026-10-18.md          KEEP   F1–F7 record
  README.md                    ADD    no index at toolkit root
code/
  seatlib.py                   TUNE   comment still says prefix-overlap
  conductor.py                 TUNE   _least_loaded hard 30s vs hb_dead_s 90
  live_talk.py                 KEEP   lounge_session gate (F3)
  test_lounge.py               TUNE   does not lock F1–F6
scripts/
  install.sh                   TUNE   pid = kill -0 only (F8)
  go.sh                        TUNE   same pid check; sleep 0.2
  seat_launcher.sh             TUNE   grok1 omits --cwd (F16)
  open.sh                      KEEP   tmux wrapper around go.sh
  stop.sh                      KEEP   added this morning
  watch_feed.sh                KEEP
  mythos_gate.sh               KEEP   LOUNGE_DIR required
hooks/ (owned by lounge via live_talk)
  context_router.sh grok/claude/dsclaude  KEEP  no longer exec (F2)
  stop_guard.sh same                      KEEP  exit 2 only on peer move
entry/
  ~/.bashrc _lounge_up / grok3 prober     KEEP
runtimes/
  targets/PROGRAM_71/LOUNGE         KEEP   conductor 11095 alive (do not hunt)
  targets/PROGRAM_68/LOUNGE        TUNE   stale conductor.pid 1532800
  targets/PROGRAM_56/LOUNGE      KEEP   json only; do not touch hunt STATE
data/
  ~/.lounge/{seat}.seen        TUNE   legacy global files still present
binaries/                      KEEP   python3 stdlib only; no extra pkgs
```

## Top findings (remaining after F1–F7)

| # | Verdict | I | E | R | Evidence |
|---|---|---|---|---|---|
| 1 | ADD | H | L | L | `test_lounge.py` does not bash -n install.sh, does not assert hooks lack `exec live_talk`, does not assert `lounge_session()` false without env. Same class of miss as PROGRAM_68 `token` exit 0. |
| 2 | FIX | M | L | L | `install.sh`/`go.sh` treat any live PID as conductor. PROGRAM_68 1532800 is dead; a reused PID would skip start. `stop.sh` already checks `conductor.py` in argv. |
| 3 | TUNE | M | L | L | `seat_launcher.sh` grok1 has empty `GROK_CWD`; `go.sh` idle path always `--cwd /home/RESEARCHER`. |
| 4 | TUNE | M | L | L | `_least_loaded` hb window is 30s; `hb_dead_s` is 90. VERIFY-ME skips a thinking seat (PROGRAM_68 receipt #7). |
| 5 | TUNE | L | L | L | `seatlib.py` section comment still says `prefix-overlap`. |
| 6 | ADD | M | L | L | No README. Fresh seat finds PROTOCOL via launcher prompt only. |
| 7 | TUNE | L | L | L | `go.sh` waits 0.2s after conductor start; first claim can be INCONCLUSIVE. |
| 8 | KEEP | — | — | — | Exact mutex, token exit 1, `--op read` not mint, inotify, KILL→LOUNGE_KILLS, F1–F7 patches. |

Needs approval (not this run): DeepSeek key in process env; rewriting conductor to not scan full jsonl; deleting PROGRAM_68/PROGRAM_56 lounge data; changing hook deny lists.

## Batches (this run)

B1 Snapshot toolkit → `~/targets/_shared/backups/lounge_20261018_selfupgrade/`
B2 Tests that lock F1/F2/F3/F6
B3 Conductor pid = alive AND argv contains conductor.py (install + go)
B4 grok1 `--cwd /home/RESEARCHER`; go.sh wait until conductor alive
B5 `_least_loaded` uses `hb_dead_s`
B6 README + comment + install footer names `stop.sh`

Verify: `python3 test_lounge.py`, `bash -n` scripts, grep hooks have no `exec live_talk`.
Undo: copy snapshot back.

## Change log (this run)

| Batch | What | Why | Verify | Undo |
|---|---|---|---|---|
| B1 | Snapshot `backups/lounge_20261018_selfupgrade/` | reversible | 16 toolkit files + 6 hooks | — |
| B2 | Tests: bash -n, no `exec live_talk`, `lounge_session()`, `--class`, `_least_loaded` 45s peer | lock F1–F6 so they cannot regress | `python3 test_lounge.py` OK | restore `test_lounge.py` |
| B3 | `install.sh` / `go.sh` conductor alive = pid live AND argv contains `conductor.py` | reused PID would skip start | bash -n; helper present | snapshot |
| B4 | launcher grok1 `--cwd /home/RESEARCHER`; go.sh waits up to 1s for conductor | grok1 was starting on `/mnt/c`; 0.2s race | grep GROK_CWD | snapshot |
| B5 | `_least_loaded` uses `hb_dead_s` (90) | VERIFY-ME skipped a 45s think | test_least_loaded_uses_hb_dead_s | snapshot |
| B6 | `README.md`; install footer `stop.sh`; seatlib comment exact-mutex | findable, docs=code | README exists; prefix-overlap gone | snapshot |

Golden: `OK lounge tests` (inotify 45.9ms). Hooks: no `exec live_talk`. PROGRAM_71 conductor 11095 still the pre-B5 process (do not restart under the operator).

## Protected (KEEP)

- Exact-cell mutex, coarse DENY, token exit 1, `--op read` not mint
- `hb_dead_s=90`, `--launch` hb-loop, `claim_seq`, KILL→LOUNGE_KILLS
- F1–F7 from the morning audit (install `||`, live_talk additive, session gate, per-program seen, PROGRAM_68-only X-PP-BB, `--klass`)
- `open.sh`, `watch_feed.sh`, `mythos_gate.sh`, bashrc `_lounge_up`
- Live PROGRAM_71/PROGRAM_68/PROGRAM_56 hunt STATE

## Needs approval

- DeepSeek key in dsclaude process env
- Streaming/tailing `events.jsonl` instead of full parse every cycle
- Deleting PROGRAM_68 stale pid / PROGRAM_56 lounge json
- Changing PreToolUse deny list

## Open questions

- Will the next PROGRAM_71 pair actually `follow` + `reflect`, or still hunt solo inside the lounge?
- Should `stop.sh` also `tmux kill-session -t lounge-<seat>`? Operator said shutdown tmux yesterday; script leaves terminals.

## Next audit

- After the next multi-seat hunt: did INCONCLUSIVE still happen? did VERIFY-ME pick a 45s-old peer?
- Re-run `python3 test_lounge.py` after any hook edit
- Cadence: light check on `install.sh` parse + hook `exec` every lounge change; full after the next hunt that uses two seats

## Phase 8

Scoreboard this upgrade: 6 batches, 0 rollbacks, 0 guardrail weakenings, 0 live-STATE writes, PROGRAM_71 conductor left running.
