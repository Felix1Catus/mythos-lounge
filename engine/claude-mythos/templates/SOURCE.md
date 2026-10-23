# SOURCE — {PROG}

> Source-first (M1/M2): the source IS published — READ/DIFF it, then probe only to CONFIRM.
> recon_diff.py blocks the FIRST live probe each session until DIFFED below is flipped to
> yes — so you don't black-box a target whose bugs are sitting in the diff.
> Delete this file if the target is genuinely black-box (no source).

DIFFED: no

## Source
- repo / tarball / package:
- fork vs upstream (M1):
- version N vs N-1 (M2 patch-gap — "incomplete fix for CVE-X" = the sibling the fix missed):

## Audited components (depth over breadth — mine ONE fully)
- [ ] component:
- [ ] server-controlled values used to size/index/bound/fetch/pick-alg, UNVALIDATED (M3):
- [ ] second-path authz inventory — BOLA/BFLA (M4):
- [ ] forgotten-auth sweep (M5) · secret-to-sink (M6):
