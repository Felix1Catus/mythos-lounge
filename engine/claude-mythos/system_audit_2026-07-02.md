# SYSTEM AUDIT — RESEARCHER's Claude / MYTHOS operating setup — 2026-07-02

Probe-backed (every claim below was run, not remembered). Auditor: Claude Fable 5, MYTHOS OS.
Scope: the box, the 3-account Claude config, the MYTHOS framework, memory stores, targets workspace, credential hygiene.

## VERDICT
Mature, well-instrumented single-operator research rig. The account1 framework is genuinely well-engineered
(versioned OS, safety guard, persist discipline). **Every real weakness is CONFIG DRIFT / CONSISTENCY, not design:**
the 3 accounts have drifted apart, memory stores diverged and one overflows its own load budget, account3 is
unconfigured, and there are loose ends (a leaked API key, 2 abandoned sessions). Nothing on fire; several things quietly degrading.

## 1. BOX / ENV
- WSL2 k6.18, 4 vCPU, **11,808 MB RAM** (the documented OOM ceiling). Now: 10 GB PROGRAM_11 — fine. Disk 1 TB, 9% used — ample. Load 0.3.
- **4 `claude` processes:** 2 active (incl. this session), **2 SUSPENDED `claude --continue` from Jun 29 (STAT Tl, ~790 MB RSS combined, PIDs 1271 & 1169)** — Ctrl-Z'd and abandoned 3 days. Dead weight on an OOM-prone box. FLAG only (don't auto-kill siblings — feedback rule).

## 2. MULTI-ACCOUNT ARCHITECTURE (biggest drift)
| acct | model | hooks | outputStyle | switchModelsOnFlag | CLAUDE.md | mem files |
|---|---|---|---|---|---|---|
| .claude (1) | claude-fable-5 (fixed today) | full 4 | MYTHOS | false | present | 119 |
| .claude-account2 | claude-opus-4-8 | full 4 | MYTHOS | **unset → ON** | present | 103 |
| .claude-account3 | **claude-fable-5[1m] CORRUPT** | **NONE** | none | unset | **ABSENT** | 16 |
- **account3 is essentially unconfigured**: no OS, no hooks (⇒ no safety guard), corrupt model → silently runs Opus. Launching `claude3` = dangerous-perms mode with ZERO MYTHOS safety net.
- **account2 never got** account1's `switchModelsOnFlag:false` / effort / skipAutoPerm hardening — drift.
- The `/model` `[1m]` corruption hit account1 (fixed) AND account3 (still corrupt).

## 3. PERMISSIONS POSTURE (deliberate, high-trust, high-blast-radius)
All 3: `permissions.defaultMode = bypassPermissions` + `skipDangerousModePermissionPrompt:true`. Every tool auto-runs, no prompts — a conscious velocity choice for autonomous hunting. The **PreToolUse safety guard is the one backstop** (validated: returns `ask` on `rm -rf /` / modprobe / core_pattern; fail-open on parse error). **BUT account3 has bypassPermissions WITHOUT the guard = unguarded dangerous mode** — the one genuinely unsafe corner.

## 4. MYTHOS FRAMEWORK HEALTH (the strong part)
- CLAUDE.md OS: 10 sections, mirrored account1↔2 (parity OK). Manual 1003 lines. 5-slot priority queue present. All hook scripts exist + executable. Safety guard solid. Well-built.
- Gap: framework lives only on account1/2; account3 bare.
- Logs grow slowly (persist_nudge 34 KB, safety 9.9 KB) — fine, unbounded, trivial to rotate later.

## 5. MEMORY SYSTEM (integrity issue)
- 3 stores DIVERGED: **119 / 103 / 16** files. Loaded MEMORY.md header claims *"Both stores synced to parity"* — **FALSE** (those disagree).
- **account2 MEMORY.md = 26,058 B, OVER the ~24 KB load budget the OS itself documents** ⇒ per your own rule it "only partially loads and entries silently vanish." account2 is dropping memory entries right now. account1 (19.7 KB) is safe.

