# Changelog

All notable changes to project-harness are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres
to [Semantic Versioning](https://semver.org/spec/v2.0.0.html). The version in
`.claude-plugin/plugin.json` is the source of truth; each release is a matching
`vX.Y.Z` git tag.

## [Unreleased]

## [1.0.1] - 2026-07-09

### Fixed

- **Self-test now runs the wired settings command, not just the hook file.** A hook
  weakened by exit-code masking in `.claude/settings.json` (e.g. `… || true`) fired
  correctly when invoked directly but was swallowed at runtime; the self-test missed
  it. `harness_selftest.py` now executes the actual configured command with each
  plant payload, so a masked wiring is caught as a hollow guard.
- **`secret_scan` credential coverage.** Added AWS STS temporary keys (`ASIA…`) and
  `access_key`/`private_key` secret names; the assignment detector now sees through a
  type annotation (`api_key: str = "…"`); and placeholder sanctioning is judged on the
  literal's residue so a real secret with a `${…}` glued on is no longer shielded.
- **`status_guard` matching.** The gated-status check is now case-insensitive and
  tolerant of whitespace around the colon (closing the `Status:` / `status :` bypass)
  and is scoped to a frontmatter-shaped line, so prose that merely contains
  `status: done …` no longer trips a false positive.
- **`gen_status` table safety.** Cell values containing `|` are escaped so a story
  title or ref can't corrupt the generated Markdown table.
- **`gen_dashboard` latest-audit selection.** The panel now considers only dated
  `audit-YYYY-MM-DD.md` files, so a non-dated draft can't sort last and shadow the
  real latest audit.

## [1.0.0] - 2026-07-08

### Added

- Initial public release: setup / audit / dispatch modes, tiered templates, the
  harness self-test with plant tests, PreToolUse enforcement hooks (`protected_paths`,
  `secret_scan`, `status_guard`), the synthetic tier-M install test, and the opt-in
  self-contained HTML status dashboard. Packaged as an installable Claude Code plugin.

[Unreleased]: https://github.com/Entuvo/project-harness/compare/v1.0.1...HEAD
[1.0.1]: https://github.com/Entuvo/project-harness/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/Entuvo/project-harness/releases/tag/v1.0.0
