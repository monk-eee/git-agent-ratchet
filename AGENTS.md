# AGENTS.md -- git-agent-ratchet Codebase Guide for AI Agents

---

### Core coding philosophy

> "The code you write makes you a programmer.
> The code you delete makes you a good one.
> The code you don't have to write makes you a great one."
> -- Mario Fusco

Lines of code are a cost, not an asset. The best contribution is often a
smaller diff than you arrived expecting to write -- a delete, a consolidation,
or a one-line addition to an existing helper instead of a new sibling. This
repo enforces that bias mechanically; see "Mechanical enforcement" below.

#### Before-you-write checklist (NON-NEGOTIABLE)

Run these four checks before writing any helper, utility, or "small" function:

1. **Grep `git_agent_ratchet/` for the verb.** `grep -rn "def <verb>" git_agent_ratchet/`
   -- if anything already does this, use it. If a near-miss exists, extend it
   -- do not fork.
2. **Grep the whole repo for the function name you're about to type.**
   `grep -rn "def _your_name_here" .` -- if it exists outside `tests/`, that's
   the existing implementation. Import it or extract both to a shared module
   under `git_agent_ratchet/`.
3. **Check the red-flag prefixes.** If your function starts with `_run_*`,
   `_safe_*`, `_resolve_*`, `_load_*_or_default`, `_no_prompt_*`, `_retry_*`,
   `_copy_*`, `_walk_*`, `_atomic_*`, `_canonical_*` -- stop. These are the
   exact patterns that get forked. Check `git_agent_ratchet/` again, harder.
4. **Run Ratchet A locally.**
   `uv run git-agent-ratchet no-duplicate-helpers --dir git_agent_ratchet --baseline config/ratchets/duplicates.json`.
   It exits non-zero with a per-name report if your change introduces or grows
   a duplicate. The pre-commit hook wired in `.pre-commit-config.yaml` runs
   the same check on every commit; do not rely on CI for it.

If you find yourself about to write the same helper twice in one session, the
second occurrence is the signal to extract immediately. Do not "do it once
more and clean up later". Later does not arrive.

#### Mechanical enforcement (this repo dogfoods itself)

This codebase ships the very ratchets that guard it. Every prose rule below
that ends in "NON-NEGOTIABLE" must map to a mechanical gate in
[.pre-commit-config.yaml](.pre-commit-config.yaml). If a rule cannot be
mechanically enforced, it goes in the "Known soft rules" section of
[DEVELOPERS.md](DEVELOPERS.md) so the gap is public.

| Rule | Programmatic gate | Source |
| --- | --- | --- |
| No duplicate private helpers | `ratchet-no-duplicate-helpers` | [git_agent_ratchet/hooks/no_duplicate_helpers.py](git_agent_ratchet/hooks/no_duplicate_helpers.py) |
| No agent chatter in any file | `ratchet-deny-agent-chatter` | [git_agent_ratchet/hooks/deny_agent_chatter.py](git_agent_ratchet/hooks/deny_agent_chatter.py) |
| No agent self-bypass of the ratchets | `ratchet-anti-bypass` | [git_agent_ratchet/hooks/anti_bypass.py](git_agent_ratchet/hooks/anti_bypass.py) |
| Per-file line count <= 350 (sum of overages) | `ratchet-max-file-lines` | [git_agent_ratchet/hooks/max_file_lines.py](git_agent_ratchet/hooks/max_file_lines.py) |
| No cross-module imports of `_private` names | `ratchet-no-cross-module-private-import` | [git_agent_ratchet/hooks/no_cross_module_private_import.py](git_agent_ratchet/hooks/no_cross_module_private_import.py) |
| No `print()` outside allowlisted shims (use `logging`) | `ratchet-no-print-outside-allowlist` | [git_agent_ratchet/hooks/no_print_outside_allowlist.py](git_agent_ratchet/hooks/no_print_outside_allowlist.py) |
| No expedient-path comment markers (`for now`, `back-compat`, `TODO: remove once`, `HACK: fix later`) | `ratchet-no-temporary-comments` | [git_agent_ratchet/hooks/no_temporary_comments.py](git_agent_ratchet/hooks/no_temporary_comments.py) |
| Lint + format clean | `ruff` (check + format --check) | `pyproject.toml [tool.ruff]` |
| Trailing whitespace / EOF / line endings / merge markers / large files | `pre-commit-hooks` | `.pre-commit-config.yaml` |

