# P09 DIVERGENCE_ENGINE — kills U12 (checklist-trap), U5 (circle)

**TRIGGER:** For any interesting endpoint, at mutation time.

**RULE:** Mutation is STRUCTURAL, not payload iteration. Generate across: type
(int→string→bool→null→array→object), sign/magnitude (0, negative, overflow, float,
scientific), encoding (URL, double-URL, unicode, normalization, case, whitespace/control
chars), structure (nesting, duplicate keys/HPP, array↔object, content-type swaps), method
matrix, version params (an ignored-looking enum can be the load-bearing differential),
coercion boundaries ("08", "8.0", "+8", tab). Loosen per doctrine: unpredicted behavior is
the TARGET. Known-payload wordlists are the floor, never the ceiling.
