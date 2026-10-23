# P10 ERROR_ORACLE — kills U12 (checklist-trap), U2 (instrument-trust)

**TRIGGER:** Every distinct error class observed.

**RULE:** Every distinct error class = one mapped internal branch. Maintain the ladder
(e.g. opaque 400 → specific mismatch → alternate required → malformed → success+action).
For each branch: what input shape selects it, what it reveals about the pipeline, what
adjacent branch is unprobed. The UNMAPPED branch is where the 0day is. 5xx/crash oracles
are leads, logged with repro, never discarded. For any 4xx/5xx: ask "what does this server
want?" before "is this blocked?" — replicate the real client's request byte-for-byte from
its own JS; vary method first (405 vs 400 vs 404 separates routing from parsing); test
whether omitting the param changes the error; only then sweep values.
