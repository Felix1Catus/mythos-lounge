# P06 PROBE_BUDGET — kills U10 (rate/scope indiscipline)

**TRIGGER:** Payment/state-mutating endpoints; any spray; any 429.

**RULE:** Payment/state-mutating endpoints: one attempt per mint, ≥60s spacing, 429 →
≥2min cool, board entry BEFORE the next attempt. Cheap discriminators before expensive
sprays. Probes are finite — spend only on new primitives (P02). Never mass-mint, never
mass-enum; low-and-slow.
