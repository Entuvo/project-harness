# project-harness

A Claude skill that sets up a software project *before* implementation starts, then re-audits it at every phase boundary — so agentic work doesn't drift, and unknowns get surfaced before they become wrong code.

## Why this exists

An agent that hits a gap in its context does not stop. It fills the gap with a plausible, industry-average assumption and keeps going — producing coherent, confidently wrong work. The cost of each wrong assumption grows with how late it's discovered.

The second failure mode is quieter: even a well-set-up project decays. A rule gets softened during a refactor, a status gets hand-edited under deadline pressure, a doc keeps describing a world that no longer exists. Guardrails fail silently, and nobody notices until the damage is in.

This skill attacks both: a **setup mode** that closes context gaps before code is written, and a **phase audit** that verifies the guardrails still physically work — by feeding them fake violations and requiring rejection, not by reading documents that claim they work.

## What it distills

Three inputs, which independently converge on the same spine (surface assumptions before code; verify against executed checks in a loop):

1. **An "unknowns alignment" playbook** building on Thariq Shihipar's *know your unknowns* essay and examples: information gaps come in four quadrants, and each needs a *different* discovery move — open decisions get toggles, preferences the user can't articulate get generated variants to react to, blindspots get code scans and one-question-at-a-time interviews ordered by architectural blast radius.
2. **A Karpathy-style minimal CLAUDE.md** of behavioral rules: state assumptions before coding, minimum code that solves the problem, surgical diffs where every changed line traces to the request, and goal-driven execution that loops until verified.
3. **A production harness from a live algorithmic-trading platform build**, where months of agent-driven development grew enforcement machinery incident by incident: statuses derived from evidence rather than hand-authored, hooks that block violations with exit codes, generated docs with freshness gates, self-tests that prove each guard can actually fire, and a retro process that adds machinery only after the same failure appears twice.

The third input also supplies the skill's humility: that project's own governance notes warn that over-building the harness is the same scope-creep disease it prevents. So this skill installs the smallest tier that fits and grows it only on felt pain.

## What it does

**Setup mode** (no `.claude/harness.json` in the project): recon the territory (scan the actual code the work will touch), interview the human one question at a time ordered by blast radius, file everything into an unknowns register with the right move per quadrant, pick a harness tier, install the files, and — before declaring done — run the self-test, which feeds every installed guard a fake violation and fails unless each one rejects it.

**Audit mode** (harness present, run at every phase boundary): seven checks — presence & wiring, rules unweakened (the CLAUDE.md core-rules block is hash-pinned), guards still fire (plant tests re-run), status honesty (evidence sampled, generated docs re-generated and diffed), a drift sweep across eight drift types, a retro that proposes graduating or retiring machinery, and a written report. PARTIAL never silently converts to a pass; FAIL blocks the phase transition unless the owner records an override.

**Dispatch mode** (mid-phase): a single discovery move matched to the task shape — blindspot scan, spec interview, variant comparison, reference port map, deviation logging.

### Tiers

| Tier | For | Installs |
|---|---|---|
| S | Any project, day one | Bootstrap CLAUDE.md (≤40 lines, hash-pinned rules), PRD with stable clause IDs, HARNESS/UNKNOWNS/PLAN/DECISIONS/ACTIVE docs, manifest, self-test |
| M | Multi-week, unattended-agent, or production work | Adds three enforcement hooks (protected paths, secret scan, status guard), evidence-stamped work items, generated STATUS with a freshness gate |
| L | Long-running, high-stakes, parallel agents | Never installed day one — a patterns catalog (drivers, merge locks, invariant registries, review panels) grown via retro-justified additions |

## How to use it

**Install the skill**, any of:

- Save the packaged `project-harness.skill` file (Claude desktop / Cowork: click *Save skill*).
- From a marketplace repo: `/plugin marketplace add <owner>/<repo>` then `/plugin install project-harness@<marketplace>`.
- Claude Code, manual: copy this folder into `~/.claude/skills/` (global) or `<project>/.claude/skills/` (per-project).

**At project kickoff / planning**, in the repo you're setting up, say something like:

> Set this project up with a proper harness before we start building.

Claude runs setup: expect an interview (answer one question at a time), a tier recommendation to confirm, installed docs under `docs/`, and a passing self-test as the completion proof.

**At every phase boundary** (or after a rough week), say:

> Run the phase audit.

Expect a report in `docs/audits/audit-YYYY-MM-DD.md` with a PROCEED / PROCEED-WITH-FIXES / BLOCKED verdict and at most a couple of findings that actually matter.

**Requirements:** `python3` on PATH (all scripts are stdlib-only). Hooks require Claude Code's hook support (`.claude/settings.json`); on other surfaces the docs-and-audit layers still work. Git recommended — audits use history to find what changed.

## What's in the box

```
project-harness/
├── SKILL.md                    # entry point: modes, procedure, dispatch table
├── references/
│   ├── discovery.md            # the four quadrants and their moves, in detail
│   ├── tiers.md                # tier selection, contents, graduation/retirement
│   └── drift-audit.md          # the seven audit checks and report format
├── assets/templates/           # files installed into your project (fill + prune per tier)
│   ├── CLAUDE.md · HARNESS.md · PRD.md · UNKNOWNS.md · PLAN.md
│   ├── DECISIONS.md · ACTIVE.md · STORY.md · SEAMS.md · PATCHES.md
│   └── harness.json · settings-hooks.json
└── scripts/
    ├── harness_selftest.py     # proves the harness fires; also --hash-rules
    ├── gen_status.py           # STATUS.md generator (tier M)
    └── hooks/                  # protected_paths.py · secret_scan.py · status_guard.py
```

## Design principles

Prompting is not enforcing — every rule wants an executed backstop. State lives on disk, never in chat memory. Status is derived from evidence, never hand-authored — an LLM-emitted number is not evidence. Every guard ships a plant test; a guard that has never been fed a fake violation is presumed hollow. Audits verify disk reality, never a document's description of itself. Right-size, then grow on felt pain — each mechanism must answer "what failure created you?" One source of truth per fact; a copy is a fork that will rot.

## Verification

The machinery is tested, not asserted. `scripts/selftest_synthetic.py` — run in CI on every push and pull request — builds a full tier-M install in a tempdir, asserts the shipped self-test passes it with every plant firing, then applies each tamper below and asserts the self-test flips to a failure:

- softening a core rule (hash mismatch)
- hollowing out a hook (plant violation accepted)
- removing a hook's high-entropy / MultiEdit detector (a second plant catches it)
- unwiring a hook from settings.json
- deleting an *enabled* hook file while its `test ! -f`-guarded settings line remains — `hooks.enabled` makes this fail instead of passing silently
- an unfilled `{{ }}` template placeholder in an installed doc, or in the manifest itself
- a stale generated STATUS.md
- hand-flipping a work item to `done` with empty-quoted evidence
- a tier-S install still carrying a tier-M `Delete on tier S` section

It also feeds the hooks `MultiEdit`- and `NotebookEdit`-shaped payloads directly and asserts the credential and protected-path guards catch both shapes (and the status guard the `MultiEdit` form) — the write surfaces the hooks read beyond a plain `Write`.

(CI does not run `make check` or the dogfood `harness_selftest.py .`: this repo's own installed harness is intentionally git-excluded, so a fresh checkout has neither. The synthetic install is the self-contained gate.)

## License

MIT.
