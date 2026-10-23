# UPGRADE LOG — MYTHOS + Lounge

Dated record of capability upgrades. Newest first. Every tool here is self-testing
(`--selftest` / embedded) and fails OPEN where it rides a live tool call.

---

## 2026-10-23 — `mythos` single command + code review gate

- **`mythos` / `shared/mythos.py`** — one command runs the whole front-end as a staged,
  resumable pipeline implementing the Command Success/Failure Contract: stages
  **A scope → B deps → C enumerate → D scan → E agent → F report**, each with an explicit
  status (PENDING/RUNNING/SUCCESS/WARNING/FAILED/SKIPPED). It computes the overall state from the
  stage ledger (not the last command), returns the contract exit codes (0/2/3/4/5/6/7/8/9/10),
  writes a machine-readable `run-manifest.json`, prints a terminal summary, and resumes from the
  first incomplete stage (`--resume`). An **invalid or unauthorized target is a hard stop** — no
  enumeration/scan/agent runs; `--authorized` is required for network stages.
  - **Auto-scope:** on target set it immediately writes `<target>` + `*.<target>` into
    `STATE/SCOPE.md` (idempotent), so wildcard scope is recorded up front.
  - **Agent prompt:** stage E generates the full target-specific context package
    `reports/AGENT_PROMPT.md` — scope, ranked surface, confirmed takeover/PHP2Shell findings,
    open leads, stage statuses, which skills to load, and the task directive.
  - Installed on PATH as `mythos` by `install.sh`. Acceptance tests: `mythos.py --selftest`
    (target validation, wildcard scope, invalid-target hard-stop, unauthorized PARTIAL, status
    calc, prompt sections, two-target isolation, resume — all offline; live-network cases
    documented). Added to `mythos_doctor` (now 17/17).
- **`shared/review.py`** — static review + self-test gate across the toolkit and hooks
  (AST/compile, bare-except / mutable-default / `== None` / debugger / unused-import lints, runs
  every `--selftest`). Ran it, fixed the findings (removed unused `json` import in `pow_detector`).

---

## 2026-10-23 — PHP2Shell (CVE-2026-109618 / CVE-2026-109619) detection + gated PoC

`shared/php2shell_check.py` — PHP2Shell is unauthenticated RCE in PHP's session.upload_progress
/ RFC1867 handler chained with an OOM-longjmp dangling-pointer bug (CVSS 9.2; PHP 5.4.0–8.5.11;
fixed 8.2.35 / 8.3.36 / 8.4.27 / 8.5.12). Refs: github.com/hypnguyen1209/php2shell ·
github.com/9bie/php2shell-bypass-aslr-exp · sansec.io/research/php2shell · wiz.io/blog/php2shell-php-rce.

- **Detection (safe, automated)** — single-GET PHP version fingerprint (Server / X-Powered-By /
  body) → precise per-branch vulnerable/patched classifier → `STATE/PHP2SHELL.md` +
  `PHP2SHELL_SIGNALS.ndjson`; `rank_surface` folds a VULNERABLE host as the confirmed CVE pair
  (CVSS 9.2) and it promotes to `LEADS.md`. Runs by default in `enum_pipeline.sh`
  (`--no-php2shell` to skip). Self-test: 16/16 version-matrix cases.
- **PoC (human-gated, never auto-fired)** — the exploit is a build-specific memory-corruption
  chain that crashes/respawns workers, so per doctrine it is human-gated: `--poc --target <url>
  --authorized` only writes a single-target plan with a benign proof token, pointing at the two
  reference PoCs and their Docker labs (validate in a lab first; benign marker `id`/`echo
  <token>` only; one target; file at the floor). It **refuses** without `--authorized` and
  **refuses** any out-of-scope target. The tool never executes an exploit or mass-targets.

Verified in WSL: doctor 16/16; classifier + regex + live fetch path confirmed; PoC gate refuses
without authorization and out-of-scope.

---

## 2026-10-22/23 — Enumeration phase, surface ranking, ops tooling, 12 bug-hunting hooks

### Bug-hunting hooks (12) — `engine/{kimi,claude}-mythos/`, wired in `hooks-config/settings.json`
Doctrine-enforcing guards on the Claude Code hook lifecycle; shared lib `mythos_hooklib.py`;
all fail-open. Self-test: `python3 <edition>/test_hooks.py` (52 assertions).

| # | hook | event | enforces |
|---|---|---|---|
| 1 | scope_sentry | PreToolUse | tendon 4 — block off-scope/excluded host |
| 2 | deadend_guard | PreToolUse | L3/P05 — block re-probing a logged infra gate |
| 3 | entropy_gate | PreToolUse | L2 — block brute of a high-entropy identifier |
| 4 | instrument_selftest_gate | Pre+Post | P03 — no trusting probelib before a PASS |
| 5 | secret_sink | Pre+Post | M6 — log secrets (redacted), block off-scope exfil |
| 6 | error_oracle | PostToolUse | P10 — status+class ledger, flag stage-flips |
| 7 | evidence_autolog | PostToolUse | P01/P14 — auto-save mutation-2xx/5xx/redirects |
| 8 | two_fail_loosener | PostToolUse | L1/P02 — nudge untried axes on 2nd identical class |
| 9 | liveness_watchdog | PostToolUse | P04 — halt on 401-after-authed; /25-req liveness |
| 10 | ceiling_gate | Stop | P11 — no ending a chain at the floor |
| 11 | recon_diff | PreToolUse | M1/M2 — no black-box probe of a source-available target until diffed |
| 12 | pow_detector | PostToolUse | divergence — flag PoW/signed-body/JS-challenge responses |

