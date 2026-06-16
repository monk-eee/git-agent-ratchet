# DEVELOPERS.md

Day-to-day reference for working on `git-agent-ratchet`. The contract is in
[docs/spec.md](docs/spec.md). The agent-facing index is [AGENTS.md](AGENTS.md).
This file is the human view.

---

## Getting started

```bash
git clone https://github.com/monk-eee/git-agent-ratchet.git
cd git-agent-ratchet
make setup
make test
```

`make setup` runs `uv sync --all-extras` and installs the local pre-commit
hook chain. If you bootstrapped without `make`, run `uv run pre-commit
install` yourself or the hooks are silently bypassed.

---

## Common workflows

| Task | Command |
| --- | --- |
| Run the full test suite | `make test` |
| Run tests with coverage | `make test-cov` |
| Format + auto-fix lint | `make format` |
| Verify lint clean | `make lint` |
| Dogfood all four ratchets | `make ratchet` |
| Re-seed the duplicates baseline (after a real cleanup) | `make seed-baseline` |
| Run pre-commit against every file | `uv run pre-commit run --all-files` |

If `make ratchet` fails on a clean tree, the last change is wrong. That is
the entire CI loop.

---

## Repository layout

```
git_agent_ratchet/        # The package (flat, no src/)
  baseline.py             # JSON registry persistence
  cli.py                  # `git-agent-ratchet <sub>` dispatcher
  ratchets/               # Pure scanners
  hooks/                  # Pre-commit entry points (call the scanners)
config/ratchets/          # Baseline JSON files
docs/                     # spec.md (contract) + TODO.md
tests/                    # pytest suite
.github/workflows/        # CI
```

---

## Mechanical gates

| Rule | Gate |
| --- | --- |
| No duplicate private helpers (Python / TS / JS / C#) | `ratchet-no-duplicate-helpers` |
| No agent chatter in committed text | `ratchet-deny-agent-chatter` |
| No agent-driven mutation of ratchet config | `ratchet-anti-bypass` |
| Per-file line count <= 350 (sum of overages) | `ratchet-max-file-lines` |
| No cross-module imports of `_private` names | `ratchet-no-cross-module-private-import` |
| No `print()` outside allowlisted shims (use `logging`) | `ratchet-no-print-outside-allowlist` |
| No expedient-path comment markers | `ratchet-no-temporary-comments` |
| Lint + format clean | `ruff check` + `ruff format --check` |
| Hygiene (EOF, whitespace, line endings, merge markers, large files) | `pre-commit-hooks` |
| Tests pass on Linux / Windows / macOS x 3.10 / 3.11 / 3.12 | GitHub Actions `test` matrix |

All gates run locally via `pre-commit` and again in CI. Local first; CI is
the safety net, not the first line of defence.

---

## Known soft rules

Rules in [AGENTS.md](AGENTS.md) that are *not* mechanically enforced yet --
listed here so the gap is public and the next gate is easy to spot.

- **Regression test required per bug fix.** Honour system; reviewed in PRs.

When a soft rule fires twice in production, it graduates to a mechanical
gate. The pattern is always: ratchet first, then prose, then this table
loses an entry.

---

## Releasing

Releases are tags on `main` of the form `vX.Y.Z`. The
`.pre-commit-hooks.yaml` manifest is consumed via `rev: vX.Y.Z` in
downstream `.pre-commit-config.yaml` files, so tags must:

1. Be signed (`git tag -s vX.Y.Z -m "release X.Y.Z"`).
2. Match `git_agent_ratchet/_version.py::__version__` exactly.
3. Be created on a commit where the full CI matrix is green.

A future automation job will build the sdist + wheel from a tag and
publish to PyPI; until then, releases are tag-only and consumers pin by
git rev.

---

## Bypass etiquette (humans only)

`HUMAN_RATCHET_BYPASS_KEY` exists so a human operator can land a
genuine exception (e.g. landing the cleanup commit that legitimately
reduces a baseline mid-merge). Use it like this:

```bash
uv run python -c "import os, subprocess; env=dict(os.environ, HUMAN_RATCHET_BYPASS_KEY='i-am-a-human-and-i-know-what-i-am-doing'); subprocess.check_call(['git','commit','-m','cleanup: extract _safe_load_or_default -> baseline.py'], env=env)"
```

Never put the key in `.env`, a CI secret, or any persistent shell
profile. The point of the variable is that it is set deliberately, for
this commit, and then unset.

If you are an LLM agent reading this, the bypass key is not for you.
Surface the blocker to your operator.
