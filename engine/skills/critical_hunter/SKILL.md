---
name: critical-hunter
description: >
  CRITICAL catch/analyze/break playbook for authorized bug bounty. Use when hunting for
  Critical impact, when a finding is "not critical enough", or when user says chain/escalate.
---

# Critical Hunter Skill

**SoT playbook:** `~/.grok/memory/feedback/feedback_critical_hunter.md`  
**Home rule:** `~/.grok/rules/CRITICAL_HUNTER.md`  
**Agents:** `critical-hunter`, `chain-breaker`, `surface-re`  
**Commands:** `/critical` · `/chain` · `/error-protocol`

## When to use
- Starting or resuming a program hunt with Critical as the goal
- User says "not critical enough", "chain", "escalate", "ATO", "RCE"
- Floor finding exists and ceiling is still probeable

## Procedure
1. Execute the prompt. Brain: `~/.grok/rules/CRITICAL_HUNTER.md`. Do not open another doctrine file first.
2. **CATCH** the client's real bytes and the server's current error class. That is the recon.
3. **ANALYZE** the stage the class names. Same HTTP status + later class = the check between them was skipped.
4. **BREAK** — if the crack is already named, send that one request. Seven axes only while the class is still the author's.
5. **PERSIST** the class ladder. Chain the floor to the ceiling in the same pass.
6. Report only the proven floor. A status-only dead log is reopened. An infra identity gate with no class flip stays dead.

## Anti-patterns
- Polishing Mediums while a Critical link is open
- Status-code closure / first-403-as-final
- Trusting prior DONE/BLOCKED without re-probe
- Pre-conceding impact in report openers
