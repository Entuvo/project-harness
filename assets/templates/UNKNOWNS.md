# Unknowns register
<!-- harness:unknowns v1 · re-read at every phase audit; each quadrant has a DIFFERENT move — see the project-harness skill.
Quadrant map: Open decisions = known unknowns · Preference gaps = unknown knowns · Blindspot findings = unknown unknowns ·
Assumptions = the map itself, whichever quadrant it came from — anything work currently relies on without confirmation.
Known knowns don't live here: they are proven at setup by enumerating constraints WITH file citations (uncitable = assumed). -->

## Open decisions (known unknowns — toggle before dependent work proceeds)

<!-- Never decide silently. Dependent work is blocked until the toggle is flipped. -->

| ID | Decision | Options (tradeoffs) | Toggle | Decide by | Blocks |
|---|---|---|---|---|---|
| D1 | {{e.g. datastore}} | A: {{option (tradeoff)}} · B: {{option (tradeoff)}} | ☐ undecided | {{phase/date}} | {{story IDs}} |

## Assumptions awaiting confirmation (the map may be wrong)

<!-- Stated assumptions work is currently proceeding on. Confirm or refute each — an unconfirmed assumption is a liability, not a fact. -->

| ID | Assumption | Source (file:line or "unverified") | Status |
|---|---|---|---|
| A1 | {{e.g. "upstream API is idempotent on retry"}} | {{citation or unverified}} | ☐ unconfirmed |

## Preference gaps (unknown knowns — show variants, don't ask)

<!-- Subjective choices the owner can't articulate until shown. Resolve by generating 3–4 concrete variants and compiling the reactions into a spec. -->

| ID | Area | Variants shown | Compiled preference |
|---|---|---|---|
| P1 | {{e.g. CLI output format}} | {{link/date or pending}} | {{spec or pending}} |

## Blindspot findings (unknown unknowns — from scans and interviews)

<!-- Discovered constraints nobody had written down. Each accepted finding becomes a context correction (CLAUDE.md if always-on, here if situational). -->

| ID | Finding | Where found | Context correction | Accepted? |
|---|---|---|---|---|
| B1 | {{e.g. "deploy script rewrites config on every run"}} | {{file:line}} | {{the sentence that prevents the wrong assumption}} | ☐ |

## Resolution log

| Date | ID | Resolution | Recorded in |
|---|---|---|---|
| {{DATE}} | {{ID}} | {{what was decided/confirmed}} | DECISIONS.md {{entry}} |
