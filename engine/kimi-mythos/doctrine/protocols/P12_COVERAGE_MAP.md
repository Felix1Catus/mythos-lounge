# P12 COVERAGE_MAP — kills U12 (checklist-trap), U6 (overrotation)

**TRIGGER:** Per program, living ledger; before any coverage claim.

**RULE:** Per program, a living ledger: surface (endpoints/params) × classes (idor /
mutation / injection / xss / rce / xxe / lfi / sqli / ssti / ssrf / race / logic / authz /
authn / upload / deserialization / parser-diff / business-logic / leak) × status
(untested / tested-held / tested-weak / oracle-open). Never leave a tiny detail untested;
never assume. The map exists to find EMPTY cells and ANOMALOUS ones, not to feel complete.
Stale maps are lies — timestamp every cell. Coverage claims without timestamped cells and
a listed set of empty cells are claims, not coverage.
