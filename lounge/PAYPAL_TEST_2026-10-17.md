# PROGRAM_68 lounge test — 2026-10-17 — what broke, what changed

## Collaboration correction (same day)

The first patch made seats quieter: prefix-lock the whole path, treat KILL as
"do not refire", persist at the end. That is the opposite of the table.

PROGRAM_68 receipts: grok3 stopped when dsclaude wrote "do not refire". dsclaude
stopped on mint-lock and a VERDICT that the ceiling was human-gated. Neither
answered the other's class with a different axis in the same minute.

Now: exact cell is mutex, sibling axes run together, bare `POST /graphql` is
too coarse, and KILL/ANOMALY/RESULT/VERDICT/PUSH fan into every other live
inbox as PUSH. `follow --wait` is the real-time read. A KILL is one axis.

Receipts: `/home/RESEARCHER/grok3.txt` and
`C:\Users\RESEARCHER\2026-10-17-163236-you-are-seat-dsclaude-prober-on-the-project-lou.txt`.

Hunt still found the TMC floor (UAT 338 / prod 150) and KILLed DOCUMENT_VERIFICATION
+ bankBranches. The **harness** leaked two honesty flags from dsclaude and a
heartbeat graveyard from both seats.

## Failures (quoted from the seats)

1. **String-matched claims.** dsclaude: `grok3's cell "POST /graphql DOCUMENT_VERIFICATION loosen" ≠ my "POST /graphql", so the string-claim didn't dedupe`. Both seats field-enumerated `UserUiConfiguration` at the same time.
2. **`token` exit 0 on deny.** dsclaude: `I fired past mint-lock twice — seatlib.py token exits 0 even on grant:false, so my token … && fire chains proceeded anyway.`
3. **`--op read` mint-locked the shared bucket.** `token --op read returned mint-lock wait_ms=22367`. `--op` treated any key as a 60s global mint.
4. **45s heartbeat death during think.** grok3 joined 20:09:59, SEAT-DOWN 20:14:14 (before any claim). dsclaude joined 20:11:52, dead 20:15:06 — their first think was 4m27s. grok1/2/4 joined and died the same way. Default launcher path did not start hb-loop (`--launch` missing). Role `PROBER--launch` was a glued flag.
5. **KILL appended junk to DEADENDS.md** (bullets under the table) instead of a dedicated log.
6. **Stale inbox GRANT** could match a later claim of the same cell (no `claim_seq`).
7. **VERIFY-ME** went to the other PROBER who was still on the same GraphQL family.
8. **dsclaude scripts in `/tmp`**, grok3 under `targets/PROGRAM_68/scripts/`.
9. **First action was a long STATE/widget-JS read** (grok3) before `claim`.

## Fixes shipped in this toolkit

| Fix | Where |
|---|---|
| Exact-cell mutex (sibling axes run together). Bare `POST /graphql` is too coarse, not a prefix lock. | `seatlib.cells_conflict` (equality) + `cell_too_coarse` + conductor DENY |
| `token` CLI **exit 1** when `grant` is false | `seatlib.py token` |
| `--op read` is not a mint; mint-lock only mutating ops / `--mint` | `is_mint_op` |
| `token --wait` blocks until grant (cap 120s) | CLI |
| Every seatlib command heartbeats | `_touch_hb` |
| `hb_dead_s` default **90** (was 45) | `lounge.json` + conductor |
| `--launch` is the documented start; without it, launcher prints WARNING | `seat_launcher.sh` `install.sh` |
| Strip glued `PROBER--launch` | launcher |
| OWNER stores `cell`; CLAIM-GRANTED carries `claim_seq` | seatlib + conductor |
| SEAT `resume=1` does not spam ROLE | conductor |
| KILL → `STATE/LOUNGE_KILLS.md` (not DEADENDS table junk) | conductor |
| VERIFY-ME skips seats holding an overlapping claim | `_least_loaded(..., cell=)` |
| `seatlib status` | CLI |
| Protocol rules 0–9 rewritten from the receipts | `LOUNGE_PROTOCOL.md` |
| Install smoke: overlap DENY + token exit 1 | `install.sh` |

## What the hunt itself got right

Board events, PREDICT, independent VERDICT of TMC 338/150, KILL with error class,
PROFILE positive control, scripts with WHAT-IT-PROVES headers (grok3). Keep those.

Do not file the PROGRAM_68 TMC floor until RESEARCHER says.
