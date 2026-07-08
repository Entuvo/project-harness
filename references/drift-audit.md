# Phase audit: harness integrity and drift

Run at every phase boundary (and before any release/merge milestone). The audit answers two questions: **is the harness still intact**, and **has the work drifted from the plan, the scope, or reality**. It exists because harnesses fail quietly — a rule gets softened during a refactor, a status gets hand-edited under deadline pressure, a doc keeps describing a world that no longer exists. Each check below verifies disk reality, never a document's description of itself.

## Verification doctrine

- **Run, don't read.** "HARNESS.md says the self-test runs in CI" is a claim; running the self-test is the check.
- **PARTIAL is a first-class result.** A check that couldn't run (missing environment, unavailable tool) reports PARTIAL with the reason — it never silently converts to a pass.
- **FAIL blocks the phase transition** until fixed, or explicitly overridden by the user with a DECISIONS.md entry recording the override and its revisit_when.
- **An LLM-emitted number is never evidence.** Counts, percentages, and "all tests pass" claims must come from executed command output captured in the report.

**Establishing "since the last audit":** the prior report is the newest file in `docs/audits/` — read its date and verdict first. No prior report → this is the first audit: sample everything. Which statuses advanced since then: `git log -p --since=<date> -- <story_glob>` (or file modification order when there's no git history).

## The seven checks

### 1. Presence & wiring

Read `.claude/harness.json`. For every listed component: the file exists and is non-empty. Every hook referenced in `.claude/settings.json` resolves to an existing file or carries the `test ! -f` missing-file guard (a phantom hook without the guard blocks every edit). Run the project's check command; its exit code is the result. Orphans count both ways: a manifest entry with no file, or a harness-marked file absent from the manifest.

### 2. Rules unweakened

Recompute the SHA-256 of the delimited core-rules block in CLAUDE.md (`python3 scripts/harness_selftest.py --hash-rules .` — the project-local copy) and compare to `core_rules_sha256` in the manifest.

- Match → PASS.
- Mismatch + a DECISIONS.md entry authorizing the change → re-bless: update the manifest hash, note in the report.
- Mismatch + no authorizing entry → FAIL. Someone (often an agent mid-task) edited the constitution. Restore the block from the template or from the last authorized version, then file what happened in the deviation log.

Also: CLAUDE.md still ≤40 lines (bloat is drift — it stops being read), and still a pointer (no copied requirement text).

### 3. Guards still fire

Run the project-local `python3 scripts/harness_selftest.py .`. It plants a fake violation for each installed guard (a write into a protected path, a gated-status edit with only empty-quoted evidence, a credential-shaped literal) and requires each to be rejected; it also verifies template markers, hook wiring in both directions, and regenerates every `generated_docs` entry to diff against the committed copy. A guard that stopped rejecting fakes is hollow **now**, whatever it did last month.

### 4. Status honesty

Tier M: sample the work items whose status advanced since the last audit (all of them if few). For each: `evidence.artifact` points at a real, non-empty file under `docs/evidence/` whose content is executed check output (a hand-typed `result: exit 0` with no artifact is a claim, not evidence). Check no expected-fail markers remain on tests whose features shipped.

Tier S (no work items): sample PLAN.md's checked-off steps instead — each must have its `→ verify:` command's output recorded next to it or reachable from it.

### 5. Drift sweep

Walk the catalog. Each row: what it looks like when healthy, what drift looks like, how to check.

| Drift type | Healthy | Drifted | Check |
|---|---|---|---|
| Scope creep | Every work item cites PRD clause IDs; diffs touch what the item declared | Work with no clause ref; diffs sprawling past the declared surface; cut-list items reappearing | Diff work items against PRD refs; grep recent changes against the out-of-scope list |
| Plan vs. code | PLAN.md steps checked off with their `→ verify:` executed | Steps done with no verify run; plan silently reordered; deviations unlogged | For each completed step, find the verify output; empty deviation log after a hard phase is itself suspicious |
| Copy-fork rot | Facts stated once, cited by ID elsewhere | Requirement text pasted into stories/plans, now diverged from PRD | Spot-check quoted requirement text against the PRD source |
| Assumption drift | Load-bearing claims about external APIs/libs carry a file:line citation verified by reading | "X behaves like Y" stated from memory | Sample recent claims; re-read the cited source; a claim with no citation is unverified |
| Stale unknowns | UNKNOWNS.md toggles flipped or re-dated; resolved rows moved to the log | Open toggles past decide-by; work proceeding on un-flipped decisions | Read UNKNOWNS.md against the calendar and the diff |
| Decision expiry | DECISIONS.md `revisit_when` conditions checked each audit | A decision whose revisit condition came true, still governing | Evaluate each revisit_when against today's reality |
| Upstream divergence (if trait installed) | Zero PATCHES rows, or rows with live retirement conditions | A patch outliving its retirement condition (silent re-fork); upstream edits not in the ledger | Evaluate each retirement condition; verify the protected dir is clean modulo ledgered paths |
| Doc-consumer rot | Every harness doc has a writer, trigger, consumer | A doc updated by nobody, read by nobody, describing last month | For each doc: when last updated, what updates it, who read it this phase — fail any doc with no answer |
| Tier budget | Installed ceremony fits the tier's caps in `references/tiers.md` (tier S: one-page plan, no standalone plan docs, audits diff-scaled) | Governance volume outgrowing the product code; plan pages, report files, or logs past the tier's caps | Compare the manifest's tier against the caps; over-budget → retirement/slimming proposal in check 6 |

### 6. Retro & right-sizing

Mine deviation logs and audit findings since the last audit:

- **Pattern threshold: the same failure class twice.** Once is noise; twice is a pattern → propose a harness addition (new rule, hook, or check) as a backlog item citing the incidents. Proposal, never silent application — the user authorizes, then it lands like any other change.
- **Cost check:** any guard that has fired only false positives, or protects against something this project structurally can't do → propose retirement (with `subsumed_by`/`obsolete_because`).
- Rules that were repeatedly bypassed with authorization are mis-sized: either promote enforcement (ladder up: prose → hook) or loosen the rule honestly.
- **YAGNI check:** does any planned-but-unstarted phase serve a consumer that does not yet exist (a second brand with one brand live, a feedback loop before anything publishes)? If yes, propose deferring it — harness planning feels cheap, which pulls speculative phases forward.

### 7. Report & handoff

Write the report to `docs/audits/audit-YYYY-MM-DD.md`:

```markdown
# Phase audit — YYYY-MM-DD (phase: <name>)

| # | Check | Result | Evidence |
|---|-------|--------|----------|
| 1 | Presence & wiring | PASS/PARTIAL/FAIL | <command outputs, paths> |
| 2 | Rules unweakened | ... | <hash compare> |
| 3 | Guards fire | ... | <self-test output> |
| 4 | Status honesty | ... | <sampled items> |
| 5 | Drift sweep | ... | <per-row notes> |
| 6 | Retro | n/a | <proposals filed> |

## Findings (ranked by risk)
1. ...

## Proposals (require user authorization)
- Graduate: ... (incidents: ...)
- Retire: ... (obsolete_because: ...)

## Verdict
PROCEED / PROCEED-WITH-FIXES / BLOCKED (reason)
```

Then update ACTIVE.md (audit happened, verdict, top findings) and tell the user the verdict with the one or two findings that matter most — plain language, no ceremony.

## Cadence — scale depth to diff size, not phase count

The audit must never cost more than the phase it audits. Measure the diff since the last audit (`git diff --stat <last-audit-ref>`):

- **Small diff (roughly < 300 changed lines, no schema/API/infra change):** light audit — run the check command and the self-test (checks 1–3 collapse into their exit codes), spot-check status honesty, then append **one paragraph to ACTIVE.md**: date, verdict, anything found. No report file, no multi-auditor pass.
- **Above threshold, or any release/merge milestone:** full seven checks with the report.

Prior audit reports are **inputs** (dates, open proposals), never audit subjects — auditing an audit is drift, not diligence.

- Phase boundary: full seven checks (subject to the diff-size rule above).
- Mid-phase spot check (optional, after a rough week or a big merge): checks 3 + 4 + the Plan-vs-code row of check 5.
- Never batch audits ("we'll audit both phases later") — the value is catching drift while the diff is small.