### Enumeration phase (bbot → ranked attack surface) — `shared/`
- **`enum_pipeline.sh <prog>`** — scope-gated bbot run (subdomain-enum + web probe + baddns
  takeover; `--vuln` nuclei, `--ports` portscan, `--passive`, `--top N`). Targets ONLY the
  in-scope roots from `STATE/SCOPE.md`.
- **`rank_surface.py <prog>`** — folds bbot's NDJSON events into a per-host **bug-likelihood
  score** (takeover ≫ nuclei-severity > auth-gated > naked-origin > hot-name > open-ports >
  cve-tech, minus a clone penalty). Writes `STATE/SURFACE_MAP.md` + promotes top-N into
  `STATE/LEADS.md`. Breadth feeds depth — not a spray. Wired into the `recon_pipeline` skill
  as Stage 3b (ENUMERATE) + 3c (RANK-SURFACE).
- **nuclei tech→CVE enrichment** (in `rank_surface.py`) — extracts **confirmed** CVE-IDs +
  CVSS from bbot's nuclei VULNERABILITY events (CVSS-scaled weight), and derives **suspected**
  CVEs from TECHNOLOGY product+version via a curated, overridable heuristic table
  (`~/targets/_shared/cve_rules.json` or `<prog>/STATE/cve_rules.json`; ships log4j, jQuery,
  Apache httpd, OpenSSL, WordPress, Bootstrap). Adds a CVEs column to `SURFACE_MAP.md`.
  Strongest with `enum_pipeline.sh <prog> --vuln` (runs nuclei). Self-test: 8/8.
- **JS secret/endpoint miner** — `shared/js_miner.py` fetches a live host's root HTML + same-origin
  JS (BFS, recursing into fetched JS for lazy chunks, capped, rate-limited, stdlib urllib,
  scope-gated). Extracts **secrets** (tiered HIGH/MED/LOW catalog — raw HIGH keys to a chmod-600
  file only, redacted everywhere else) and **endpoints** (/api,/v1,graphql, fetch/axios/.get
  targets, same-host URLs). Writes `recon/js/<host>.json` + appends `STATE/JS_SIGNALS.ndjson`,
  which `rank_surface.py` folds into the score (`js_secret_high`/`med`, `js_endpoint_unit`) and
  shows in `why`. `enum_pipeline.sh --mine-js` mines the top-N ranked hosts then re-ranks.
  Self-test 8/8 (offline extractor); live fetch path confirmed.
- **Subdomain-takeover confirmer** — `shared/takeover_check.py` (second-source over bbot baddns):
  resolves the CNAME chain (DNS-over-HTTPS, so no `dig`/dep needed; `dig` used if present),
  matches a curated, JSON-overridable service fingerprint table (S3, GitHub Pages, Heroku,
  Azure, Shopify, Fastly, Netlify, …), and fetches the host for the service's unclaimed
  fingerprint → VULNERABLE / LIKELY (dangling) / POTENTIAL / SAFE. Writes `STATE/TAKEOVER.md`
  + `STATE/TAKEOVER_SIGNALS.ndjson` (rank_surface marks those hosts takeover — top weight) and
  promotes VULNERABLE/LIKELY into `LEADS.md`. Runs by default in `enum_pipeline.sh` (disable
  with `--no-takeover`), then re-ranks. Self-test 6/6; live DoH resolution confirmed.

### Operations tooling — `shared/`
- **`mythos_doctor.sh`** — runs every self-test (hooks, instruments, enum, rank, coverage,
  report) + structural checks (settings.json valid, referenced hook files present, bbot
  installed) in one command. Exit 0 iff all structural pass. *Verified 13/13.*
- **`hunt_status.sh [prog]`** — one-screen cross-target dashboard: open leads, deadends,
  chain floor/ceiling, surface-map top-3, evidence count, last journal line; active target
  starred.
- **`coverage_map.py <prog>`** — P12 surface×class×status ledger from `ERROR_ORACLE.ndjson`;
  lists the HTTP methods NOT yet tried per surface (the empty cells = the next probe).
- **`report_draft.py <prog>`** — P14 assembler: stitches CHAIN_LEDGER floor/ceiling/missing +
  SCOPE + auto-captured evidence into `reports/DRAFT_<date>.md`, drafted at the proven floor.

### Install / packaging
- **`install.sh`** (bundle root) — one-command, idempotent, non-destructive installer for
  Linux/WSL/macOS: backup → copy trees → CRLF-normalize → chmod → merge hooks into
  `~/.claude/settings.json` (`--full-settings` for the rest) → fail-open `gate_hook.py` stub →
  optional `--with-bbot` (uv, managed py3.12, no sudo) → runs `mythos_doctor.sh`.
- Templates added: `ENTROPY.md`, `SOURCE.md` (activate `entropy_gate` / `recon_diff`).

### Verified in WSL (Ubuntu, py3.14 host; bbot on uv-managed py3.12)
`mythos_doctor.sh` → 13/13 pass. `test_hooks.py` → 52/52 (both editions). bbot 3.0.2 installed.
`rank_surface`/`coverage_map`/`report_draft`/`enum_pipeline` self-tests pass; `hunt_status`,
`coverage_map`, `report_draft` produce real output against a live target.

---

## Possible further upgrades (roadmap)
- ~~nuclei **tech→CVE** enrichment feeding `rank_surface`~~ — ✅ built 2026-10-23.
- ~~JS **secret/endpoint miner** folded into the surface score~~ — ✅ built 2026-10-23.
- ~~Dedicated **subdomain-takeover** confirmer (second-source over baddns)~~ — ✅ built 2026-10-23.
- **Scheduled re-scan** (cron/loop) with diff-alerting on new/changed hosts.
- `SURFACE_MAP` → **auto `TARGET_MODEL`** seeding (tech/auth hints per top host).
- Lounge: surface-map **cell claiming** so two seats split the ranked queue.
