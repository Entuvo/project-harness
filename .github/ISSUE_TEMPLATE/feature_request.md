---
name: Feature request
about: Propose new machinery or a change to existing behavior
title: "[feat] "
labels: enhancement
assignees: ''
---

## What failure would this catch?

This project grows on *felt pain* — new machinery should answer "what failure
created you?" Describe the concrete failure mode this addresses, ideally one
you've hit more than once.

## Proposed change

What you'd like the harness to do.

## Which layer

- [ ] Discovery (unknowns, interview, variants)
- [ ] Drift audit (a new check or drift type)
- [ ] Enforcement (a hook / guard)
- [ ] Templates / docs
- [ ] Tiers / graduation logic
- [ ] Other

## How would it be proven?

Every guard ships a plant test. Sketch how the self-test would feed this a fake
violation and require rejection.

## Alternatives considered

Simpler options, or why prose/checklist isn't enough here.
