# Contributing to project-harness

Thanks for your interest in improving project-harness. This skill exists to keep
agentic software work from drifting, so the bar for changes is the same one the
skill enforces: **every rule wants an executed backstop, and every guard ships a
plant test.** Contributions that add behavior without a way to prove it fires will
be asked to add one.

## Ground rules (the same principles the skill installs)

Please keep changes aligned with the design principles in the [README](README.md#design-principles):

- **Prompting is not enforcing.** If you add a rule, note or build its executable backstop.
- **Every guard ships a plant test.** A new hook or check must be fed a fake violation in `scripts/harness_selftest.py` and must reject it.
- **Right-size, then grow on felt pain.** New machinery should answer "what failure created you?" We favor small, justified additions over speculative features.
- **One source of truth per fact.** Reference by ID or pointer; don't copy text between docs.

## Getting set up

There is no build step and no third-party dependencies. You need:

- `python3` on your PATH (scripts are Python **standard-library only** — please keep them that way).
- `git` (recommended; audits use history).

Clone your fork and you're ready:

```bash
git clone https://github.com/<your-username>/project-harness.git
cd project-harness
```

## Running the self-test

The self-test is the project's proof of life. It stands up a synthetic install, feeds
every installed guard a fake violation, and fails unless each one rejects it:

```bash
python3 scripts/harness_selftest.py .
```

If you change the behavioral core rules in `assets/templates/CLAUDE.md`, regenerate the
pinned hash so the audit's "rules unweakened" check stays honest:

```bash
python3 scripts/harness_selftest.py --hash-rules .
```

Before opening a pull request, make sure:

1. `python3 scripts/harness_selftest.py .` passes.
2. Every `.py` file still compiles: `python3 -m py_compile scripts/**/*.py`.
3. Any new guard has a corresponding plant test that provably fires.

## Filing issues

Use the issue templates. The most useful bug reports include the surface you ran on
(Claude Code, Cowork, Claude Desktop), the mode (setup / audit / dispatch), and the
exact self-test or audit output. Feature requests are most persuasive when they name
the concrete failure the machinery would have caught.

## Pull requests

1. Fork the repo and create a topic branch off `main`.
2. Make focused, surgical changes — every changed line should trace to the stated goal.
3. Update the relevant docs (`SKILL.md`, `references/`, `README.md`) if behavior changes.
4. Run the checks above and describe the result in the PR.
5. Fill out the PR template so reviewers can see intent, verification, and tradeoffs.

## Releasing

Releases are lightweight and manual — no build pipeline, no third-party tooling.
The version in `.claude-plugin/plugin.json` is the single source of truth and follows
[Semantic Versioning](https://semver.org/) (bug fix → patch, backward-compatible
behavior → minor, breaking change to templates/hooks/manifest shape → major).

To cut a release:

1. Land the change on `main` via PR (CI runs `scripts/selftest_synthetic.py`).
2. Bump `version` in `.claude-plugin/plugin.json`.
3. Move the `[Unreleased]` notes in [`CHANGELOG.md`](CHANGELOG.md) under a new
   `[X.Y.Z] - YYYY-MM-DD` heading and update the compare links at the bottom.
4. Commit (`chore(release): vX.Y.Z`), then tag and push:
   ```bash
   git tag -a vX.Y.Z -m "vX.Y.Z"
   git push origin main --tags
   ```
5. Cut a GitHub Release from the tag, pasting that version's changelog section.

The tag **must** match `plugin.json`'s `version` — that pairing is the contract for
anyone installing the plugin from a pinned ref.

By contributing, you agree that your contributions are licensed under the project's
[MIT License](LICENSE).