## 6. CONFIG DUPLICATION / ORPHANS
- THREE CLAUDE.md files: `~/.claude/CLAUDE.md` (the OS — loads); `~/CLAUDE.md` (16.7 KB "Workspace — RESEARCHER Hassan" bug-bounty context — **ORPHANED: does NOT load in cwd /mnt/c/Users/RESEARCHER**, which isn't under /home/RESEARCHER); account3 none. Verify ~/CLAUDE.md isn't context you assume is loading.
- cwd `/mnt/c/Users/RESEARCHER/.claude/` is a 4th config layer (agents, agent-memory, settings.local.json 164 B).

## 7. TARGETS WORKSPACE (7.1 GB, 24 targets)
- Value concentration + executive-doc-overclaim pattern already documented (trust per-target floors, not cross-doc ceilings — see CLAUDE_AUDIT_OF_KIMI_2026-07-01.md).
- **1,012 credential-shaped files**, mostly stale `PROGRAM_93/archive/results*` scan residue; **NONE in git** (only `.git` = `misc/odoomap` third-party tool clone) ⇒ no push-exposure. Still a large plaintext-cred footprint on the Windows-backed FS; purging stale archives shrinks exposure + reclaims space.

## 8. CREDENTIAL HYGIENE
- GOOD: SSH keys 600; `~/.aws` symlink resolves empty; no JWT/AWS keys in history/env; `.claude.json` 600 with oauthAccount; findings not in git.
- FIX: **`DEEPSEEK_API_KEY` plaintext in `~/.bashrc` (line 138)** (also check `.bashrc.backup`) — rotate + move to a chmod-600 file sourced at runtime.
- Standing exposures: the permissive perms posture + Windows-mounted target creds.

## PRIORITIZED RECOMMENDATIONS (decision board)
AUTONOMOUS (Claude can do on your go):
1. Fix account3 `[1m]` model + wire MYTHOS OS/hooks/output-style into it (or document it as deliberately bare).
2. Reconcile account2 config to match account1 (switchModelsOnFlag:false, effort, skipAutoPerm).
3. Trim account2 MEMORY.md < 24 KB (stop silent entry loss); fix/remove the false "parity" claim.
4. Purge stale `PROGRAM_93/archive/*` cred residue (space + exposure) — after you confirm it's not needed.
HUMAN-OWNED:
5. Rotate the DeepSeek key (you hold the account).
6. Kill/resume the 2 suspended Jun-29 sessions (PIDs 1271, 1169) — Claude won't touch sibling sessions.
7. Decide account3's purpose (bare experimental vs full third rig).

---

## EXECUTED 2026-07-02 (post-audit — RESEARCHER: "the rest yes do it"; secrets/creds left untouched by request)
All probe-backed & validated. Backups: `~/.claude/backups/os_2026-07-02_reengineering/*.bak`.
1. **account3 → full Fable sibling.** model `[1m]`→`claude-fable-5`; added the MYTHOS OS (CLAUDE.md now present + identical to acct1, outputStyle, 4 hooks **including the PreToolUse SAFETY GUARD** → closes the unguarded-dangerous-mode hole), switchModelsOnFlag:false, effort:xhigh, skipAutoPerm, statusline, plugin. Guard positive-controlled: returns `ask` on `modprobe`. ✓
2. **account2 hardening reconciled** to acct1: added switchModelsOnFlag:false + effortLevel:xhigh + skipAutoPermissionPrompt:true. ✓
3. **account2 MEMORY.md overflow fixed:** 26,058B → 23,226B; **105/105 pointers preserved**, 41 long hooks truncated (scratchpad/compress_memory_index.py, CAP=160). Now loads fully. ✓
4. **False "synced to parity" corrected** in BOTH acct1+acct2 indexes → real counts 119/105/15, "treat each as its own brain." ✓

STATE NOW: all 3 accounts — model set, switch=False, effort=xhigh, skipAuto=True, MYTHOS style, 4 hooks; CLAUDE.md identical (single md5); all MEMORY.md <24KB.
NOT done (human-owned / declined): #4 purge stale creds (left per "keep creds alone"); #5 rotate DeepSeek key.
DONE later this session: #6 killed suspended PIDs 1271/1169 (RESEARCHER-authorized 2026-07-02; SIGKILL, verified reaped, active sessions 63956/64048 untouched); #7 RESOLVED — account3 wired as a full rig.
