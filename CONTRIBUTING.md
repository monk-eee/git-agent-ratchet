# Contributing to git-agent-ratchet

Thanks for caring enough to read this. The bar to land a change here is
low on ceremony and high on principle. The whole point of this codebase
is that rules are mechanical, so contributing follows the same logic --
the gates do most of the gatekeeping.

If you're an LLM agent reading this on behalf of a human operator,
[AGENTS.md](AGENTS.md) is the file written for you. Read that one first;
this one assumes a human is at the keyboard.

---

## TL;DR

1. Fork, branch, code.
2. `make setup` once. `make test` and `make lint` before every commit.
3. Open a PR against `main`. CI runs the same gates you ran locally.
4. One commit = one meaningful unit of work. Squash on merge if you wandered.
5. If you fix a bug, add a regression test in the same commit.
6. If you change a hook's gate behaviour, update [docs/spec.md](docs/spec.md)
   in the same commit.

---

## Local setup

```bash
git clone https://github.com/monk-eee/git-agent-ratchet.git
cd git-agent-ratchet
make setup     # uv sync --all-extras + pre-commit install
make test      # 71+ tests, runs in well under a second
```

If `make` is not available on your box (default Windows), the underlying
commands are all in [Makefile](Makefile) -- copy them out and run them
directly with `uv run`. Everything works through `uv`; do not use `pip`.

---

## The development loop

```bash
# Edit code.
make format       # ruff check --fix + ruff format
make test         # full pytest
make ratchet      # dogfood the three hooks against this repo
git add <named-files-only>
git commit        # pre-commit runs everything in `make ratchet` + lint
```

There is no "I'll fix lint later" mode. Every commit goes through
pre-commit. Every PR goes through CI. CI is the same script as
`pre-commit run --all-files` plus the test matrix.

---

## What "good" looks like

These are the patterns the codebase rewards. None of them are unique to
this repo -- they are just the engineering bar applied consistently.

### Tests are mandatory, not aspirational
Every shipped behaviour has a test. Bug fixes get a regression test in
`tests/test_<module>_regressions.py`. The test must fail against the
unfixed code and pass against the fix; confirm both directions before
committing.

### Code reuse is enforced by Ratchet A
Before writing a new helper, grep the package for the verb. If something
already does it, use it. If a near-miss exists, extend it. The duplicate
helpers ratchet will eventually catch you, but the goal is for the
review to catch you first.

### Objects over module-mutable globals
The `Baseline` dataclass is the canonical example -- it owns a path and
a dict, and tests pass `tmp_path` straight to the constructor. If you
catch yourself wanting `monkeypatch.setattr(module, "SOMETHING", x)` in
a test, the production code has a missing seam. Fix the seam.

### Dependency injection over env reads
Functions that read environment take it as an optional parameter
(`def f(env: dict[str, str] | None = None)`). The default reads
`os.environ`; tests pass their own dict. No monkeypatching needed.

### Frozen dataclasses for value objects
`DuplicateHelper`, `ChatterMatch`, `BypassDecision` -- all frozen.
Mutation is a code smell at this layer.

### Hooks write failure output to stderr
Pre-commit captures stderr directly to the developer. Use
`print(..., file=sys.stderr)` for user-facing failure messages; that is
the *one* allowed use of `print` in this codebase. For diagnostics
inside scanner logic, use `logging.getLogger(__name__)`.

---

## What "bad" looks like

These are the patterns the codebase will push back on. Sometimes through
review, sometimes through a hook, sometimes through a failing test.

- Adding a fallback to keep legacy callers working instead of migrating
  the callers.
- Tests that monkeypatch a production module attribute (the production
  module has a missing seam).
- A `# TODO: remove once X migrates` comment in a commit that does not
  also do X.
- A new helper named `_load_*_or_default`, `_safe_*`, `_run_*`,
  `_retry_*`, `_atomic_*` without first checking whether the existing
  package already provides it.
- `git add -A` or `git add .` -- always stage named paths.
- `git commit --no-verify` -- the hooks exist for a reason. If a hook
  is wrong, fix the hook.
- Editing `config/ratchets/duplicates.json` by hand to make a commit
  pass. Ratchet C will block it; that is its job.

---

## Branching, commits, PRs

- **Branches.** `feat/<short-handle>`, `fix/<short-handle>`,
  `cleanup/<short-handle>`, `docs/<short-handle>`. Lowercase, hyphens.
- **Commit messages.** Subject line: present tense, no trailing period,
  72 chars max. Body wrap at 80. Reference the issue or spec section
  when relevant.
- **One commit = one unit of work.** Squash exploratory commits before
  opening the PR.
- **PR description.** What changed, why, how it was verified. If the
  change touches a hook's gate behaviour, name the spec section and
  the test that proves the new behaviour.

---

## Adding a new ratchet

If you have a rule that keeps getting broken in your `AGENTS.md`, the
project is happy to ship the gate for it. The shape:

1. **Pure scanner** in `git_agent_ratchet/ratchets/<name>.py`. No I/O
   beyond reading the file system. Returns a list of typed match objects.
2. **Hook entry point** in `git_agent_ratchet/hooks/<name>.py`. Parses
   argv with `argparse`, calls the scanner, writes failure output to
   stderr, returns an exit code.
3. **CLI registration** in `git_agent_ratchet/cli.py::SUBCOMMANDS`.
4. **Console script** in `pyproject.toml::[project.scripts]` and a hook
   entry in `.pre-commit-hooks.yaml`.
5. **Tests** in `tests/test_<name>.py` (pure scanner) and
   `tests/test_hooks_<name>.py` (CLI surface).
6. **Spec entry** in `docs/spec.md` describing the target failure mode,
   the gate rule, and the bypasses you explicitly want forbidden.
7. **AGENTS.md table row** in the "Mechanical enforcement" table.

A new ratchet ships with all seven pieces or it does not ship.

---

## Reporting bugs

Open an issue with:
- What you observed.
- What you expected.
- A minimal repro: a small file or two and the exact command you ran.
- The exit code and the full stderr.

If you can also write the regression test, even better -- attach it as a
patch. The bar for accepting a fix is "this fails against `main` and
passes against the patch".

---

## Conduct

Be kind. Be technical. Disagree with the code, never with the person.
If a review feels personal, step away for an hour and come back. This
is one of those tiny weird projects that only works if the people
working on it actually want to. Don't break that.

---

## Credits

The framing of this project owes a lot to a single article -- *HUMANS.md
-- the missing piece of the agentic puzzle* by Lyndon Swan. The core
insight (rules erode under context length; convert the rules to
mechanical gates) is theirs. See the README for the full credit and the
six-step checklist that drove the design.
