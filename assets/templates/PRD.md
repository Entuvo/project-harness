# {{PROJECT_NAME}} — PRD
<!-- harness:prd v1 · requirements carry stable clause IDs; everything else cites the ID, never copies the text -->

## Vision / problem

{{2–4 sentences: who hurts, how, and what done looks like}}

## Scope boundaries and standing assumptions

- In scope: {{...}}
- Standing assumptions: {{each one is a liability until confirmed — mirror the load-bearing ones in UNKNOWNS.md}}

## Guiding principles

1. {{e.g. "boring technology unless a requirement forces otherwise"}}

## Requirements

<!-- Stable IDs: R1, R2… with clauses R1.c1, R1.c2… Each clause is individually testable — that's what makes it citable by stories and checkable by audits. Never renumber; retire IDs instead. -->

### R1 — {{requirement title}}
- **R1.c1:** {{single testable clause}}
- **R1.c2:** {{single testable clause}}
- Acceptance: {{the check that proves R1 — command, test name, or observable behavior}}

## Non-functional requirements

- **N1:** {{performance/reliability/security bound, with a number where possible}}

## Out of scope / cut list

<!-- Load-bearing for drift control: audits diff work against this list. Be specific — "no admin UI in v1", not "keep it simple". -->

- {{cut item, and the condition under which it would return}}

## Definition of done

{{what "the project/phase is done" means in executable terms}}

## Phases

| Phase | Delivers (clause IDs) | Hard exit criteria |
|---|---|---|
| 1 | {{R1, R2.c1}} | {{executable criteria}} + phase audit passed |
