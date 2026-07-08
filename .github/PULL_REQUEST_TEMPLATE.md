## What & why

What does this change, and what failure or request does it trace to?

## Type of change

- [ ] Bug fix
- [ ] New machinery (hook / check / discovery move)
- [ ] Docs / templates
- [ ] Refactor (no behavior change)

## Verification

Every rule wants an executed backstop. Check what you ran:

- [ ] `python3 scripts/harness_selftest.py .` passes
- [ ] `python3 -m py_compile` succeeds for all changed `.py` files
- [ ] Regenerated the core-rules hash (`--hash-rules`) if `CLAUDE.md` core rules changed
- [ ] New guards ship a plant test that provably fires

Paste the self-test result:

```
<paste output here>
```

## Surgical-diff check

- [ ] Every changed line traces to the stated goal
- [ ] Docs (`SKILL.md`, `references/`, `README.md`) updated if behavior changed
- [ ] No copied text between docs (one source of truth per fact)

## Tradeoffs / notes

Anything a reviewer should weigh.
