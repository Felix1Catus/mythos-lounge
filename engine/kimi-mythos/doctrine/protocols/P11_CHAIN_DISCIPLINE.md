# P11 CHAIN_DISCIPLINE — kills U3 (premature closure), U6 (overrotation)

**TRIGGER:** Every finding, at log time.

**RULE:** Every finding gets: floor (what's proven), ceiling (highest impact this primitive
could reach), missing-link (the single next probe). Escalate every primitive to its ceiling
before celebrating the floor. First hit of any vuln class → horizontal sweep of that class
across the mapped surface. "Not critical enough — chain or escalate" is the default
response to your own findings. Second-order variants (stored/reflected/deferred) are part
of the same class — test them before closing the cell.
