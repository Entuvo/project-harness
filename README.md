# project-harness

**A Claude Code skill that sets up a software project _before_ the first line of code — and keeps it honest at every step after.**

It installs a right-sized *harness* — the small set of docs, rules, and automated guards a project needs to stay on track — then re-checks, at every phase boundary, that the harness still physically works. The payoff: agents stop drifting, and the unknowns that would have become wrong code get surfaced up front.

---

## Why you'd want it

An AI agent that hits a gap in its context does not stop and ask. It fills the gap with a plausible, industry-average guess and keeps going — producing coherent, confidently wrong work. The later that guess is caught, the more it costs.

And even a well-run project decays. A rule gets softened during a refactor. A status gets hand-edited under deadline pressure. A doc keeps describing a world that no longer exists. Guardrails fail quietly, and nobody notices until the damage is in.

project-harness attacks both failure modes: it **closes the context gaps before code is written**, and it **proves your guardrails still work** — by feeding them fake violations and requiring rejection — instead of trusting a document that claims they do.

---

## What it does

You talk to it in plain language, and it runs one of three modes.

| You say… | Mode | What happens |
|---|---|---|
| "Set this project up before we build." | **Setup** | Interviews you, files the unknowns, installs a right-sized harness, and proves the guards fire before declaring done. |
| "Run the phase audit." | **Audit** | Re-checks that the harness is intact and the work hasn't drifted; returns a **PROCEED / PROCEED-WITH-FIXES / BLOCKED** verdict. |
| "What are we missing here?" | **Dispatch** | Runs a single discovery move mid-phase — a blindspot scan, a spec interview, a variant comparison, a reference-port map. |

It detects the mode automatically: no `.claude/harness.json` yet → Setup; one exists → Audit; a specific mid-phase ask → Dispatch.

---

## How it works

1. **Interview, don't assume.** During setup it asks one question at a time, ordered by *blast radius* — whatever answer would most change the architecture comes first — and files every open decision, assumption, and blindspot into an unknowns register, each with the right discovery move.

2. **Right-size, then grow.** It installs the **smallest tier that fits** (see below) and grows only when an audit shows real pain. Over-building the harness is the same disease it prevents.

3. **Put the state on disk, not in chat.** Requirements (with stable clause IDs), the plan, the unknowns, the decisions, and a session handoff all live as files, so any session — or any agent — can resume from disk alone.

4. **Guard with executed checks, not prose.** Load-bearing rules become real enforcement: hooks that block a credential-shaped literal, a hand-edited status with no evidence, or an edit to protected code — each exiting non-zero so the violation can't land.

5. **Prove the guards are real.** A shipped self-test feeds every guard a fake violation and fails unless each one rejects it. *A guard that has never been fed a fake is presumed hollow.*

6. **Audit against disk reality.** At each phase boundary it re-runs the guards, re-hashes the rules, re-generates and diffs the generated docs, and sweeps for drift — reading the actual files and running the actual commands, never a doc's description of itself.

7. **See the whole status at a glance** — the status dashboard, below.

---

## The status dashboard

A picture is worth a hundred words. Run:

```bash
python3 scripts/gen_dashboard.py . > docs/status.html
```

…and open `docs/status.html` in any browser to see the whole project at a glance: tier and self-test health, the work-item board, PRD clause coverage, plan progress, the unknowns quadrants, decisions due for review, and the latest audit verdict.

- **Self-contained and tool-agnostic** — one standalone HTML file (inline styles and scripts, system fonts, no external dependencies, no hosted service). It opens from disk and works the same under Claude Code, Codex, or no agent at all.
- **Read-only** — a snapshot regenerated from your harness files, never a way to hand-edit a status (that would defeat the point).
- **Deterministic** — identical inputs produce identical bytes, so the self-test catches a stale dashboard.
- **Opt-in at any tier** — not part of the default install; add it when you want the view. Tiers without work items simply omit that panel.

---

## Tiers — install the smallest that fits

