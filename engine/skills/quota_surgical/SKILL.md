---
name: quota_surgical
description: When remaining quota is low, fire the cheapest autonomous misses first — no new recon theatre, no wide batteries. Use when the user says "quota", "10% tokens left", "LAST-QUOTA", "cheapest-first", "surgical wave", or "make the most out of it".
user-invocable: true
---

# quota_surgical — cheapest miss first

## Trigger
The user names remaining quota, a percent of tokens left, "LAST-QUOTA", "cheapest-first", or "surgical wave".

## Procedure
1. Stay on the live target. Do not open a new program.
2. Rank remaining probes by (expected Critical-shape) / (requests × time). Prefer one JS-faithful request over a battery.
3. Fire the cheapest miss that is not in DEADENDS. One variant. Read the class. Persist. Next cheapest.
4. Skip anything that needs a human gate, a second account, a widget token, or a paid write.
5. If the cheapest miss is blocked, name the blocker in one line and take the next cheapest. Do not spend the rest of quota restating the wall.

## Rules
- No new recon dump. No skill-loading ceremony. No report drafting unless a chain is already complete.
- Persist after every probe. The next session must resume from disk, not from this chat.
