# git-agent-ratchet

A Programmatic Git Ratchet System for Automated Agent Guarding

- **Author:** Monkee Magic & Git Ratchet Core
- **Target Ecosystem:** Python, pre-commit, LLM Agents
- **Date:** June 2026
- **Version:** v1.3.0

---

## 1. Executive Philosophy

Modern autonomous AI engineering tools (e.g., Cursor, Claude Code, Aider) optimize
actions dynamically against a multi-variable context matrix. This matrix consists of
internal system instructions, codebase telemetry, historical file state, and direct
user prompts. In this operational architecture, purely text-based instructions
provided within markdown manifests — such as `AGENTS.md` or `CLAUDE.md` — experience
silent rule erosion over long multi-turn context cycles. The agent does not willfully
ignore instructions; instead, it selects paths of least technical resistance that
systematically compromise loose programmatic constraints.

The solution is the implementation of a **Git Ratchet**: a deterministic code
gating system embedded within local workspace life cycles (such as pre-commit
hooks). A Git Ratchet turns abstract prose requirements into non-negotiable
structural compilation conditions. If an agent introduces code that violates a
rule, the local workspace gate triggers an explicit, non-zero system failure.
Because the agent inherently targets a successful green lifecycle state to
complete its loop, it is mechanically forced to find compliance. The rule didn't
change; the cost profile of breaking it did.

**Core Invariant:** Structural metrics governed by an git-agent-ratchet hook are
permitted to shrink (improving the codebase quality) or remain static, but are
structurally barred from ever increasing under agent operations without human
cryptographic bypasses.

---

## 2. Package Architecture & Configuration

The framework is built as a lightweight, modular Python package named
`git-agent-ratchet`. It interfaces directly with the standard pre-commit framework,
ensuring universal cross-language compatibility via isolated Python runtimes.

### 2.1 Pre-Commit Hook Declaration

Users integrate the system into their workspace by declaring the package
repository inside their project's root `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/monk-eee/git-agent-ratchet
   rev: v1.3.0
    hooks:
      - id: ratchet-no-duplicate-helpers
        args: [--baseline=config/ratchets/duplicates.json, --dir=src/]
      - id: ratchet-deny-agent-chatter
        files: \.(py|md|txt|go|js|ts|rs)$
      - id: ratchet-anti-bypass
        args: [--enforce-files=AGENTS.md,.pre-commit-config.yaml]
      - id: ratchet-max-file-lines
        args: [--baseline=config/ratchets/file_lines.json, --dir=src/, --max=350]
      - id: ratchet-no-cross-module-private-import
        args: [--baseline=config/ratchets/private_imports.json, --dir=src/]
      - id: ratchet-no-print-outside-allowlist
        args: [--baseline=config/ratchets/print_calls.json, --dir=src/, --allow-prefix=src/cli.py]
      - id: ratchet-no-temporary-comments
        args: [--baseline=config/ratchets/temporary_comments.json, --dir=src/]
         - id: ratchet-dont-use-powershell
            files: \.(py|md|txt|ya?ml|toml|json|sh|bash|zsh)$
