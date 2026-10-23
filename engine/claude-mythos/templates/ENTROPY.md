# ENTROPY — {PROG}

> Format + entropy of every identifier BEFORE any prediction/brute/fuzz (L2).
> entropy_gate.py reads this file: an identifier tagged high-entropy here (uuidv4 /
> 128-bit / random / ULID / nonce / crypto-random) BLOCKS brute/fuzz against it, so you
> pivot to structure (binding · race · leak channel · lifecycle) instead of burning hours.
> Only list what you have CONFIRMED (captured a real value + checked the format).

## Identifiers
| Identifier (param/field name) | Format / entropy | Predictable? | Pivot if dead |
|---|---|---|---|
| session_token | uuidv4 (128-bit random) | NO — prediction dead | binding / fixation / lifecycle |
| — | | | |

## Low-entropy / structured (prediction IS on the table)
- e.g. sequential numeric id, timestamp-derived, short base36 counter — these stay huntable.
