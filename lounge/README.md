# PROJECT LOUNGE

Two hunter agents, one enrolled program, same minute. Exact cell is mutex.
Sibling axes run together. The board is the shared brain.

## Start

```
dsclaude prober PROGRAM_71          # or: grok3 prober PROGRAM_71
bash open.sh grok3 prober PROGRAM_71   # tmux session lounge-grok3
```

If `no lounge at …/LOUNGE`:

```
bash ~/targets/_shared/lounge/install.sh --program PROGRAM_71
```

## Watch / stop

```
bash ~/targets/_shared/lounge/watch_feed.sh --program PROGRAM_71
bash ~/targets/_shared/lounge/stop.sh --program PROGRAM_71
```

Stop kills conductor + hb-loops. Ctrl-C the agent terminals yourself.

## Read

1. `MACHINE.md` — GROUND → hypo → shot → reflect
2. `LOUNGE_PROTOCOL.md` — claims, token, GATE
3. `PAYPAL_TEST_2026-10-17.md` — why exact mutex, not prefix-lock
4. `SELF_UPGRADE_2026-10-18.md` — this morning's upgrade record

## Seat commands

```
export LOUNGE_DIR=~/targets/<prog>/LOUNGE SEAT_ID=grok3
python3 seatlib.py board
python3 seatlib.py claim --cell 'METHOD /path AXIS'   # exit 1 if denied
python3 seatlib.py token                               # exit 1 if empty
python3 seatlib.py reflect --cell '...' --klass '...' --sibling 'METHOD /path AXIS'
python3 seatlib.py follow --wait 2
```

`--class` is an alias of `--klass`. Header `X-PP-BB: HackerOne-RESEARCHER` is PROGRAM_68-only.

A leftover `~/.lounge/*.role` does not join a solo grok. `LOUNGE_SEAT` or `LOUNGE_JOINED=1` is required.
