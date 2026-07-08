# Harness — how this project works
<!-- harness:harness-md v1 · sections marked "tier M only" get DELETED on tier S installs — a doc describing enforcement that doesn't exist is the anti-goal in action -->

## Goal and anti-goal

**Goal:** {{ONE_SENTENCE_PROCESS_GOAL — e.g. "ship X with every status backed by an executed check"}}

**Anti-goal (the failure this harness exists to prevent):** {{NAMED_ANTI_GOAL — e.g. "docs that over-claim, gates that pass hollow, scope that creeps feature by feature". Name it concretely; every mechanism below should trace to it.}}

## Manifest

Machine-readable manifest: `.claude/harness.json` (tier, components, hook config, core-rules hash). The phase audit checks disk against it. Rule: `components` lists **every** installed harness-marked file — adding or retiring one updates the manifest in the same change.

- Tier: {{TIER}}
- Conditional traits: {{none | upstream (SEAMS.md + PATCHES.md + protected-paths hook)}}

## Tracking work

<!-- Tier S: keep this paragraph, delete the tier-M block below. -->
{{TIER_S: Work is tracked as PLAN.md steps. A step is done when its `→ verify:` command has been executed and its output recorded next to the step. No other state machine exists at this tier.}}

<!-- Tier M only: work items with evidence-gated states. Delete on tier S. -->
Work lives in `docs/stories/` (one file per item, frontmatter per the STORY template). The `status` field on disk is the state machine:

`backlog → planned → in-progress → done`{{ADJUST_STATES_TO_FIT — if you rename states, update gated_statuses in .claude/harness.json and the STORY template comment in the same change}}

**The honesty rule: no transition without evidence.** Each transition's required evidence:

| Transition | Required evidence |
|---|---|
| planned → in-progress | PLAN.md step exists with `→ verify:`; for non-trivial items, a committed failing test bound to a PRD clause |
| in-progress → done | The item's verify command executed and green; output captured to `docs/evidence/` and referenced in the item's `evidence.artifact` field |

Statuses are advanced by work that produced the evidence — never by a bare hand-edit. The status-guard hook enforces this for file edits; Bash-based edits bypass it, which is why audit check 4 samples evidence directly.

`docs/STATUS.md` is generated (`python3 scripts/gen_status.py docs/stories > docs/STATUS.md`), never hand-edited; the self-test regenerates and diffs it.

## The check command

`{{CHECK_COMMAND}}` — lint + tests + `python3 scripts/harness_selftest.py .` (tier M). The first failure's exit code propagates. No pipes that can mask exit codes. Run before declaring anything done and at every audit.
{{GREENFIELD_NOTE — if the repo has no tests yet: check = linter over what exists + self-test, recorded here as PARTIAL until the first story lands the first real test. An echo-ok check command is the named disease.}}

## Phase audits

At every phase boundary, run the project-harness skill's phase audit before advancing. Reports land in `docs/audits/`. FAIL blocks the transition unless the owner records an override in DECISIONS.md.

## Drift controls (summary — full catalog in the project-harness skill)

- Scope: work cites PRD clause IDs; the PRD's out-of-scope list is checked in audits.
- Plans: volatility-sorted, every step `→ verify:`, deviations logged as they happen.
- Rules: CLAUDE.md core-rules block is hash-pinned in the manifest; changes require a DECISIONS.md entry.
- Docs: generated docs are never hand-edited; every doc must have a writer, a trigger, and a consumer.

## Explicitly NOT governed

{{LIST_WHAT_IS_DELIBERATELY_FREE — e.g. "commit message format, editor choice, exploratory spikes in scratch/ (which never merge without a story)". An honest list here prevents the harness from swallowing everything.}}

## Graduation / retirement log

Machinery is added only after felt pain (same failure twice, or a named incident) and removed when obsolete — both via DECISIONS.md proposals authorized by the owner. Retiring a hook also removes its settings.json entry, its manifest entry, and its self-test expectations. Every mechanism must be able to answer: *what failure created you?*

| Date | Added/Retired | Component | Incident / obsolete_because |
|---|---|---|---|
| {{DATE}} | Added | Initial tier {{TIER}} harness | Project setup |
