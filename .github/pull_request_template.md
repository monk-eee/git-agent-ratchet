<!-- Thanks for opening a pull request against git-agent-ratchet. Keep diffs
small, scoped, and validated. See CONTRIBUTING.md for the full bar. -->

## What this PR does

<!-- One paragraph. The reviewer should not have to read the diff to know
the intent. -->

## Why

<!-- Link the AGENTS.md / docs/spec.md / docs/TODO.md line item, or the
issue, or describe the failure mode this fixes. -->

## Type of change

<!-- Check all that apply. -->

- [ ] New ratchet
- [ ] Bug fix (regression test included, see CONTRIBUTING.md)
- [ ] Documentation
- [ ] Refactor (no behaviour change)
- [ ] CI / repo hygiene
- [ ] Dependency update

## Checklist

- [ ] `make test` passes locally (76+ tests, 100% coverage maintained).
- [ ] `make lint` passes locally (ruff check + ruff format --check).
- [ ] `make ratchet` passes against this repo (all three ratchets dogfood).
- [ ] If a bug was fixed, a regression test in
      `tests/test_<module>_regressions.py` was added and verified to fail
      against the un-fixed code and pass against the fix.
- [ ] If a new feature shipped, `docs/TODO.md`, `README.md`, and
      (where relevant) `AGENTS.md` + `docs/spec.md` were updated in the
      same commit, per CONTRIBUTING.md.
- [ ] `CHANGELOG.md` updated under `## [Unreleased]`.
- [ ] No `--no-verify`, no `git stash`, no `git add -A` was used to land
      this work (AGENTS.md, NON-NEGOTIABLE).

## Bypass disclosure (delete if not applicable)

If this PR's commit history includes any commit landed with
`HUMAN_RATCHET_BYPASS_KEY` set, explain here:

- Which commit
- Which protected file was mutated
- Why the human override was correct
