# Harness tiers and right-sizing

## Why tiers

The reference harness this skill distills was grown over months on a high-stakes, parallel-agent project — and its own governance docs warn that installing that mass up front is the same scope-sink disease the harness prevents. Its design history is explicit: mechanisms were added in response to *named, dated incidents*, not speculatively. So: install the smallest tier the answers justify, and let the audit's retro step grow it when pain is felt.

## Tier selection

Ask (fold into the setup interview, don't run as a separate questionnaire):

1. Expected duration — days, weeks, or open-ended?
2. Who works on it — one human, human+agent, multiple agents in parallel?
3. Stakes — throwaway/exploratory, internal tool, or production with real users/money?
4. Is there a vendored, pinned, or generated codebase that must not be hand-edited? (→ upstream trait)
5. Will work ever proceed unattended (agent-driven runs, CI-triggered work)?

Mapping: days + throwaway → **S**, even when Claude does the work — "agent-driven" below means *unattended or CI-triggered* runs, not "an agent is helping". Weeks, or unattended/CI-triggered agent work, or production stakes → **M**. Open-ended + parallel agents + high stakes → start at **M** and grow toward **L** via retro. Don't install L machinery day one unless the user explicitly insists — then record the override in DECISIONS.md with a revisit_when, like any other hard-stop override.

Confirm the tier with the user before installing.

## Tier S — docs and discipline (every project)

| Component | Job | Template |
|---|---|---|
| CLAUDE.md | Bootstrap pointer, ≤40 lines: current focus + non-goals, core rules block, context hygiene, source-of-truth map. A pointer — never a copy of other docs. | `CLAUDE.md` |
| docs/PRD.md | What to build. Requirements carry **stable clause IDs** (`R3.c2`) so other docs cite instead of copy. The out-of-scope/cut list is load-bearing: scope creep is caught by diffing work against it. | `PRD.md` |
| docs/HARNESS.md | How we work: goals + **named anti-goal**, work-item states and what evidence each transition needs, the check command, what is deliberately NOT governed, graduation log. | `HARNESS.md` |
| docs/UNKNOWNS.md | The quadrant register: open decisions with toggles, assumptions awaiting confirmation, blindspot findings, resolution log. Re-read at every audit. | `UNKNOWNS.md` |
| docs/PLAN.md | Volatility-sorted plan: likely-to-change decisions at top with toggles, routine work collapsed below, every step with `→ verify:`. Deviation log at the bottom. | `PLAN.md` |
| docs/DECISIONS.md | Dated decisions: context, choice, rejected alternatives, and a falsifiable `revisit_when`. | `DECISIONS.md` |
| docs/ACTIVE.md | Session handoff: what landed, deliberate scope notes, open threads, NEXT. The anti-amnesia file — read at session start, appended at session end. | `ACTIVE.md` |
| Check command | One honest command (`make check` or a script): lint + tests + self-test, first failure's exit code propagates, **no pipes that mask exit codes** (`cmd \| tail` eats the failure). Greenfield repos have no tests yet: check = linter over what exists + self-test, recorded as PARTIAL in HARNESS.md until the first story lands the first real test — an `echo ok` check command is the named disease. | documented in HARNESS.md |
| Self-test | `scripts/harness_selftest.py` **copied into the project** (skill-relative paths rot in CI). At tier S it verifies manifest, components, markers, and the rules hash; hooks add plant tests at tier M. | copy from `scripts/harness_selftest.py` |
| Manifest | `.claude/harness.json`: tier, components, core-rules hash, hook config. What audits check against. | `harness.json` |

Every document must have a writer, an update trigger, and a consumer. A doc nobody is obligated to update and nobody reads will rot and then lie — if you can't name all three, don't install the doc.

## Tier M — enforcement (multi-week, agent-driven, or production)

Everything in S, plus:

| Component | Job | Source |
|---|---|---|
| Protected-paths hook | Blocks edits under configured paths (vendored code, generated files, lockfiles). Realpath-resolved so worktrees/symlinks can't dodge it. Env bypass exists but contractually requires a ledger row in the same change: PATCHES.md when the upstream trait is installed, otherwise DECISIONS.md. | `scripts/hooks/protected_paths.py` |
| Status-guard hook | Blocks hand-editing a work item into a gated status when the edit carries no real evidence (empty-quoted template defaults don't count). Boundary, stated honestly: it sees Edit/Write tool calls only — Bash `sed`/append edits bypass it, which is why audit check 4 samples evidence directly. | `scripts/hooks/status_guard.py` |
| Secret-scan hook | Blocks writes containing credential-shaped literals (known prefixes, high-entropy assignments). Skips test fixtures; env-var reads are fine. | `scripts/hooks/secret_scan.py` |
| Work items | One file per story/task with frontmatter: `id`, `status`, `prd_refs` (clause IDs), `evidence`. The status field on disk is the state machine. | `STORY.md` |
| Harness self-test (extended) | The project-local copy now also plants a fake violation per hook and requires rejection, verifies hook wiring both ways (installed-but-unwired AND wired-but-missing), and regenerates each `generated_docs` entry to diff against the committed copy. **A guard that has never failed a fake must be presumed hollow.** | copy from `scripts/harness_selftest.py` |
| Failing-test discipline | Plans commit a failing (expected-fail) test bound to an acceptance clause before implementation. Use strict expected-fail (`xfail(strict=True)`, `test.todo` equivalents) so the test *flips loudly* when the feature lands, forcing marker removal. Guard against hollow tests: a constant-returning stub must NOT pass them — check with a throwaway stub before trusting a test. | discipline, documented in HARNESS.md |
| Generated STATUS | `docs/STATUS.md` generated from work-item frontmatter (`python3 scripts/gen_status.py docs/stories > docs/STATUS.md`), header says "generated — do not edit". Register it under `generated_docs` in the manifest so the self-test enforces freshness. | copy `scripts/gen_status.py` into the project |

Hook wiring: copy hooks into the project's `.claude/hooks/`, register via `assets/templates/settings-hooks.json` merged into the project's `.claude/settings.json` — **include only the hooks you actually installed**, and keep the `test ! -f || python3` guard form so a missing hook file allows edits instead of blocking every one. Configure `protected_paths` and `gated_statuses` in `.claude/harness.json`. Hooks are thin and **fail open** (a broken hook must never brick the session) — which is exactly why the self-test must prove they fire when healthy.

## Tier L — grown, never installed (patterns catalog)

For long-running, high-stakes, parallel-agent projects. Do not install these at setup; when an audit retro shows the pain, add the matching pattern as a backlog item with the incident named:

- **Driver + firing map**: work-item status on disk maps to which workflow fires next, via code whose exit code halts the loop mechanically — never rely on an agent reading a message to stop.
- **Append-only transition ledger** (JSONL): sole-writer function that refuses malformed rows and forces no-advance on non-green results.
- **Fresh-agent verification**: the reviewer agent is quarantined from the implementer's transcript; diffs pinned to a recorded base SHA; an unavailable reviewer yields PARTIAL, never a pass.
- **Merge lock + serialized merge queue**: for parallel agents; atomic lock directory, live owners are never stolen.
- **Invariant registry with owners**: cross-story invariants (the things N individually-green changes can silently compose into breaking) each get an executable member, a named owner, and routing by blast radius; full suite nightly.
- **Failure attribution by revert-and-retest**: when the integration suite goes red, revert candidate merges one at a time and re-test — never blame the last toucher.
- **Preamble fingerprinting**: shared rules injected into every workflow verbatim, SHA-checked so they can't be silently weakened — noting honestly that the hash proves presence, not obedience; obedience is proven by executed gates.
- **Upstream trait machinery** (see below), external multi-model review panels, epic-level value verification by subtraction (stub each child; the outcome test must break).

## Conditional trait: vendored/pinned upstream

Orthogonal to tier — install whenever the project wraps a codebase it must not fork:

- **Protected-paths hook** covering the upstream directory (tier M hook; for tier S projects, install just this hook anyway — it is the cheapest, highest-value guard).
- **SEAMS.md**: one row per contact point with the upstream — `seam · upstream_pin · depends_on_symbols (file:line) · acceptance_check · retirement_condition`. Enumerating the contact surface makes an upgrade a finite checklist instead of an archaeology dig.
- **PATCHES.md**: ledger for the escape hatch. **Zero data rows is the designed default.** Every bypass of the protected-paths hook lands a row in the same commit, with a machine-evaluable retirement condition (`retire when upstream >= X`). A patch outliving its condition is a silent re-fork — the audit checks for this.

## Graduation and retirement

Both go through DECISIONS.md, both are proposals for the user, never silent applications:

- **Graduate** (add machinery) when the same failure appears twice in deviation logs/audits since the last review, or a named incident occurred. Record the incident in the decision entry — every mechanism should be able to answer "what failure created you?"
- **Retire** (remove machinery) when a component guards against nothing this project does, or hasn't fired in multiple phases and its failure mode is covered elsewhere. The entry records `subsumed_by` or `obsolete_because`. Removing a guard removes, in the same change: the hook file, its `.claude/settings.json` entry, its manifest entry, and its self-test expectations — the audit flags orphans on any of these.
