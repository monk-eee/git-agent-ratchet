# TODO

Progress tracker, known gaps, and triage list.

## Shipped

- [x] docs/spec.md v1.0.0 -- the contract
- [x] Package scaffold (`git_agent_ratchet/`, flat layout, hatchling)
- [x] Baseline registry (`Baseline` dataclass + JSON I/O)
- [x] Ratchet A (duplicate helpers, AST scan)
- [x] Ratchet B (agent chatter, regex scan)
- [x] Ratchet C (anti-bypass, env + protected-files guard)
- [x] Three hook entry points + unified CLI dispatcher
- [x] `.pre-commit-hooks.yaml` manifest for downstream consumers
- [x] `.pre-commit-config.yaml` (this repo dogfoods its own ratchets)
- [x] README.md (long-form, with HUMANS.md framing)
- [x] AGENTS.md (mechanical enforcement table)
- [x] DEVELOPERS.md (human contributor view)
- [x] Test suite covering baseline, ratchets, hooks, CLI
- [x] Makefile (`setup`, `test`, `lint`, `format`, `ratchet`, `seed-baseline`)
- [x] GitHub Actions CI (test matrix + lint + pre-commit + build)
- [x] LICENSE (MIT)
- [x] 100% line + branch coverage (`fail_under = 95` in pyproject)
- [x] Codecov upload + badge
- [x] diff-cover PR gate (>= 80% on changed lines)
- [x] CodeQL security analysis workflow
- [x] Dependabot config (weekly pip + github-actions, grouped)
- [x] SECURITY.md (private vulnerability reporting + threat model)
- [x] CHANGELOG.md (Keep a Changelog format)
- [x] Pull request template + bug / feature issue templates
- [x] Ratchet D (max-file-lines) -- scanner + hook + CLI + tests + dogfood
- [x] PyPI publish workflow (trusted publisher, OIDC, environment `pypi`)
- [x] Example downstream consumer layout under `examples/downstream/`
- [x] Pluggable language support for Ratchet A (Python AST + TypeScript/JavaScript
      regex + C# regex extractors, `--lang` filter, registry under
      `git_agent_ratchet/ratchets/extractors/`)
- [x] Tagged + released v1.1.0 to PyPI via trusted publisher
- [x] Ratchet E (no-cross-module-private-import) -- AST scanner + hook + CLI +
      tests + dogfood; flags `from pkg.mod import _foo` and bars the count
      from growing
- [x] Ratchet F (no-print-outside-allowlist) -- AST scanner + hook + CLI +
      tests + dogfood; graduates the soft `logging.getLogger(__name__)` rule
      in DEVELOPERS.md, with `--allow-prefix` for stderr-writing shims
- [x] Ratchet G (no-temporary-comments) -- cross-language regex scanner + hook
      + CLI + tests + dogfood; catches `for now`, `back-compat`, `transitional
      bridge`, `TODO: remove once`, `HACK: fix later` markers; per-line
      `ratchet-allow: temporary_comments` opt-out
- [x] Shared `iter_python_files` extracted to `git_agent_ratchet/paths.py` so
      Ratchets D / E / F share one walker (Ratchet A caught the fork on the
      seven-ratchet expansion)

## Next

- [x] Configure PyPI trusted publisher on pypi.org for `git-agent-ratchet`
      (owner `monk-eee`, repo `git-agent-ratchet`, workflow `release.yml`,
      environment `pypi`) -- one-time, requires PyPI maintainer access
- [x] Example downstream consumer repo to validate the published manifest
- [x] Pluggable language support for Ratchet A (Python, TypeScript/JavaScript, C#)
- [x] Enable GitHub Discussions (referenced from ISSUE_TEMPLATE/config.yml)
- [x] Configure Codecov repo secret `CODECOV_TOKEN` on monk-eee/git-agent-ratchet

## Known soft rules

See [DEVELOPERS.md](DEVELOPERS.md) for the table. Each entry there is a
candidate ratchet.

## Known bugs

- [FIXED] `anti_bypass._normalize` used `str.lstrip("./")`, which treats
  `./` as a *character set* and stripped any leading `.` or `/`. Result:
  dotfile paths in the gate output were mangled (`.pre-commit-hooks.yaml`
  -> `pre-commit-hooks.yaml`, `.env` -> `env`). Enforcement still worked
  (both sides of the comparison were mangled identically) but the
  diagnostic was confusing. Fix: strip only the literal `./` prefix.
  Regression test:
  `tests/test_anti_bypass_regressions.py::test_normalize_preserves_leading_dot_in_dotfiles`
  + `::test_blocked_decision_reports_dotfile_with_leading_dot_intact`.

- [FIXED] `print_outside_allowlist.is_allowed` ended its match with
  `or label.startswith(norm)`, a bare string-prefix check. A prefix like
  `pkg/cli` wrongly allow-listed `pkg/client.py` (and `src/util` allowed
  `src/utility.py`), silently exempting files the operator never intended
  to allowlist -- so stray `print()` calls in those files went undetected.
  Fix: match only the exact file or a directory boundary (`norm + "/"`).
  The same function's `str.lstrip("./")` was routed through the shared
  `paths.strip_dot_slash` for consistency (that part was benign -- the
  stripping was symmetric on both sides of the comparison). Regression
  test: `tests/test_print_outside_allowlist_regressions.py::test_is_allowed_does_not_match_bare_string_prefix`.

## Known duplicates

_Empty. Ratchet A enforces this mechanically; any duplicate that survives
a commit lives here with a note explaining why the cleanup hasn't landed
yet._