- The baseline registry lives at [config/ratchets/duplicates.json](config/ratchets/duplicates.json).
  It is **allowed to shrink** (cleanups) but never grow. Each cleanup gets its
  own commit (`cleanup: extract _name -> git_agent_ratchet/...`) and the
  ratchet rewrites the registry with the smaller count, staging the diff.
- Do not add an ignore-list to the scanner. The fix is always extraction.
- Do not edit `config/ratchets/duplicates.json` by hand to make a commit pass.
  Ratchet C will block it; that is the point.

---

## What is this repo?

`git-agent-ratchet` is a small Python package that ships three pre-commit hooks
designed to keep LLM coding agents on rails. The premise (full version in
[docs/spec.md](docs/spec.md)): prose instructions in `AGENTS.md` or `CLAUDE.md`
experience silent rule erosion over long multi-turn context windows; agents
follow the path of least technical resistance. The fix is to convert each
prose rule into a deterministic gate at commit time, so the *cost profile* of
breaking the rule changes -- the rule itself does not need to be re-asserted
every turn.

The three hooks:

1. **Ratchet A -- `no-duplicate-helpers`.** AST scan for private/semi-private
   top-level functions that appear in two or more files. Count is tracked in a
   JSON baseline; the count may shrink or stay flat, never grow.