```

### 2.2 The Unified Baseline Registry Format

Ratchets track structural state using deterministic, version-controlled JSON
baselines. The default baseline tracking mechanism relies on tracking the item
count `C_t` at commit state `t`. The ratchet guarantees that for any future
commit state `t+1`, the condition `C_{t+1} <= C_t` is strictly enforced.

```json
{
  "$schema": "https://git-agent-ratchet.org/schemas/v1.json",
  "ratchet_meta": {
    "repo_signature": "sha256:...hash...",
    "last_updated_by": "git-agent-ratchet-core"
  },
  "baselines": {
    "duplicate_helpers": {
      "metric_value": 3,
      "items": [
        {"name": "_safe_load_or_default", "occurrences": ["src/utils/io.py", "src/core/loader.py"]},
        {"name": "_retry_backoff", "occurrences": ["src/net/http.py", "src/db/client.py"]},
        {"name": "_run_command", "occurrences": ["scripts/deploy.py", "src/tasks/runner.py"]}
      ]
    }
  }
}
```

---

## 3. Core Hook Implementations

### 3.1 Ratchet A: Cross-Language Duplicate Helper Detection

**Target Failure Mode:** Agents frequently fork local helper utilities (e.g.,
internal string formatters, safe shell execution wrappers, atomic array appenders)
instead of traversing existing abstractions to perform reuse.

**Programmatic Execution Mechanics:**

1. The hook scans every source file inside specified directory trees,
   dispatched to a language-specific extractor by file suffix:

   | Language | Extensions | "Helper-shaped" definition | Parser |
   | --- | --- | --- | --- |
   | Python | `.py` | Top-level `def` / `async def` with a leading underscore but not a dunder. | `ast.parse` |
   | TypeScript / JavaScript | `.ts`, `.tsx`, `.js`, `.jsx`, `.mjs`, `.cjs` | Unexported top-level `function` declaration or `const NAME = (...) => ...` / `function` arrow at column zero. | Regex |
   | C# | `.cs` | Any line declaring a `private` (optionally `static` / `async` / generic) method. Constructors, fields, and properties excluded. | Regex |

2. Each extractor returns the names of declarations it considers
   "helper-shaped" for its language. Names are grouped across files
   ignoring anything under the configured exclude directories.
3. Any helper name present in two or more distinct physical source
   files is flagged. The metric tracked in the baseline is the total
   occurrence count across all flagged groups.
4. **The Gate Rule:** If the count exceeds the recorded value in the
   baseline file, the hook exits with exit code `1`, outputting the
   exact delta to stderr. If the count is lower than the baseline, the
   hook modifies the baseline file directly with the clean state,
   staging the shrunk registry for inclusion in the current commit.
5. The `--lang` flag (repeatable) restricts scanning to a subset of
   registered languages; default behaviour is to run every extractor.
   Adding a new language is a new module under
   `git_agent_ratchet/ratchets/extractors/` plus a registry entry --
   no other call site changes.

### 3.2 Ratchet B: Lexical Agent Chatter Stripping

**Target Failure Mode:** Multi-turn agent operations tend to leak conversational
preamble or postscript artifacts into codebase structures, modifying files with
content like: `# Sure, let me implement that interface change for you:`.

**Programmatic Execution Mechanics:** The hook scans all staged line diffs via a
deterministic token and regular expression engine targeting high-probability
conversational marker combinations.

| Regex Signature Trigger | Target Agent Fallback Substring |
| --- | --- |
| `(?i)(sure,\s)?i\scan\shelp\swith` | "Sure, I can help with modifying this code..." | <!-- ratchet-allow: agent_chatter -->
| `(?i)as\san\sai,\s(i\s)?` | "As an AI, I am tasked with maintaining structural parameters..." | <!-- ratchet-allow: agent_chatter -->
| `(?i)i\shave\ssuccessfully\s(modified|updated)` | "I have successfully updated the workspace dependencies." | <!-- ratchet-allow: agent_chatter -->
| `(?i)now\slet\sme\scheck\sthe\s(docs\|dir)` | "# Now let me check the docs directory to confirm layout..." | <!-- ratchet-allow: agent_chatter -->

### 3.3 Ratchet C: Cryptographic Human Anti-Bypass Guard

**Target Failure Mode:** When confronted with a rigid programmatic constraint, an
intelligent agent will parse files tracking the rule definition (like
`.pre-commit-config.yaml` or the baseline JSON arrays) and mutate those tracking
files to force its broken commit to pass.

**Programmatic Execution Mechanics:**

1. The hook determines the origin of the current workspace execution block. If a
   mutation is detected on the ratchet configuration files or baseline paths, it
   halts processing.
2. It scans for the existence of an environmental cryptographic parameter:
   `HUMAN_RATCHET_BYPASS_KEY` or an equivalent structural signature inside the
   local shell layer.
