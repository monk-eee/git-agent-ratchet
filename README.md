# git-agent-ratchet

[![CI](https://github.com/monk-eee/git-agent-ratchet/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/monk-eee/git-agent-ratchet/actions/workflows/ci.yml)
[![CodeQL](https://github.com/monk-eee/git-agent-ratchet/actions/workflows/codeql.yml/badge.svg?branch=main)](https://github.com/monk-eee/git-agent-ratchet/actions/workflows/codeql.yml)
[![codecov](https://codecov.io/gh/monk-eee/git-agent-ratchet/branch/main/graph/badge.svg)](https://codecov.io/gh/monk-eee/git-agent-ratchet)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/downloads/)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://pre-commit.com/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Built with uv](https://img.shields.io/badge/built%20with-uv-de5feb)](https://github.com/astral-sh/uv)
[![Version](https://img.shields.io/badge/version-1.0.0-informational)](https://github.com/monk-eee/git-agent-ratchet/releases)

> The rule didn't change. The cost of breaking it did.

A pre-commit hook pack that turns the polite suggestions in your `AGENTS.md`
into deterministic gates at commit time. Four small, ugly, single-purpose
scripts. They do not get clever. They just fail loudly when an agent does
the thing your file already told it not to do.

- **Ratchet A** -- `no-duplicate-helpers`. AST scan. Private helper names
  are not allowed to spread across more files than the recorded baseline.
- **Ratchet B** -- `deny-agent-chatter`. Regex scan. Conversational
  preamble (`"Sure, I can help with..."`, `"As an AI, ..."`, `"Now let me <!-- ratchet-allow: agent_chatter -->
  check the docs..."`) cannot ride into a commit.
- **Ratchet C** -- `anti-bypass`. If a mutation lands on a protected
  ratchet config file without `HUMAN_RATCHET_BYPASS_KEY` in the environment,
  the commit dies.
- **Ratchet D** -- `max-file-lines`. Per-file line counts may not grow
  past their recorded baseline. Split, don't sprawl.

The package itself runs all four of these against itself on every commit.
If our own hooks fail on our own code, the change is wrong. That's the test.

---

## Why this exists

Given enough runs, every agent eventually breaks a rule in your
`AGENTS.md`. Not maliciously. Not noticeably at first. It reads the file at
the start of the session -- you can watch it in the transcript -- and for
the first few turns the rules hold. Then it gets stuck on something, finds
a path that works, and the file becomes background. Three commits later
it's writing the helper you explicitly told it not to write, in the
directory you explicitly told it to check first.

The agents.md spec is a filename convention. It standardised the location
so every tool (Codex, Cursor, Aider, Copilot, Zed, Claude Code) looks in
the same place. That was worth shipping. But the spec is silent on
enforcement, because enforcement is not what the spec is for. It is a
README for agents, and READMEs ask politely.

The vendors know this. Anthropic's own docs say it out loud:

> *Settings rules are enforced by the client regardless of what Claude
> decides to do. `CLAUDE.md` instructions shape Claude's behavior but are
> not a hard enforcement layer. If the instruction is something that must
> run at a specific point, such as before every commit or after each file
> edit, write it as a hook instead.*

Cursor's Team Rules toggle is careful to add that "AI guidance should not
be your only security control." GitHub Copilot's recommended boilerplate
for `copilot-instructions.md` ends with a sentence telling the agent to
trust the file -- an instruction that would not need to exist if trust
were the default.

All three vendors are saying the same thing in different words: the file
is context, weighted against everything else in the prompt. Length erodes
adherence, conflicts resolve arbitrarily, and if you need a guarantee you
leave the markdown layer and write a hook.

`git-agent-ratchet` is the hook layer.

---

## What an enforced rule looks like

The pattern is three things, every time:

1. **The rule, in prose, in your `AGENTS.md`** -- so the agent knows what's
   expected and why.
2. **A script that fails the commit** when the rule is broken.
3. **A line in the file that names the gate** -- so the agent knows the
   ratchet exists before it walks into it.

Concrete, copy-pasteable, this is what one entry in your `AGENTS.md` looks
like after you wire `git-agent-ratchet`:

```markdown
### Duplicate helpers

Don't fork helpers. Check `libs/` first; if a near-miss exists, extend it.
Red-flag prefixes that historically get forked: `_run_*`, `_safe_*`,
`_load_*_or_default`, `_no_prompt_*`, `_retry_*`, `_atomic_*`.

Enforcement:
- `ratchet-no-duplicate-helpers` (this repo) -- AST scanner. Fails on any
  module-level `def _name(...)` appearing in 2+ files outside `tests/`
  when the count exceeds the baseline.
- Baseline lives at `config/ratchets/duplicates.json`. Allowed to shrink,
  never grow.

Forbidden bypasses:
- Do not add an allowlist to the scanner.
- Do not edit the baseline JSON by hand -- Ratchet C will block it.
- Do not `--no-verify`.
```

The prose says what and why. The enforcement block names the code that
runs. The bypasses block names the cheats the agent will reach for if you
don't forbid them by name.

---

## Install

Add the repo to your project's `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/monk-eee/git-agent-ratchet
    rev: v1.0.0
    hooks:
      - id: ratchet-no-duplicate-helpers
        args:
          - --baseline=config/ratchets/duplicates.json
          - --dir=src/
      - id: ratchet-deny-agent-chatter
        files: \.(py|md|txt|go|js|ts|rs)$
      - id: ratchet-anti-bypass
        args:
          - --enforce-files=AGENTS.md,.pre-commit-config.yaml,config/ratchets/duplicates.json,config/ratchets/file_lines.json
      - id: ratchet-max-file-lines
        args:
          - --baseline=config/ratchets/file_lines.json
          - --dir=src/
          - --max=350
```

Then:

```bash
pre-commit install
pre-commit run --all-files
```

The first run of `ratchet-no-duplicate-helpers` against a real codebase
will scream. That is the point. It writes the current state as your
baseline and from that commit forward the count can only shrink. Each
cleanup commit extracts one duplicate into a shared module, swaps the
callers, and the hook rewrites the baseline JSON with the smaller count
and stages the diff into your commit.

---

## The three ratchets, in detail

### Ratchet A -- `ratchet-no-duplicate-helpers`

**Target failure mode.** Agents fork local helper utilities (internal
string formatters, safe shell execution wrappers, atomic array appenders)
instead of traversing existing abstractions to reuse them. By the fifth
helper, the soft "check `libs/` first" rule has slipped.

**What it does.** Walks the directory you point at with `--dir`, parses
each `.py` file with `ast`, collects top-level `def` / `async def` names,
keeps only the private/semi-private ones (`_foo`, not `__init__`), and
groups by name across files. Any name that appears in two or more files
outside `tests/` is a "duplicate". The total occurrence count is the
metric; the baseline JSON records it.

**Gate rule.**
- Current count > baseline -> exit 1 with a per-name report on stderr.
- Current count < baseline -> rewrite the baseline JSON with the smaller
  count, save it, exit 0. Pre-commit re-stages the file into the current
  commit automatically.
- Current count = baseline -> exit 0.
- No baseline yet -> seed the file, exit 0.

**Args.**

| Flag | Default | Purpose |
| --- | --- | --- |
| `--baseline` | `config/ratchets/duplicates.json` | Path to the JSON registry. |
| `--dir` | `src` | Directory to scan. |
| `--exclude` | `tests`, `test` | Repeatable. Path-segment names to skip. |

### Ratchet B -- `ratchet-deny-agent-chatter`

**Target failure mode.** Multi-turn agent operations leak conversational
preamble into source files: `# Sure, let me implement that interface
change for you:`, `// As an AI, I am tasked with...`, `Now let me check <!-- ratchet-allow: agent_chatter -->
the docs directory:`. One leak in a generated artefact and the file reads
as a chat transcript. Trust collapses.

**What it does.** Scans every file pre-commit hands it for the regex
signatures in [git_agent_ratchet/ratchets/agent_chatter.py](git_agent_ratchet/ratchets/agent_chatter.py):

| Signature | Catches |
| --- | --- |
| `(?i)(sure,\s)?i\scan\shelp\swith` | "Sure, I can help with modifying this code..." | <!-- ratchet-allow: agent_chatter -->
| `(?i)as\san\sai,\s(i\s)?` | "As an AI, I am tasked with..." | <!-- ratchet-allow: agent_chatter -->
| `(?i)i\shave\ssuccessfully\s(modified\|updated)` | "I have successfully updated the workspace dependencies." | <!-- ratchet-allow: agent_chatter -->
| `(?i)now\slet\sme\scheck\sthe\s(docs\|dir)` | "Now let me check the docs directory to confirm layout..." | <!-- ratchet-allow: agent_chatter -->

**Gate rule.** Any match anywhere -> exit 1 with the file, line number,
which signature fired, and the offending text.

**Extending it.** When a CLI version bump introduces a new narration
pattern, add the regex to `CHATTER_SIGNATURES` and a regression test in
`tests/test_agent_chatter_regressions.py` in the *same commit*. Ship the
test without the regex and the next agent is blocked by your own change.

### Ratchet C -- `ratchet-anti-bypass`

**Target failure mode.** When confronted with a rigid programmatic
constraint, an intelligent agent parses the files that define the rule
(like the baseline JSON, like `.pre-commit-config.yaml`, like the
`AGENTS.md` paragraph that names the ratchet) and mutates them to force
its broken commit to pass. The rule itself becomes the attack surface.

**What it does.**

1. Normalises the list of staged filenames pre-commit passed in.
2. Compares against `--enforce-files` (comma-separated, repo-relative).
3. If nothing protected was touched, exit 0.
4. If `HUMAN_RATCHET_BYPASS_KEY` is set to a non-empty value, exit 0.
   The human asserted intent for this shell session.
5. Otherwise, scan the environment for known agent signatures
   (`CURSOR_AGENT`, `CLAUDECODE`, `AIDER`, `COPILOT_AGENT`, ...) and
   exit 1 with a clear "human operator must export the bypass key"
   message. The agent signal, when present, is named in the failure
   output so you know which tool tripped it.

**Args.**

| Flag | Required | Purpose |
| --- | --- | --- |
| `--enforce-files` | yes | Comma-separated repo-relative paths to protect. |

**Important.** Ratchet C never logs the bypass key value, only its
presence. The CI suite asserts this.

### Ratchet D -- `ratchet-max-file-lines`

**Target failure mode.** Agents grow a single module instead of splitting
it. The 350-line soft rule in your `AGENTS.md` is the first casualty of a
five-turn refactor session: each turn adds "just one more helper", the
file passes 400 lines, then 600, then nobody can read it any more.

**What it does.** Walks the directory you point at with `--dir`, counts
the lines of every `.py` file, and records any file whose count exceeds
`--max` (default 350) in the baseline. The metric is the total overage
across all over-sized files. The baseline shrinks when you split a file
or contract one; it is structurally barred from growing.

**Gate rule.**
- Current overage > baseline -> exit 1 with the per-file diagnostic on
  stderr.
- Current overage < baseline -> rewrite the baseline JSON, save it,
  exit 0. Pre-commit re-stages the file automatically.
- Current overage = baseline -> exit 0.
- No baseline yet -> seed the file, exit 0.

**Args.**

| Flag | Default | Purpose |
| --- | --- | --- |
| `--baseline` | `config/ratchets/file_lines.json` | Path to the JSON registry. |
| `--dir` | `src` | Directory to scan. |
| `--max` | `350` | Per-file line-count limit. |
| `--exclude` | `tests`, `test` | Repeatable. Path-segment names to skip. |

---

## The baseline registry

One JSON file per project, default `config/ratchets/duplicates.json`.
Shape (full schema in [docs/spec.md](docs/spec.md)):

```json
{
  "$schema": "https://git-agent-ratchet.org/schemas/v1.json",
  "ratchet_meta": {
    "repo_signature": "sha256:...",
    "last_updated_by": "git-agent-ratchet-core"
  },
  "baselines": {
    "duplicate_helpers": {
      "metric_value": 3,
      "items": [
        {"name": "_safe_load_or_default", "occurrences": ["src/utils/io.py", "src/core/loader.py"]},
        {"name": "_retry_backoff",        "occurrences": ["src/net/http.py", "src/db/client.py"]},
        {"name": "_run_command",          "occurrences": ["scripts/deploy.py", "src/tasks/runner.py"]}
      ]
    }
  }
}
```

The invariant: for any ratchet `R` and any two consecutive commits,
`C_{t+1} <= C_t`. The registry is allowed to shrink (the hook does it for
you and stages the diff). It is structurally barred from growing without
a human bypass.

Do not edit this file by hand to make a commit pass. Ratchet C is watching
it.

---

## Direct CLI

Useful for debugging, CI scripting, or seeding a new baseline. Every hook
also has a long form under the unified `git-agent-ratchet` dispatcher:

```bash
# Ratchet A
git-agent-ratchet no-duplicate-helpers \
    --dir src \
    --baseline config/ratchets/duplicates.json

# Ratchet B (scan specific files)
git-agent-ratchet deny-agent-chatter path/to/file.py path/to/other.md

# Ratchet C (treat these paths as staged)
git-agent-ratchet anti-bypass \
    --enforce-files AGENTS.md,.pre-commit-config.yaml \
    AGENTS.md

# Ratchet D
git-agent-ratchet max-file-lines \
    --dir src \
    --max 350 \
    --baseline config/ratchets/file_lines.json
```

Each subcommand prints the decision it made and why. There is no `--quiet`
flag. The point of a ratchet is to be loud.

---

## How `git-agent-ratchet` and `AGENTS.md` work together

This package does not replace your `AGENTS.md`. It makes the rules in it
real.

The full pattern, sometimes called the **HUMANS.md** approach
(after the article that prompted this repo):

1. Audit every rule in your `AGENTS.md`. For each, ask:
   *What actually happens when the agent breaks this?*
2. If the answer is "nothing", the rule is soft. Mark it soft in the file,
   in prose. The next agent and the next human both deserve to know it is
   currently on the honour system.
3. Rank the soft rules by historical cost. Which one has already bitten
   you most? Build that ratchet first. A baseline regression check is the
   cheapest thing you can write and the easiest thing for the next agent
   to fail.
4. Document the enforcement next to the rule. Same paragraph. Name the
   hook id, name the baseline file, name the script. The agent reads
   top-down; the gate should be visible before the agent gets to the part
   where it would otherwise walk through it.
5. Forbid the bypasses by name. Allowlists, baseline-grows, `--no-verify`,
   `git add -A` instead of explicit paths, `git stash` instead of WIP
   commits. The agent will find these on its own; you might as well call
   them out before it does.
6. Stop writing rules with no plan to enforce them. If a rule is important
   enough to be in the file, it is important enough to either ratchet now
   or queue as the next ratchet.

This repo's own [AGENTS.md](AGENTS.md) follows this pattern. The
"Mechanical enforcement" table at the top maps every `NON-NEGOTIABLE`
rule to the hook id that enforces it. Rules that have no gate yet are
listed under "Known soft rules" in [DEVELOPERS.md](DEVELOPERS.md).

---

## Development

Flat layout. Hatchling. uv. No `src/`.

```bash
# Setup
make setup                  # uv sync + pre-commit install

# Run the suite
make test                   # uv run pytest -q
make test-cov               # with coverage

# Lint / format
make lint                   # ruff check + ruff format --check
make format                 # ruff check --fix + ruff format

# Dogfood: run all three ratchets against this repo
make ratchet
```

If `make ratchet` fails on a green tree, the change you just made is
wrong. That is the entire CI loop.

The full architectural contract lives in [docs/spec.md](docs/spec.md).
The agent-facing index is [AGENTS.md](AGENTS.md). The bug log and roadmap
are in [docs/TODO.md](docs/TODO.md).

---

## FAQ

**Why not just use README.md for both audiences?**
Different cold start. The README is human onboarding: story, badges,
install quirks. AGENTS.md is for the machine about to write code in your
repo in the next forty seconds and has no time for any of that. If one
file works for you, use one file. This repo keeps them separate because
the audiences answer different questions.

**Won't this slow my commits down?**
Ratchet A's AST scan is `O(files)` over your source tree and runs in
sub-second time on packages up to a few thousand modules. Ratchet B is a
regex pass over the staged set, capped at whatever pre-commit hands it.
Ratchet C is a string compare. Ratchet D is a line-count pass. None of
them call out over the network.

**Does it work with Husky / lefthook / native git hooks instead of pre-commit?**
The console scripts (`ratchet-no-duplicate-helpers`,
`ratchet-deny-agent-chatter`, `ratchet-anti-bypass`,
`ratchet-max-file-lines`) and the unified `git-agent-ratchet` CLI are
pure Python and have no `pre-commit` dependency at runtime. Wire them
into any hook runner that can execute a Python
console script. The bundled `.pre-commit-hooks.yaml` is provided because
that's the most common deployment, not because it's the only one.

**What if I really do need an exception?**
You are a human. Export `HUMAN_RATCHET_BYPASS_KEY=<anything-non-empty>`
in your shell, run the commit, unexport. Agents must not do this. If you
are an agent and you find yourself wanting to set this variable, you are
the failure mode the ratchet exists to catch -- stop and surface the
blocker to your operator instead.

**Why JSON for the baseline and not YAML?**
The baseline is rewritten programmatically by the hook itself. JSON has
one canonical serialisation; YAML has six and the agent will pick a
different one each commit. We are trying to remove drift, not add it.

**A new chatter pattern slipped through. What do I do?**
Add the regex to `CHATTER_SIGNATURES` in
[git_agent_ratchet/ratchets/agent_chatter.py](git_agent_ratchet/ratchets/agent_chatter.py),
add a regression test in `tests/test_agent_chatter_regressions.py` that
matches the new phrasing, and commit both in the same commit. Open an
issue if the pattern looks generalisable -- we want the signature table
to converge across the community, not fork per repo.

---

## Credits

The pattern is older than the package. The framing -- "the file is
context, the hook is the gate" -- is the consensus position from
practitioners who got tired of agents quietly breaking the same rule on
turn six of every session. The specific failure modes the three ratchets
catch are scars from real codebases. They have names; the bypasses do
too; both are written down here so the next agent has to walk past them
on the way in.

Background reading and prior art:

- The agents.md spec -- <https://agents.md>
- *HUMANS.md: my practical guide to making the agent do what you want,
  now with 100% more added sticks* -- Lyndon Swan, 2026
- *README, Don't AGENTS.md Me* -- Josh Beckman
- *When everything is important, nothing is* -- OpenAI Harness team
- Anthropic's Claude Code memory docs (the "not a hard enforcement layer"
  passage)

---

## License

MIT. See [LICENSE](LICENSE).
