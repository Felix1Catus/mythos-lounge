# P07 BOARD_DISCIPLINE — kills U11 (context-amnesia), U6 (overrotation)

**TRIGGER:** After every wave; before compaction/restart; after every resume.

**RULE:** STATE files updated after every wave: floor/ceiling/missing-link, active track,
next probe, negative results (disproven hypotheses are ASSETS — logged so never re-run).
Before compaction/restart: checkpoint pointer written
(`python3 ~/.kimi-code/mythos/checkpoint.py <prog> --next "<exact command>"`).
After resume: read the board in the same pass as the shot. A hunt that can't warm-boot from
disk in <2 minutes is misconfigured.
