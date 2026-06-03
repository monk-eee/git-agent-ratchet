# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Multi-language support for Ratchet A.** Duplicate-helper detection
  now scans TypeScript / JavaScript (`.ts`, `.tsx`, `.js`, `.jsx`,
  `.mjs`, `.cjs`) and C# (`.cs`) in addition to Python. New extractor
  registry under `git_agent_ratchet/ratchets/extractors/` with one
  module per language; each defines its own "helper-shaped" predicate
  (Python: leading underscore; TS/JS: unexported top-level function or
  arrow const; C#: `private` method). New `--lang` flag on the hook
  restricts scanning to a subset of registered languages. 35 new
  extractor tests; total suite now 137 tests at 100% coverage.
- Default exclude list grows to skip `node_modules`, `bin`, `obj`,
  `.venv`, `venv`, `dist`, `build` so the scanner does not chase build
  output or vendor trees in polyglot repos.
- **Ratchet D -- `ratchet-max-file-lines`.** Per-file Python line-count
  ratchet. Records the total overage across all files larger than `--max`
  (default 350) in a separate baseline; metric is allowed to shrink, never
  grow. New scanner module
  `git_agent_ratchet/ratchets/max_file_lines.py`, hook entry
  `git_agent_ratchet/hooks/max_file_lines.py`, console script
  `ratchet-max-file-lines`, `max-file-lines` subcommand on the unified CLI.
  25 new tests; total suite now 102 tests at 100% line + branch coverage.
- GitHub Actions release workflow (`.github/workflows/release.yml`) that
  builds the sdist + wheel on every `v*` tag and publishes to PyPI via
  trusted-publisher OIDC (no long-lived token in the repo). Requires
  one-time PyPI-side publisher configuration documented in the workflow.
- 100% line + branch coverage (`fail_under = 95` in `pyproject.toml`).
- Codecov upload on `ubuntu-latest` + Python 3.12 (`codecov/codecov-action@v4`).
- `codecov.yml` policy file mirrors local gates: 95% project floor
  (matches `fail_under`) and 80% patch floor (matches `diff-cover`).
- `diff-cover` PR gate: PR-changed lines must be >= 80% covered.
- CodeQL security analysis workflow (`security-and-quality` query suite).
- Dependabot config: weekly Python + GitHub Actions updates, grouped.
- `SECURITY.md` with private-vulnerability reporting flow and threat model.
- `CHANGELOG.md` (this file).
- Pull-request template and bug-report / feature-request issue templates.

### Changed
- README now displays Codecov coverage badge.
- README, downstream `.pre-commit-hooks.yaml`, and the CLI all advertise
  four ratchets instead of three.
- `DEVELOPERS.md` "Known soft rules" no longer lists the 350-line
  per-file limit -- it is now mechanically enforced by Ratchet D.

## [1.0.0] - 2026-06-03

### Added
- Three pre-commit hooks: `ratchet-no-duplicate-helpers` (Ratchet A, AST
  scan), `ratchet-deny-agent-chatter` (Ratchet B, regex scan),
  `ratchet-anti-bypass` (Ratchet C, env + path inspection).
- Unified `git-agent-ratchet` CLI dispatcher with `--version` and three
  subcommands.
- JSON baseline registry with shrink-only invariant; auto-rewritten by the
  hook on cleanup, blocked from growing without `HUMAN_RATCHET_BYPASS_KEY`.
- `ratchet-allow: agent_chatter` per-line escape marker for legitimate
  quotations of forbidden phrases in docs and tests.
- GitHub Actions CI: test matrix (ubuntu / windows / macos x py 3.10 / 3.11
  / 3.12), ruff lint + format, pre-commit dogfood, build sdist + wheel.
- Documentation: README with seven badges, `AGENTS.md` (agent-facing index),
  `DEVELOPERS.md` (human-facing dev guide), `CONTRIBUTING.md`, `docs/spec.md`
  (the contract), `docs/TODO.md` (roadmap + known bugs).
- 76 tests covering every hook entry point, every ratchet, the baseline
  registry, the unified CLI, and the `python -m git_agent_ratchet`
  entrypoint.

### Security
- Ratchet C never logs the bypass key value; only its presence is
  acknowledged in failure output (regression-tested).

[Unreleased]: https://github.com/monk-eee/git-agent-ratchet/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/monk-eee/git-agent-ratchet/releases/tag/v1.0.0