3. If the signature is absent, it executes an automated `git diff` check against
   origin branches. If modifications to the ratchet engine itself were authored
   by the automated agent process, the tool forces an immutable system abort.

### 3.4 Ratchet D: Per-File Line-Count Ratchet

**Target Failure Mode:** Agents grow modules instead of splitting them. The 350-
line soft rule in `AGENTS.md` is the first casualty of a long refactor session:
each turn adds "just one more helper", the file passes 400 lines, then 600, then
nobody can read it any more.

**Programmatic Execution Mechanics:**

1. The hook walks the directory tree supplied by `--dir`, skipping the path
   segments listed by `--exclude` (default: `tests`, `test`).
2. For every `.py` file it counts the lines (`len(text.splitlines())`) and
   records any file whose count exceeds `--max` (default: 350) as an
   `OversizedFile(path, line_count, overage)`.
3. The metric tracked in the baseline is the sum of all per-file overages.
4. **The Gate Rule:** If the current total overage exceeds the recorded value
   in the baseline file, the hook exits with exit code `1`, printing the
   per-file diagnostic to stderr. If the value is lower, the hook rewrites the
   baseline to the smaller number and stages the change. If equal, exit `0`
   silently. If no baseline exists yet, seed it and exit `0`.

### 3.5 Ratchet E: Cross-Module Private Import Detection

**Target Failure Mode:** Agents reach into another module's private namespace,
e.g. `from pkg.helpers import _normalise_path`. The leading underscore is the
Python convention for *module-private*; importing such a name across module
boundaries silently couples consumers to an implementation detail the author is
free to rename or delete, defeating the privacy contract that the leading
underscore was supposed to encode.

**Programmatic Execution Mechanics:**

1. The hook walks the directory tree supplied by `--dir`, skipping path
   segments listed by `--exclude` (default: `tests`, `test`).
2. For every `.py` file it parses the AST and walks `ast.ImportFrom` and
   `ast.Import` nodes. Any imported name (alias) whose identifier starts
   with `_` and is not a dunder (`__init__`, `__main__`) is recorded as a
   `PrivateImport(file, line, name, source_module)`.
3. **Relative imports are ignored.** `from . import _helper` and `from .util
   import _x` stay inside the package and are considered the author's
   prerogative. Only absolute imports trigger the gate.
4. The metric tracked in the baseline is the count of violations.
5. **The Gate Rule:** Same shape as Ratchet A / D -- grow -> exit 1 with the
   per-violation report; shrink -> rewrite baseline and stage; equal -> exit
   0 silently; missing baseline -> seed and exit 0.

### 3.6 Ratchet F: Print-Call Allowlist

**Target Failure Mode:** The `AGENTS.md` "use `logging.getLogger(__name__)`,
not `print()`" rule is the first soft rule to slip during a debug session. The
agent adds a `print(...)` to trace one variable, the session ends, the print
lands in the commit, and the diagnostic noise outlives the bug.

**Programmatic Execution Mechanics:**

1. The hook walks the directory tree supplied by `--dir`, skipping path
   segments listed by `--exclude` (default: `tests`, `test`).
2. For every `.py` file it parses the AST and walks `ast.Call` nodes. Any
   `Call(func=Name("print"))` -- the literal `print(...)` expression -- is
   recorded as a `PrintCall(file, line, col)`. The word "print" appearing
   in strings, comments, or docstrings is ignored.
3. **Path-prefix allowlist.** Modules that must legitimately write to stderr
   (hook entry-point shims, CLI dispatchers) are allowlisted by path prefix
   via repeatable `--allow-prefix`. A file whose repo-relative posix path
   starts with any allowed prefix is skipped wholesale.
4. The metric tracked in the baseline is the count of non-allowlisted
   `print()` calls.
5. **The Gate Rule:** Same shape as Ratchet A / D / E. Grow -> exit 1 with
   the per-call diagnostic; shrink -> rewrite baseline; equal -> silent
   pass; missing -> seed and pass.

