# Plan — {{PHASE_OR_FEATURE}}
<!-- harness:plan v1 · volatility-sorted: what's likely to CHANGE sits at the top, not what happens first -->
<!-- Phase names come from this file's headings and nowhere else — a second numbering scheme is drift. -->
<!-- Tier S: this whole file stays under one page. -->

## Volatile decisions (resolve or toggle before dependent steps)

<!-- Pointers only: picks, alternatives, and tradeoffs live in UNKNOWNS.md. Restating them here is a fork that will rot. -->

- Blocks step {{n}}: UNKNOWNS.md D{{n}} — {{one-line label, e.g. "export execution model"}}

## Steps

<!-- Every step carries a concrete, executable verify. "Works" is not a verify; a command with an expected result is. -->

1. {{step}} → verify: `{{command}}` {{expected result}}
2. {{step}} → verify: `{{command}}` {{expected result}}
3. {{step}} → verify: `{{command}}` {{expected result}}

## Routine work (collapsed — low variance, do when reached)

- {{boilerplate/setup items, one line each}}

## Deviation log

<!-- Tier S: leave this section empty until the SECOND deviation — the first is a line in ACTIVE.md.
     Fill the row AT THE MOMENT you diverge, not retroactively. These rows are the retro's raw material at the phase audit — an empty log after a hard phase is itself a finding. -->

| Date | Planned | Actual | Why | Tradeoff accepted | Lesson |
|---|---|---|---|---|---|