| Tier | For | Installs |
|---|---|---|
| **S** | Any project, day one | Bootstrap `CLAUDE.md` (≤40 lines, hash-pinned rules), a PRD with stable clause IDs, the HARNESS/UNKNOWNS/PLAN/DECISIONS/ACTIVE docs, a manifest, and the self-test. |
| **M** | Multi-week, unattended-agent, or production work | Everything in S, plus three enforcement hooks (protected paths, secret scan, status guard), evidence-stamped work items, and a generated STATUS with a freshness gate. |
| **L** | Long-running, high-stakes, parallel agents | Never installed on day one — a patterns catalog (drivers, merge locks, invariant registries, review panels) grown one retro-justified addition at a time. |

The optional [status dashboard](#the-status-dashboard) can be added to any tier.

---

## Getting started

**Install the skill** (any of):

- Save the packaged `project-harness.skill` file (Claude desktop / Cowork: click *Save skill*).
- From a marketplace repo: `/plugin marketplace add <owner>/<repo>` then `/plugin install project-harness@<marketplace>`.
- Claude Code, manual: copy this folder into `~/.claude/skills/` (global) or `<project>/.claude/skills/` (per-project).

**At kickoff**, in the repo you're setting up, say:

> Set this project up with a proper harness before we start building.

Expect an interview (answer one question at a time), a tier recommendation to confirm, installed docs under `docs/`, and a passing self-test as the completion proof.

**At every phase boundary** (or after a rough week), say:

> Run the phase audit.

Expect a report in `docs/audits/audit-YYYY-MM-DD.md` with a verdict and at most a couple of findings that actually matter.

**Requirements:** `python3` on PATH (all scripts are standard-library only). The enforcement hooks use Claude Code's hook support (`.claude/settings.json`); on other surfaces the docs, audit, and dashboard layers still work. Git recommended — audits use history to find what changed.

---

## What's in the box

```
project-harness/
├── SKILL.md                    # entry point: modes, procedure, dispatch table
├── references/
│   ├── discovery.md            # the four unknown-quadrants and their moves
│   ├── tiers.md                # tier selection, contents, graduation/retirement
│   └── drift-audit.md          # the seven audit checks and report format
├── assets/templates/           # files installed into your project (fill + prune per tier)
│   ├── CLAUDE.md · HARNESS.md · PRD.md · UNKNOWNS.md · PLAN.md
│   ├── DECISIONS.md · ACTIVE.md · STORY.md · SEAMS.md · PATCHES.md
│   └── harness.json · settings-hooks.json
└── scripts/
    ├── harness_selftest.py     # proves the harness fires; also --hash-rules
    ├── selftest_synthetic.py   # synthetic tier-M install test (the CI gate)
    ├── gen_status.py           # STATUS.md generator (tier M)
    ├── gen_dashboard.py        # self-contained HTML status dashboard (opt-in)
    └── hooks/                  # protected_paths.py · secret_scan.py · status_guard.py
```

---

## Design principles

Prompting is not enforcing — every rule wants an executed backstop. State lives on disk, never in chat memory. Status is derived from evidence, never hand-authored — an LLM-emitted number is not evidence. Every guard ships a plant test; a guard that has never been fed a fake violation is presumed hollow. Audits verify disk reality, never a document's description of itself. Right-size, then grow on felt pain — each mechanism must answer "what failure created you?" One source of truth per fact; a copy is a fork that will rot.

---

## Verification

The machinery is tested, not asserted. `scripts/selftest_synthetic.py` — run in CI on every push and pull request — builds a full tier-M install in a tempdir, asserts the shipped self-test passes it with every plant firing, then applies each tamper below and asserts the self-test flips to a failure:

- softening a core rule (hash mismatch)
- hollowing out a hook (plant violation accepted)
- removing a hook's high-entropy / MultiEdit detector (a second plant catches it)
- unwiring a hook from settings.json
- deleting an *enabled* hook file while its `test ! -f`-guarded settings line remains
- an unfilled `{{ }}` template placeholder in an installed doc, or in the manifest
- a stale generated STATUS.md
- hand-flipping a work item to `done` with empty-quoted evidence
- a tier-S install still carrying a tier-M `Delete on tier S` section

It also feeds the hooks `MultiEdit`- and `NotebookEdit`-shaped payloads directly, and renders the status dashboard against the synthetic install — asserting it is a complete, self-contained, byte-deterministic document that degrades gracefully at tier S.

---

## License

MIT.