2. **Ratchet B -- `deny-agent-chatter`.** Regex scan for conversational
   preamble/postscript leaking into source files ("Sure, I can help with...", <!-- ratchet-allow: agent_chatter -->
   "As an AI, ...", "I have successfully updated...", "Now let me check the <!-- ratchet-allow: agent_chatter -->
   docs..."). Any match is a hard block.
3. **Ratchet C -- `anti-bypass`.** Blocks mutations to the ratchet config
   files themselves unless `HUMAN_RATCHET_BYPASS_KEY` is set in the
   environment. Detects common automated-agent env signatures
   (`CURSOR_AGENT`, `CLAUDECODE`, `AIDER`, `COPILOT_AGENT`, ...).

The full design contract is [docs/spec.md](docs/spec.md). The CLI surface is
in [git_agent_ratchet/cli.py](git_agent_ratchet/cli.py).

---

## Vibe Coding Rules (Mandatory for all AI agents)

### Prime directive (READ FIRST, OVERRIDES EVERYTHING BELOW)
**Do the right thing, not the expedient thing.** When a clean design and a
quick hack both reach green tests, pick the clean design. When fixing one test
the right way would require updating fifteen other tests, update the fifteen
tests -- do not add a back-compat shim, a transitional bridge, a "for now"
indirection, or a `_current_*()` helper that hides the legacy pattern. Those
shortcuts calcify. They get committed with TODO comments that never get
resolved, and the next agent inherits two ways to do the same thing forever.

Concrete tells that you are about to take the expedient path:
- "I'll add a fallback so legacy callers keep working" -- no, migrate the
  legacy callers.
- "Tests monkeypatch the old constant; I'll make the new code read both" --
  no, update the tests.
- "This is a bridge until the wider refactor lands" -- the bridge becomes
  permanent. Land the refactor now or do not introduce the new abstraction yet.
- "Touching 15 files for one design change is too much" -- if the design is
  right, touching 15 files is what it costs. Pay it.
- A `# TODO: remove once X migrates` comment in a commit that does not also
  do X.

If the right thing is genuinely too large for one commit, **stop and say so**
-- do not ship the expedient half. Either reduce scope (pick a smaller
right-shaped change) or split into a sequence of right-shaped commits, each
individually principled.

### File discipline
- **Max 350 lines per file.** Split aggressively. Enforced by Ratchet D
  (`ratchet-max-file-lines`); the baseline lives at
  `config/ratchets/file_lines.json` and is allowed to shrink, never grow.
- **Close irrelevant files.** Only keep the current file, its test, and
  related module visible.

### Test-driven workflow (NON-NEGOTIABLE)
- **Tests are the only way we ship.** Every hook, ratchet, and CLI surface
  needs tests.
- **Run tests after every generation.** `uv run pytest -q`. Even minor edits
  can introduce side effects -- regex changes in
  [git_agent_ratchet/ratchets/agent_chatter.py](git_agent_ratchet/ratchets/agent_chatter.py)
  are the canonical footgun.
- **Never skip or disable a test to make CI pass.** Fix the code, not the
  test.
- **Bug fixes require a regression test. No exceptions.**
  - Every fixed bug gets a test in `tests/test_<module>_regressions.py` (one
    file per module).
  - The test name and docstring must describe the bug in plain English: what
    went wrong, what the impact was, what the fix is.
  - The test must FAIL against the un-fixed code and PASS against the fix.
    Confirm both directions before committing. **Do not** use `git stash` to
    verify this (see Multi-agent collaboration); restore the buggy line
    manually, run the test, re-apply the fix.
  - Do not delete regression tests during refactors. They pin subtle
    behaviour that is not obvious from the API surface.
- **Always report bugs and failures, even ones you do not fix in this run.**
  If you notice a bug, a flaky test, an unexpected failure, suspicious
  behaviour, or a latent footgun while doing other work, add an entry to the
  `## Known bugs` section of [docs/TODO.md](docs/TODO.md) before you finish
  the turn. **We never silently drop bugs.** Each entry must describe: (1)
  what you observed, (2) where (file + symbol or test name), (3) impact /
  blast radius if known, (4) whether it was fixed in this run or left for
  later.

### Pre-commit hooks (NON-NEGOTIABLE)
- **Pre-commit runs on every commit.** Never use `--no-verify`.
- **Hooks enforce:** the three ratchets above, plus trailing whitespace,
  end-of-file, YAML/JSON validity, ruff lint+format.
- **Install with `make setup`.** If you bootstrapped with `uv sync` directly,
  run `uv run pre-commit install` once -- otherwise the hooks are silently
  bypassed and lint debt accumulates.

### Git discipline
- **One commit = one meaningful unit of work.** Scoped, validated, tested.
- **Review every diff.** Do not blindly accept generated code.
- **Never edit the ratchet baseline by hand to pass a commit.** Ratchet C
  will block it. The correct response to a tripped ratchet is to remove the
  duplication or chatter, not to grow the registry.

### Doc discipline (NON-NEGOTIABLE)
Every shipped feature must update the three user-facing surfaces in the same
commit (or follow-up commit before the next feature lands). Doc drift here is
treated like a failing test.
- **[docs/TODO.md](docs/TODO.md)** -- record what shipped, or open a new
  entry. Mark prior `[ ]` items `[x]` with the commit / artefact reference.
- **[README.md](README.md)** -- if the change adds, removes, or renames a
  hook, CLI subcommand, or config knob a user passes in
  `.pre-commit-config.yaml`, update the usage section in the same commit.
- **[AGENTS.md](AGENTS.md)** (this file) and **[docs/spec.md](docs/spec.md)**
  -- if you change a ratchet's gate behaviour, update the "Mechanical
  enforcement" table here and the corresponding section in the spec. The
  spec is the contract; this file is the agent-facing index.

If a refactor is purely internal (file split, helper extraction, test
reshuffle), only TODO.md needs to acknowledge it.

### Multi-agent collaboration (READ THIS FIRST)
This repo runs **multiple AI agents concurrently in the same worktree by
design**. The operator does not always fork to a separate clone; they trade
isolation for velocity. You will frequently find another agent has edited
files between your `read_file` and your `commit`. Plan accordingly.

**Rules for every agent (NON-NEGOTIABLE):**
- **Never `git stash`.** Stash interacts catastrophically with concurrent
  worktree edits, pre-commit's own auto-stashing, and Windows file locks. We
  have repeatedly lost staged work and accumulated phantom stash entries when
  agents tried to isolate their changes via stash. Instead: **commit your
  work directly**, even if it's a WIP commit -- a WIP commit can always be
  amended (`git commit --amend`) or squashed later, and it survives every
  failure mode that destroys a stash. If you must verify a regression test
  FAILS against unfixed code, restore the buggy line manually in the editor;
  do not `git stash` the fix.
- **Always `git status --short` before staging or committing.** If you see
  files you did not touch in the staged set, the previous agent left them
  staged for their next commit -- unstage them with `git restore --staged
  <file>` before you `git commit`.
- **Stage explicitly with named paths.** Never `git add -A` or `git add .`.
  Always `git add <specific-files-you-touched>`.
- **Verify the staged set immediately before every commit.** `git diff
  --cached --name-only` MUST list ONLY files you authored this turn -- no
  more, no less. If it doesn't match exactly, `git restore --staged
  <unexpected-file>` before you `git commit`.
- **Stage as late as possible.** Run your edits, run your tests, then `git
  add` + `git diff --cached --name-only` + `git commit` as a tight three-step
  block.
- **Watch the pre-commit auto-stash hijack window.** Pre-commit stashes
  unstaged files before running hooks, then restores them. If a sibling runs
  `git add` DURING that window, the restore + their stage lets THEIR files
  end up committed with YOUR message. Before every `git commit`, verify
  `git status --short` shows ALL files staged-only (capital M in the left
  column, blank in the right). If anything has a right-column M, re-add
  explicitly first.
- **Do not run mass refactors (`ruff --fix .`, sweeping renames, format-the-
  world commits) while another agent is active.** Schedule them for a quiet
  window.
- **Read commits that landed during your turn.** `git log --oneline -5` at
  the start of any non-trivial action. The other agent may have already
  fixed the bug you were about to fix.

### Code reuse (NON-NEGOTIABLE)
- **Always check existing modules before writing a new helper.** Baseline
  load/save belongs in [git_agent_ratchet/baseline.py](git_agent_ratchet/baseline.py).
  Anything that walks Python source belongs near
  [git_agent_ratchet/ratchets/duplicate_helpers.py](git_agent_ratchet/ratchets/duplicate_helpers.py).
  Regex scanners belong near
  [git_agent_ratchet/ratchets/agent_chatter.py](git_agent_ratchet/ratchets/agent_chatter.py).
- **If you find yourself writing a `_load_baseline` / `_normalise_path` /
  `_iter_py_files` / `_signature_for` helper, stop.** Check the modules
  above. If a helper with that purpose already exists, use it. If a
  near-miss exists, extend it rather than forking a new one.
- **When you spot a duplicate during unrelated work, file it.** Add a
  `Known duplicates` entry to [docs/TODO.md](docs/TODO.md). Don't silently
  leave the duplication for the next agent -- Ratchet A will catch it but
  TODO.md captures *why* the duplication appeared so the consolidation
  doesn't just push it back down on the next iteration.

### Code design discipline (NON-NEGOTIABLE)
Pythonic, testable code by default.

- **Prefer objects over module-mutable globals when state has identity.**
  The `Baseline` dataclass in [git_agent_ratchet/baseline.py](git_agent_ratchet/baseline.py)
  is the worked example -- it owns a path and a dict, and tests instantiate
  their own with `tmp_path`. No `monkeypatch.setattr(module, "BASELINE_PATH",
  tmp)` ever.
- **Dependency injection over monkeypatch.** Functions that read env take it
  as a parameter with a default (`def detect_agent_signal(env: dict[str,
  str] | None = None)`). If you find yourself writing
  `monkeypatch.setattr(some_module, "SOME_CONSTANT", x)`, the production
  code has a design bug -- fix the seam, not the test.
- **`@dataclass(frozen=True)` for settings and value objects.** `DuplicateHelper`,
  `ChatterMatch`, `BypassDecision` are the canonical examples -- frozen by
  default, mutation is a code smell.
- **Context managers for resource lifecycles.** If anything starts holding a
  file lock or temp dir, wrap it with `__enter__` / `__exit__` or
  `@contextlib.contextmanager`.
- **Class only when state + behaviour bind.** `Baseline` is a class because
  load / save / get / set share a path + dict. A scanner that takes a root
  and returns a list stays a free function.
- **Anti-patterns to refuse:**
  - Module-level `_CACHE = {}` plus `def get(...)` plus `def clear_cache()`.
    That's a class without the class -- write the class.
  - Two helpers that differ only by which directory they walk. That's one
    function with a parameter.
  - "Helper" that takes the same first three arguments at every call site.
    Those are constructor params.
  - Test that monkeypatches a production module attr. Production code has a
    missing seam -- fix the seam.

### Package management (NON-NEGOTIABLE)
- **NEVER use `pip install`.** Always use `uv add` (or `uv add --dev` for dev
  deps).
- **`uv sync`** to install from lockfile. **`uv run`** to execute commands.
- **No `src/` layout.** Package lives at `git_agent_ratchet/` at the repo root.
  Build backend is hatchling (see `pyproject.toml`).

### Logging standard (NON-NEGOTIABLE)
- **Use Python's `logging` module.** Every module that does non-trivial work
  gets `logger = logging.getLogger(__name__)`. Never use `print()` for
  diagnostic output. Hook scripts write user-facing failure messages to
  `sys.stderr` via `print` -- that is the *one* allowed use, because
  pre-commit captures and displays stderr directly to the developer.
- **Log every ratchet decision the user might need to debug:** which
  baseline was loaded, what the current metric was, what the recorded metric
  was, whether the registry was rewritten. The user is debugging a failed
  commit; volume is fine.

### Safety and secrets
- **Never log `HUMAN_RATCHET_BYPASS_KEY` or any token.** Ratchet C reads it
  but must not echo it. Tests assert on this; do not break them.
- **`.env` files for local configuration.** `.gitignore` + `.env.example` =
  security + transparency. This repo does not currently use `.env`; if you
  add one, follow the pattern.

### Agent narration policy (NON-NEGOTIABLE)
GitHub Copilot CLI, Cursor, Claude Code, and Aider all occasionally leak
agent narration ("Now let me check the docs directory:", "Sure, I can help <!-- ratchet-allow: agent_chatter -->
with...") into stdout despite `-s/--silent`. That narration must never reach
a committed file -- it reads as a chat transcript and destroys trust in the
codebase.

This repo's defence is **Ratchet B itself**
([git_agent_ratchet/ratchets/agent_chatter.py](git_agent_ratchet/ratchets/agent_chatter.py)).
The regex signatures live in `CHATTER_SIGNATURES`. If a new narration
pattern slips through (a CLI version bump introduces new phrasing):

1. Add the pattern to `CHATTER_SIGNATURES`.
2. Add a regression test in `tests/test_agent_chatter_regressions.py` that
   matches the new phrasing.
3. Commit the regex change and the test in the same commit. **Do not** ship
   the test without the regex -- the regression suite goes red and the next
   agent is blocked.

If existing files in the repo are infected, fix them by hand in a separate
commit (`cleanup: scrub leaked narration from <file>`).

---

## Tech stack

| Layer | Choice |
|---|---|
| **Language** | Python 3.10+ |
| **Build backend** | hatchling |
| **Packaging** | uv (NEVER pip) |
| **Pre-commit framework** | pre-commit (the upstream Python tool) |
| **Testing** | pytest + pytest-cov |
| **Lint + format** | ruff (E, W, F, I, B, UP) |
| **Distribution** | published as a pre-commit-compatible repo via `.pre-commit-hooks.yaml` |

---

## Project structure

```
git-agent-ratchet/
|-- AGENTS.md                          # This file -- agent grounding
|-- README.md                          # Front door
|-- LICENSE
|-- pyproject.toml                     # hatchling build, ruff config, pytest config
|-- .pre-commit-hooks.yaml             # Hook manifest consumed by other repos
|-- .pre-commit-config.yaml            # This repo's own pre-commit config (dogfood)
|-- .gitignore
|-- docs/
|   |-- spec.md                        # Full design spec v1.0.0 (the contract)
|   `-- TODO.md                        # Master progress tracker + Known bugs
|-- git_agent_ratchet/                     # Flat package (no src/ layout)
|   |-- __init__.py
|   |-- __main__.py                    # `python -m git_agent_ratchet`
|   |-- _version.py
|   |-- py.typed
|   |-- cli.py                         # Unified `git-agent-ratchet <subcommand>` dispatcher
|   |-- baseline.py                    # JSON registry load / save / mutate
|   |-- hooks/                         # Pre-commit entry points (one per ratchet)
|   |   |-- no_duplicate_helpers.py    # Ratchet A entry
|   |   |-- deny_agent_chatter.py      # Ratchet B entry
|   |   `-- anti_bypass.py             # Ratchet C entry
|   `-- ratchets/                      # Pure scanners (no I/O of their own)
|       |-- duplicate_helpers.py       # AST scan
|       |-- agent_chatter.py           # Regex scan
|       `-- anti_bypass.py             # Env + path inspection
|-- config/
|   `-- ratchets/
|       `-- duplicates.json            # Ratchet A baseline registry
`-- tests/
    |-- test_baseline.py
    |-- test_duplicate_helpers.py
    |-- test_agent_chatter.py
    |-- test_anti_bypass.py
    |-- test_hooks_no_duplicate_helpers.py
    |-- test_hooks_deny_agent_chatter.py
    |-- test_hooks_anti_bypass.py
    `-- test_cli.py
```

---

## Key concepts

### Baseline registry
A versioned JSON file per ratchet, default `config/ratchets/duplicates.json`.
Shape and schema in section 2.2 of [docs/spec.md](docs/spec.md). The
invariant: for any ratchet `R`, the metric value `C_{t+1} <= C_t` across
commits. The registry is allowed to shrink (the hook rewrites it and stages
the diff into the current commit); it is structurally barred from growing
without a human bypass.

### Hook lifecycle inside another repo
A consumer adds this repo to their `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/monk-eee/git-agent-ratchet
    rev: v1.0.0
    hooks:
      - id: ratchet-no-duplicate-helpers
        args: [--baseline=config/ratchets/duplicates.json, --dir=src/]
      - id: ratchet-deny-agent-chatter
        files: \.(py|md|txt|go|js|ts|rs)$
      - id: ratchet-anti-bypass
        args: [--enforce-files=AGENTS.md,.pre-commit-config.yaml,config/ratchets/duplicates.json]
```

Pre-commit installs this package into an isolated venv, then dispatches the
matching console script per hook id. Filenames are passed positionally;
flags configure paths and policy.

### Anti-bypass policy
Ratchet C reads `HUMAN_RATCHET_BYPASS_KEY` from the environment. The key is
present iff a human operator has explicitly opted in for the current shell
session. Agents must not set it. If you (an agent) find yourself wanting to
set `HUMAN_RATCHET_BYPASS_KEY` to make a commit pass, you are the failure
mode the ratchet exists to catch -- stop and surface the blocker to the
operator instead.

---

## Agent workflow

When an agent is asked to extend or change this package:

1. **Read [docs/spec.md](docs/spec.md)** first. It is the contract; this
   file is the agent-facing index. If the change contradicts the spec, the
   spec must be updated in the same commit.
2. **Run the test suite before you start.** `uv run pytest -q`. If it is
   already red, fix that first or surface it -- do not stack a new change on
   a broken baseline.
3. **Pick the smallest module that owns the change.**
   - Changing a regex signature -> `git_agent_ratchet/ratchets/agent_chatter.py`
     plus a regression test.
   - Changing a hook's CLI surface -> `git_agent_ratchet/hooks/<name>.py` plus
     the matching `tests/test_hooks_<name>.py`.
   - Changing the registry shape -> `git_agent_ratchet/baseline.py` plus
     `tests/test_baseline.py`, and bump `SCHEMA_URL` if the on-disk shape
     changes.
4. **Run regression tests for any module you touch** and add a new test in
   `tests/test_<module>_regressions.py` for any bug fixed.
5. **Run all three ratchets against this repo before committing.** `make
   ratchet` runs them in sequence. This is the dogfood check -- if our own
   hooks fail on our own code, the change is wrong.

---

## Commands

```bash
# Setup
make setup                                  # uv sync + pre-commit install

# Dev
make test                                   # uv run pytest -q
make test-cov                               # uv run pytest --cov=git_agent_ratchet --cov-report=term-missing
make lint                                   # ruff check + ruff format --check
make format                                 # ruff check --fix + ruff format
make ratchet                                # run all three hooks against this repo

# Direct hook invocation (debugging)
uv run git-agent-ratchet no-duplicate-helpers --dir git_agent_ratchet --baseline config/ratchets/duplicates.json
uv run git-agent-ratchet deny-agent-chatter <file>...
uv run git-agent-ratchet anti-bypass --enforce-files AGENTS.md,.pre-commit-config.yaml,config/ratchets/duplicates.json <file>...

# Seed an empty baseline (first time only)
uv run git-agent-ratchet no-duplicate-helpers --dir git_agent_ratchet --baseline config/ratchets/duplicates.json
```

---

## Conventions

- **File naming:** snake_case for Python modules, kebab-case for hook ids.
- **No emojis** in generated content, comments, commit messages, or docs.
- **JSON for machine data, Markdown for docs** -- the baseline registry is
  JSON because it is rewritten programmatically; the spec and this file are
  Markdown because humans and agents read them.
- **Hooks are idempotent.** Running a ratchet twice on a clean tree produces
  the same exit code and the same registry. Tests assert this.
- **Every hook prints what it did to stderr.** The user is debugging a
  failed commit; "exited 1 with no output" is a bug, not a feature.
