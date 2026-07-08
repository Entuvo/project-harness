---
name: project-harness
description: Set up and maintain a project harness for agentic software development — unknowns discovery, drift prevention, and evidence-gated progress. Use at project kickoff or planning to install a right-sized harness (bootstrap CLAUDE.md, PRD with clause IDs, unknowns register, volatility-sorted plan, enforcement hooks, harness self-test), and re-run at EVERY phase boundary to audit that the harness is intact and catch drift. Trigger whenever the user starts a new software project, asks to plan, scaffold, or set up a repo for working with Claude, mentions drift, unknowns, blindspots, phase gates, kickoff, or asks whether the project/harness is still on track — even if they never say the word "harness".
---

# Project Harness

Install a harness on a software project during planning, then verify at every phase that it is still intact. The harness exists because an agent that hits a gap in its context does not stop — it fabricates a plausible assumption and keeps going. Everything here either closes those gaps before code is written (discovery) or catches the fabrication afterward (drift audit, evidence gates).

Two sources of authority behind this skill, which independently converge on the same spine:

- Behavioral floor (always-on): surface assumptions before coding, minimum code, surgical diffs, loop until verified.
- Phase ceremonies (invoked): unknowns discovery before implementation, deviation logging during, integrity audit at every boundary.

## Operating principles

These govern every mode of this skill. They come from post-mortems of real harness failures, so treat them as load-bearing:

