---
id: S-{{N}}
title: {{TITLE}}
status: backlog            # advances only with evidence — see docs/HARNESS.md state table
prd_refs: [R{{n}}.c{{m}}]  # clause IDs this story delivers; work outside these refs is scope creep
depends_on: []
touches: [{{paths/areas this story is allowed to change}}]
evidence:                  # filled by work, never by hand: executed check output that justifies the current status
  verify_cmd: ""           # the command that was run
  result: ""               # one-line outcome (e.g. "exit 0, 14 passed")
  artifact: ""             # path to the captured output under docs/evidence/ — audits verify it exists and is non-empty; a hand-typed result with no artifact is a claim, not evidence
---

# S-{{N}} — {{TITLE}}

**Goal (verifiable):** {{restate as a checkable outcome: "tests X,Y pass", not "improve Z"}}

**Failing test committed:** {{path::test_name (expected-fail until the feature lands) — or "trivial-exemption" with reason}}

**Notes / deviations:** {{link PLAN.md deviation rows that touched this story}}
