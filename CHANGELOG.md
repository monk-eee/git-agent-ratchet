# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.3.0] - 2026-06-16

### Added
- **Ratchet H -- `ratchet-dont-use-powershell`** (invariant gate).
  Blocks command-like PowerShell usage in staged text, including
  executable invocations (`powershell` / `pwsh` with switches), `.ps1`
  command references, common cmdlets, and `$env:` prefixes.
  Introduces scanner module
  `git_agent_ratchet/ratchets/powershell_usage.py`, hook entry point
  `git_agent_ratchet/hooks/dont_use_powershell.py`, console script
  `ratchet-dont-use-powershell`, and unified CLI subcommand
  `dont-use-powershell`.

### Documentation
- Codified the **anti-rot contract** that governs when a rule earns a
  ratchet. README gains a "When does a rule earn a ratchet (and how this
  avoids rot)" section and `docs/spec.md` gains section 4 "When a Rule
  Earns a Ratchet (Anti-Rot Contract)": the four-bar test for debt
  ratchets (fires often / silent in review / pays down through normal work
  / cheap early-expensive late), the debt-ratchet vs invariant-gate
  distinction, and the shrink-only / loud-by-default / retirement
  properties that keep a ratchet from degenerating into a sinecure.
- Updated all user-facing docs for the eight-ratchet surface:
  `README.md`, `AGENTS.md`, and `docs/spec.md` now consistently include
  Ratchet H and release version `v1.3.0` references.

## [1.2.0] - 2026-06-15

### Added
- **Ratchet E -- `ratchet-no-cross-module-private-import`**
  (`private_imports.json`). AST scan that blocks importing a private
  (`_`-prefixed) name across module boundaries -- `from pkg.mod import
  _foo` and `import pkg._foo`. Relative imports and dunders are ignored.
  New scanner `git_agent_ratchet/ratchets/cross_module_private_import.py`,
  hook `git_agent_ratchet/hooks/no_cross_module_private_import.py`, console
  script `ratchet-no-cross-module-private-import`, and
  `no-cross-module-private-import` subcommand on the unified CLI.
- **Ratchet F -- `ratchet-no-print-outside-allowlist`**
  (`print_calls.json`). AST scan for `print(...)` calls outside
  allowlisted path prefixes (use `logging` everywhere else; stderr shims
  under `git_agent_ratchet/hooks` and `git_agent_ratchet/cli.py` are
  allowlisted via `--allow-prefix`).
- **Ratchet G -- `ratchet-no-temporary-comments`**
  (`temporary_comments.json`). Regex scan for expedient-path comment
  markers (`for now`, `back-compat`, `TODO: remove once`, `HACK: fix
  later`, transitional bridges) across `.py/.ts/.tsx/.js/.jsx/.cs/.go/`
  `.rs/.java/.kt`, with a `ratchet-allow: temporary_comments` per-line
  escape marker.

### Changed
- Extracted `git_agent_ratchet/hooks/gate.py::run_ratchet_gate` as the
  single seed / trip / ratchet-down / equal implementation. Ratchets A,
  D, E, F, and G all dispatch through it, removing the inline-duplicated
  control flow that each baseline-gate hook previously carried.
- Added shared path helpers `paths.strip_dot_slash` and
  `paths.iter_python_files`. `strip_dot_slash` replaces a
  `str.lstrip("./")` character-set misuse (which mangled dotfile paths
  such as `.pre-commit-hooks.yaml`) in `anti_bypass._normalize` and the
  new print scanner.
- README, CLI, and `.pre-commit-hooks.yaml` now advertise seven ratchets.

### Fixed
- `print_outside_allowlist.is_allowed` matched allow-prefixes by bare
  string prefix (`label.startswith(norm)`), so a prefix like `pkg/cli`
  wrongly allow-listed `pkg/client.py` and let stray `print()` calls go
  undetected. It now matches only the exact file or a directory boundary
  (`norm + "/"`). Regression-tested.

## [1.1.0] - 2026-06-03

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

### Fixed
- CI: `pre-commit` dogfood job now sets `SKIP=ratchet-anti-bypass`.
  Ratchet C is a staged-set commit gate; `--all-files` mode fed every
  protected file in the repo to it and tripped it unconditionally on
  every run, blocking the build matrix. Anti-bypass continues to run
  on developer machines at commit time, which is the only context
  where the gate has meaning.

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

[Unreleased]: https://github.com/monk-eee/git-agent-ratchet/compare/v1.3.0...HEAD
[1.3.0]: https://github.com/monk-eee/git-agent-ratchet/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/monk-eee/git-agent-ratchet/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/monk-eee/git-agent-ratchet/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/monk-eee/git-agent-ratchet/releases/tag/v1.0.0