### 3.7 Ratchet G: Temporary-Comment Marker Detection

**Target Failure Mode:** The expedient-path comment that documents its own
calcification: `# TODO: remove once X migrates`, `// for now, fall back to
legacy`, `/* transitional bridge -- delete after release */`, `# HACK: fix
later`. The TODO never gets resolved. The bridge becomes load-bearing. The
next agent reads the comment, infers the shim is supported policy, and adds
another one. The mechanical gate is *not* "ban TODO comments" -- it is "the
count of these specific narrowly-defined expedient markers may not grow."

**Programmatic Execution Mechanics:**

1. The hook walks the directory tree supplied by `--dir`, skipping path
   segments listed by `--exclude` (default includes `tests`, `node_modules`,
   `dist`, etc.).
2. For every file whose extension is in `DEFAULT_EXTENSIONS` (`.py`, `.ts`,
   `.tsx`, `.js`, `.jsx`, `.cs`, `.go`, `.rs`, `.java`, `.kt`), it scans
   line-by-line against `TEMPORARY_SIGNATURES`, a tuple of (label, regex)
   pairs:

   | Label | Regex (case-insensitive) |
   | --- | --- |
   | `for-now` | `(?<![A-Za-z0-9_])(just\s+)?for\s+now(?![A-Za-z0-9_])` |
   | `back-compat` | `(?<![A-Za-z0-9_])back[-\s]?compat(ibility)?(?![A-Za-z0-9_])` |
   | `transitional-bridge` | `(?<![A-Za-z0-9_])(transitional\s+bridge\|temporary\s+bridge)(?![A-Za-z0-9_])` |
   | `todo-remove-once` | `todo:?\s*remove\s+(once\|when\|after)\b` |
   | `hack-fix-later` | `(?<![A-Za-z0-9_])(hack\|hacky)[:\s].*?(fix\s+later\|temporary)(?![A-Za-z0-9_])` |

3. **Per-line allow marker.** A line containing the literal
   `ratchet-allow: temporary_comments` (typically embedded in a comment)
   opts that single line out of the gate.
4. The metric tracked in the baseline is the count of non-allowlisted
   matches.
5. **The Gate Rule:** Same shape as Ratchet A / D / E / F.

### 3.8 Ratchet H: PowerShell Command Usage Detection

**Target Failure Mode:** On Windows-hosted sessions, agents frequently emit
PowerShell commands into repo artifacts (`powershell -Command ...`,
`pwsh -NoProfile ...`, `Set-ExecutionPolicy ...`, `$env:FOO=...`) even when
the repository standard is cross-platform command guidance.

**Programmatic Execution Mechanics:**

1. The hook scans staged text files passed by pre-commit.
2. Each line is matched against `POWERSHELL_SIGNATURES` for command-like
   patterns: executable invocations (`powershell` / `pwsh` with switches),
   `.ps1` command references, common cmdlets, and `$env:` prefixes.
3. Lines containing the per-line allow marker
   `ratchet-allow: powershell_usage` are skipped.
4. **The Gate Rule:** Any match is a hard fail (exit `1`) with file + line
   diagnostics. This ratchet is invariant-style (no baseline registry).

---

## 4. When a Rule Earns a Ratchet (Anti-Rot Contract)

The standing criticism of any ratchet system is that it degenerates into a
**sinecure**: a gate that runs on every commit, reports green, *feels* like
governance, but never changes behaviour and never pays down. It draws a
salary for no work. A ratchet that cannot answer this charge must not be
shipped. This section is the contract that answers it. A candidate rule that
fails the test below does not become a hook -- it stays prose in `AGENTS.md`
or moves to the linter.

### 4.1 Two Kinds of Gate

Gates are not homogeneous, and judging them on a single axis is a category
error an external reviewer will exploit.

- **Debt ratchets** are judged by *motion*. They carry a baseline count that
  is expected to trend downward through ordinary work. Ratchets A, D, E, F,
  G are debt ratchets. A debt ratchet whose count never moves across many
  commits of active development is the sinecure failure mode.
