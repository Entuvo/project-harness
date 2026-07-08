# Unknowns discovery

## Why this exists

The agent's context is a map; the repository, its pipeline, and the team's unwritten preferences are the territory. When the map has a gap, an agent does not stop — it fills the gap with an industry-average assumption and produces coherent, confidently wrong work. The cost of a wrong assumption grows with how late it is found. Discovery closes the gaps *before* code is written.

The gaps come in four kinds, and each kind fails differently, so each gets a different move. Collapsing them all into "ask clarifying questions" loses the method: you cannot ask someone about a preference they've never seen, and you cannot ask anyone about a constraint nobody knows exists.

## The four quadrants and their moves

| Quadrant | What it is | The move |
|---|---|---|
| Known knowns | Declared standards, APIs, explicit requirements | **Prove the map loaded.** Enumerate the constraints found, citing the files they came from. If you can't cite it, you assumed it. |
| Known unknowns | Identified but undecided items (database, schema, auth approach) | **Toggle, don't decide silently.** File a decision entry: 2–3 options, tradeoffs, a toggle the user flips, a decide-by point. Block dependent work until toggled. A throwaway sandbox prototype is allowed to inform the pick. |
| Unknown knowns | Preferences the user holds but cannot articulate until shown | **Show, don't ask.** Generate 3–4 concrete variants; the user selects elements across them; compile the selections into a written preference spec. Asking questions here fails by construction. |
| Unknown unknowns | Undocumented constraints, hidden couplings, deprecated behaviors | **Scan the territory and interview the human.** Read the actual code the work touches (not docs about it); interview one question at a time ordered by blast radius. The scan finds what the map omits; the human reveals what the repo omits. |

## The moves in detail

### Blindspot scan

For work touching unfamiliar or poorly documented subsystems. Read the real implementation of whatever the work will touch — auth, routing, CI config, deploy scripts, data migrations. Output is a set of **risk cards**, each with: the finding (hidden dependency, security exposure, constraint), why it bites this project, and a **copyable context correction** — the sentence that, added to context, would have prevented the wrong assumption. The user accepts or rejects each card; accepted corrections land in CLAUDE.md (if always-on) or UNKNOWNS.md (if situational). The output of a blindspot scan is corrected context, not a report.

Let the code determine how many cards there are. Three real findings beat seven padded ones.

### Spec interview

For ambiguous requirements. This is the user-side trigger phrase (recognize it when a user says it; when *you* are running setup, don't recite it — just conduct the interview under the rules below):

> Interview me one question at a time about anything still ambiguous in [feature/project]. Prioritize questions where my answer would change the architecture.

Rules that make it work:

- **One question at a time.** Batched questions get shallow answers.
- **Blast-radius order.** Ask first what would most change the architecture (execution model, data ownership, external boundaries), last what's cosmetic (naming, formats). If the answer to question 1 invalidates questions 2–7, you ordered correctly.
- **Offer the tradeoffs with each question** — "synchronous in the request (simple, but risks gateway timeout) vs. background job (robust, needs status polling)" — so the user decides on substance.
- Answers accumulate into DECISIONS.md (decided) and UNKNOWNS.md (parked with toggles).
- Stop when remaining questions wouldn't change the plan, or the user stops it. In tools with a structured question UI (e.g. AskUserQuestion), use it; the one-at-a-time and blast-radius rules still apply.

### Variant comparison

For genuinely subjective choices: visual design, interaction feel, API ergonomics, CLI shape. Generate 3–4 *concrete, distinct* variants — real renderings or real code sketches, not descriptions of variants. The user reacts, selecting elements across variants ("layout from B, density from C"). Compile the selections into a written preference spec that future work cites.

A sibling move for jargon-heavy domains (color science, audio, typography, finance): pair the variants with a short vocabulary ladder — live parameters labeled with the domain's real terms — so the user *learns to articulate* the preference ("less lift, warmer tint") instead of only pointing. Harvested parameters go into the spec verbatim.

### Reference port map

For porting logic across languages or codebases. Lay matched source and target blocks side by side; flag every semantic divergence — memory model, error-handling paradigm, numeric behavior, concurrency assumptions — before porting begins. Each flagged divergence becomes either a decision entry or a test.

### Deviation log

Not a pre-work move — the in-flight discipline that makes phase audits possible. Every divergence from the plan gets a row at the moment it happens: planned → actual → why → tradeoff accepted → lesson. Lives in PLAN.md's deviation section. At the phase audit, these rows are the retro's raw material. An empty deviation log after a long phase is itself a finding (nobody logs, or nothing was learned).

### Change quiz and pitch doc (optional, post-implementation)

Only when human reviewers exist; skip both entirely for solo/agent-only flows. Change quiz: generate comprehension questions from the actual diff; a wrong answer points the reviewer at the code block they missed. Pitch doc: a review summary that pre-answers likely objections with measured evidence from the codebase and names the approvers — useful when a change needs buy-in from people who weren't in the loop.

## Artifact rules

- **Markdown is the default medium.** Registers, plans, decisions, logs — everything that lives in git and gets diffed is markdown.
- **HTML only when the unknown is genuinely visual or comparative** — variant comparisons, interactive mocks, a change quiz. A schema decision is a markdown table with a toggle, not an HTML app.
- Every HTML artifact must be **self-contained** (single file, no build step, no external dependencies) and must **embed an export mechanism** — a button or copy block that returns the user's selections as structured markdown/JSON. Without export, the artifact is decoration; the loop never closes back into context.
- Nothing speculative: generate an artifact when a real decision needs it, never pre-build a suite of tools.

## Task inception protocol (per-task, always-on once installed)

This is installed into the project's CLAUDE.md core rules, and discovery enforces it at setup. Before any non-trivial implementation task, state:

1. **Victory conditions** — the named commands/tests whose passing proves the task done. If none exist yet, writing the failing check is the first step.
2. **Assumptions and confidence** — if requirements confidence is low, enumerate what's missing and ask; no file writes until answered. The enumerated list is the substance; never paper over uncertainty with hedged prose. Verify by behavior: when confidence was low, there must exist a question to the user and zero writes before the answer.
3. **Top 3 failure modes** — grounded in this repo's actual files and dependencies, each citing a real artifact. Generic risks ("might have bugs") don't count.

Scale by blast radius: full protocol for schema/API/infra decisions; a stated victory condition alone for small changes; the trivial-task exemption (single file, no interface change, no new dependency) skips ceremony entirely.