1. **Prompting is not enforcing.** A rule that lives only in prose will eventually be ignored. Each rule should sit as high on this ladder as the project tier allows: prose → checklist → template → hook with exit code → tested code. When you install a prose rule, note what its executed backstop would be.
2. **State lives on disk, never in chat memory.** Plans, unknowns, decisions, statuses — all files. Any session must be able to resume from disk alone.
3. **Status is derived from evidence, never hand-authored.** No transition without a validated artifact (an executed check's output, a file that exists and is non-empty). An LLM-emitted number or claim is never evidence.
4. **Every guard ships a plant test.** A guard that has never been proven to fire must be assumed hollow. The harness self-test feeds each guard a fake violation and requires rejection.
5. **Verify against disk reality, not documents' descriptions of themselves.** When auditing, read the actual files, run the actual commands. A doc claiming "X is enforced" is a claim to check, not a fact.
6. **Right-size, then grow on felt pain.** Over-building the harness is the same scope-creep disease it exists to prevent. Install the smallest tier that fits; add machinery only when a retro shows the same failure twice, and record what incident justified each addition.
7. **One source of truth per fact.** Reference by ID or pointer, never copy text between docs. A copy is a fork that will rot.

## Mode detection

When invoked, determine the mode:

- No `.claude/harness.json` in the target project → **Setup mode** (first run, during planning).
- `.claude/harness.json` exists → **Audit mode** (phase boundary, integrity + drift check).
- User asks for a specific discovery move mid-phase ("what are we missing here", porting work, an ambiguous feature) → **Dispatch mode**: pick the move from the dispatch table below and run just that.

## Setup mode (run during planning, before implementation)

Work through these steps in order. Read `references/discovery.md` before steps 2–4 and `references/tiers.md` before step 5.

1. **Recon the territory.** If the repo has existing code, scan the subsystems the planned work will touch — the actual code, not docs about it. Produce blindspot findings: hidden couplings, undocumented constraints, deprecated patterns, each with a proposed context correction. Greenfield projects skip to the interview.
2. **Interview the human.** One question at a time, ordered by architectural blast radius — ask first about whatever answer would most change the architecture, and attach the tradeoffs to each question so the user decides on substance. Cover along the way: the goal AND explicit non-goals, duration and stakes, how many people/agents work in parallel, whether a vendored or pinned upstream exists, production/deployment constraints. Stop when remaining questions wouldn't change the plan, or the user calls it.
3. **File the unknowns.** Classify everything surfaced into `docs/UNKNOWNS.md` using the quadrant moves in `references/discovery.md`. The critical discipline: each quadrant gets a *different* move — open decisions get toggles, unarticulated preferences get generated variants to react to, blindspots get scans and interviews. Never collapse this into "I asked some clarifying questions."
4. **Resolve what blocks the plan.** Decisions that gate architecture get resolved now or explicitly parked with a toggle and a decide-by point. For genuinely subjective choices (UI direction, API ergonomics), generate 3–4 concrete variants for the user to react to — people can't articulate preferences they've never seen. Follow the artifact rules in `references/discovery.md`.
5. **Pick the tier.** Use `references/tiers.md`. Confirm the tier and any conditional traits (vendored upstream → seams/patches machinery) with the user before installing. Do not install a heavier tier than the answers justify.
6. **Install the harness files.** Copy from `assets/templates/`, filling every placeholder with real project content — never leave placeholder text in an installed file — and **prune tier-marked sections** (HARNESS.md marks its tier-M-only block) so no installed doc describes enforcement that doesn't exist. Copy `scripts/harness_selftest.py` (all tiers) and `scripts/gen_status.py` (tier M) into the project's `scripts/` — audits and CI run the project-local copies, since skill-relative paths rot. Write `.claude/harness.json` (the manifest) last: tier, `components` = every installed harness-marked file plus copied scripts, `generated_docs` for anything generated, and the core-rules SHA-256 (`python3 scripts/harness_selftest.py --hash-rules .`).
7. **Wire enforcement (tier M and up).** Install the hooks you need from `scripts/hooks/` into the project's `.claude/hooks/`, register **only those** in settings via `assets/templates/settings-hooks.json` (keep its `test ! -f` guard form — a phantom hook entry without it blocks every edit), and configure `protected_paths` / `gated_statuses` in the manifest.
8. **Prove the harness fires.** Run `python3 scripts/harness_selftest.py .` in the project — it feeds each installed guard a fake violation and fails unless every guard rejects it, and checks files, markers, wiring, hashes, and generated-doc freshness. Setup is not complete until the self-test passes. If a component can't be proven, mark it PARTIAL in `docs/HARNESS.md` — never silently green.
9. **Write the plan.** `docs/PLAN.md`, volatility-sorted: decisions likely to change at the top with their toggles, routine work collapsed below, every step carrying `→ verify: <concrete executable check>`.
10. **Record the setup.** DECISIONS.md entry (tier chosen, why, revisit_when), ACTIVE.md handoff, and tell the user what was installed and what the phase-audit cadence is.

## Audit mode (run at every phase boundary)

Read `references/drift-audit.md` for the full procedure and report format. The audit has a fixed spine — run all seven, report PASS / PARTIAL / FAIL per check:

1. **Presence & wiring** — every component in the manifest exists on disk; hooks are executable and registered; the check command runs.
2. **Rules unweakened** — the delimited core-rules block still hashes to the manifest value. A mismatch with a DECISIONS.md entry authorizing it = re-bless (update manifest hash); a mismatch without one = FAIL, restore from template.
3. **Guards still fire** — re-run the harness self-test. A guard that stopped rejecting fakes is hollow regardless of what any doc says.
4. **Status honesty** — sample recent status advances; each must have evidence that exists, is non-empty, and came from an executed check. Regenerate any generated docs (STATUS) and diff against committed.
5. **Drift sweep** — walk the drift catalog in `references/drift-audit.md`: scope vs. clause refs, plan vs. code, copied-text forks, stale unknowns/toggles, decisions past their revisit_when, deviation log gaps.
6. **Retro & right-sizing** — mine failures since last audit: the same failure twice is a pattern → propose a harness addition as a backlog item (proposal, not silent application). Machinery that never fired and guards against nothing felt → propose retirement with rationale. Additions and retirements go through DECISIONS.md.
7. **Report & handoff** — write the audit report (format in drift-audit.md), update ACTIVE.md, and surface the one or two highest-risk findings to the user in plain language.

PARTIAL is a first-class result: an environment or reviewer being unavailable never converts to a pass. FAIL blocks the phase transition until fixed or explicitly overridden by the user (record the override in DECISIONS.md).

## Dispatch table (mid-phase discovery)

| Task shape | Move (details in references/discovery.md) |
|---|---|
| Touching unfamiliar or poorly documented code | Blindspot scan of the actual code, risk cards with context corrections |
| Ambiguous requirements | Spec interview, one question at a time, blast-radius ordered |
| Subjective/visual/API-feel choices | Generate 3–4 concrete variants, user reacts, compile selections into spec |
| Identified-but-undecided technical choice | Toggle entry in UNKNOWNS.md with options + tradeoffs; block dependent work |
| Porting logic across languages/codebases | Side-by-side reference map; flag semantic divergences before porting |
| Long multi-file change in flight | Deviation log discipline: planned → actual → why → tradeoff → lesson |
| Preparing work for human review | Optional: comprehension quiz generated from the diff (only when a human reviewer exists) |

## Tiers, in one line each

**S** = docs + discipline + self-test (any project, day one). **M** = adds executable enforcement: hooks, evidence-stamped work items, generated STATUS with a freshness gate (multi-week, unattended-agent, or production work). **L** = grown via retro-justified backlog items, never installed day one. The authoritative component tables, selection questions, and graduation/retirement rules live in `references/tiers.md` — read it before choosing; don't work from this summary.

Templates live in `assets/templates/`, hooks and the self-test in `scripts/`. Read `references/discovery.md` for every discovery move; read `references/drift-audit.md` for every audit.