- **Invariant gates** are judged by *deterrence*. They carry no debt count
   and fire rarely by design. Ratchet C (`anti-bypass`) and Ratchet H
   (`dont-use-powershell`) are invariant gates: one protects the guardrails,
   the other protects cross-platform command hygiene in committed text.
   A smoke detector is not measured by how often it beeps.

Every gate in this package MUST declare which kind it is. A debt ratchet is
defended on "watch the count fall"; an invariant gate is defended on "here is
the catastrophe it deters."

### 4.2 The Four-Bar Test (Debt Ratchets)

A rule earns a *debt ratchet* only if it clears all four bars. Ratchet D
(`max-file-lines`) is the reference implementation; it scores 4/4.

1. **Fires often.** The violation occurs during normal work, so the gate
   does work on a routine cadence rather than guarding an event that almost
   never happens. A gate that rarely fires is a tripwire in an empty room.
2. **Silent in review.** A human reviewer reliably misses it. The change
   reads as correct in a diff (a file drifting from 340 to 360 lines across
   a feature). This invisibility is precisely the erosion class a mechanical
   counter exists to catch. If review catches it reliably, no hook is needed.
3. **Pays down through ordinary work.** Remediation happens as a side-effect
   of someone already working in the affected file; the baseline auto-shrinks
   and stages the diff. No dedicated cleanup sprint is required.
4. **Cheap early, expensive late.** Detection at commit costs seconds;
   detection months later costs a painful untangle. This asymmetry justifies
   the per-commit cost of the gate.

A candidate that misses any bar is not a debt ratchet. Example: "no function
over 40 lines" fails bars 1 and 2 for most teams (it fires rarely and review
catches it), so it remains a linter rule, not a ratchet.

### 4.3 Structural Anti-Rot Properties

Three properties keep debt ratchets honest rather than ceremonial. All three
are invariants of the implementation, not conventions:

- **Shrink-only baselines.** Per the Core Invariant, the metric may fall or
  hold but never grow without a human bypass. A frozen count therefore means
  the code has genuinely not improved -- never that someone forgot to tighten
  the gate.
- **Loud by default.** Every hook prints its decision and the evidence for it
  (baseline loaded, current metric, recorded metric, whether the registry was
  rewritten). There is no quiet mode. A flatlining ratchet is visible in its
  own output and does not depend on anyone remembering to audit it.
- **Retirement is a valid terminal state.** A debt ratchet that reaches zero
  and holds there has succeeded and SHOULD be retired -- folded into the
  linter or deleted. Birth criteria without death criteria is how a hook pack
  bloats toward hundreds of rules; permitting retirement is what bounds the
  rule count.

### 4.4 The One-Line Defence

A hold-only ratchet is a sinecure, and this package does not ship them. A
debt ratchet that clears the four-bar test fires often, catches what review
misses, and pays itself down through normal work -- and the shrink-only
baseline makes a flatline impossible to hide.

---

## 5. The Markdown Connection Layout

To close the control loop, the agent must see the gate before it collides with
it. Every `AGENTS.md` file entry must map prose explicitly to its corresponding
programmatic ratchet gate.

---

## 6. Immediate Implementation Bootstrap Roadmap

To execute rapid deployment of this package structure across private or
open-source repositories, developer engineering teams must complete four
immediate iterative steps:

1. **Structure Core Scanners:** Implement a standalone Python CLI tool wrapping
   standard `ast` modules to count module-level private functions across
   disparate paths.
2. **Wire Pre-Commit Setup:** Draft a compliant `hooks.yaml` configuration
   mapping system arguments cleanly to the Python runtime files.
3. **Generate Initial Registry:** Run the scanner initially over the core repo
   tree to generate the structural baseline without altering historic state
   immediately.
4. **Declare Clear Manifest Gates:** Copy-paste the programmatic enforcement
   layout block directly into active `AGENTS.md` rule lists to immediately
   realign agent trajectory planning.
