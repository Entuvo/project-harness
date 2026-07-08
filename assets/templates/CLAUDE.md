# {{PROJECT_NAME}} — agent bootstrap pointer
<!-- harness:claude-md v1 · keep ≤40 lines · this file points, it never duplicates -->

## CURRENT FOCUS ({{DATE}})
- Objective: {{OBJECTIVE}}
- NOT an objective right now: {{NON_GOALS}}

<!-- harness:core-rules:begin v1 · do not edit inside this block; propose changes via docs/DECISIONS.md -->
## Always-on rules
1. Surface assumptions before writing code. If two interpretations exist, present both — never pick silently. If a simpler approach exists, say so; push back when warranted. When requirements confidence is low: enumerate what's missing and ask — zero writes until answered.
2. Before a non-trivial change, state victory conditions (the named commands/tests that prove it done). Scale with blast radius: schema/API/infra changes also get the top 3 failure modes, each citing a real file or dependency in this repo.
3. Minimum code that solves the problem. No unrequested features, no abstractions with one call site, no speculative configurability.
4. Surgical diffs: every changed line traces to the request. Match surrounding style. Remove only orphans your own change created; flag pre-existing dead code, don't delete it.
5. Loop until verified: a completion claim requires executed check output. A bug fix starts with a failing reproduction test.
6. Status is derived from evidence, never hand-authored. No validated evidence → no status advance.
7. Trivial-task exemption: single file, no interface change, no new dependency → use judgment, skip the ceremony.
<!-- harness:core-rules:end -->

## Context hygiene
- State lives on disk, not in chat memory. Read docs/ACTIVE.md at session start; append to it at session end.
- Large explorations go to subagents; clear context at phase boundaries.
- At every phase boundary, run the project-harness phase audit before advancing (reports: docs/audits/).
- Check: `{{CHECK_COMMAND}}` (exit code is the verdict — never pipe it through anything).

## Source of truth
- What to build: docs/PRD.md (cite clause IDs, never copy text)
- How we work: docs/HARNESS.md · Open questions: docs/UNKNOWNS.md
- Plan: docs/PLAN.md · Decisions: docs/DECISIONS.md · Handoff: docs/ACTIVE.md
- This file is a pointer, not a third source of truth.
