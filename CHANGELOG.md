# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- 100% line + branch coverage (`fail_under = 95` in `pyproject.toml`).
- Codecov upload on `ubuntu-latest` + Python 3.12 (`codecov/codecov-action@v4`).
- `diff-cover` PR gate: PR-changed lines must be >= 80% covered.
- CodeQL security analysis workflow (`security-and-quality` query suite).
- Dependabot config: weekly Python + GitHub Actions updates, grouped.
- `SECURITY.md` with private-vulnerability reporting flow and threat model.
- `CHANGELOG.md` (this file).
- Pull-request template and bug-report / feature-request issue templates.

### Changed
- README now displays Codecov coverage badge.

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
