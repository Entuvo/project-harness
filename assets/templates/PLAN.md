# Plan — {{PHASE_OR_FEATURE}}
<!-- harness:plan v1 · volatility-sorted: what's likely to CHANGE sits at the top, not what happens first -->

## Volatile decisions (resolve or toggle before dependent steps)

<!-- Schema shapes, external API boundaries, execution models — anything whose change would ripple. Each links to its UNKNOWNS.md toggle. -->

| Step | Decision | Current pick | Alternative kept open | UNKNOWNS ref |
|---|---|---|---|---|
| V1 | {{e.g. export runs as background job}} | {{pick}} | {{fallback + what switching costs}} | D{{n}} |

## Steps

<!-- Every step carries a concrete, executable verify. "Works" is not a verify; a command with an expected result is. -->

1. {{step}} → verify: `{{command}}` {{expected result}}
2. {{step}} → verify: `{{command}}` {{expected result}}
3. {{step}} → verify: `{{command}}` {{expected result}}

## Routine work (collapsed — low variance, do when reached)

- {{boilerplate/setup items, one line each}}

## Deviation log

<!-- Fill the row AT THE MOMENT you diverge, not retroactively. These rows are the retro's raw material at the phase audit — an empty log after a hard phase is itself a finding. -->

| Date | Planned | Actual | Why | Tradeoff accepted | Lesson |
|---|---|---|---|---|---|
