# git-agent-ratchet

A Programmatic Git Ratchet System for Automated Agent Guarding

- **Author:** Monkee Magic & Git Ratchet Core
- **Target Ecosystem:** Python, pre-commit, LLM Agents
- **Date:** June 2026
- **Version:** v1.1.0

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
    rev: v1.1.0
    hooks:
      - id: ratchet-no-duplicate-helpers
        args: [--baseline=config/ratchets/duplicates.json, --dir=src/]
      - id: ratchet-deny-agent-chatter
        files: \.(py|md|txt|go|js|ts|rs)$
      - id: ratchet-anti-bypass
        args: [--enforce-files=AGENTS.md,.pre-commit-config.yaml]
      - id: ratchet-max-file-lines
        args: [--baseline=config/ratchets/file_lines.json, --dir=src/, --max=350]
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

---

## 4. The Markdown Connection Layout

To close the control loop, the agent must see the gate before it collides with
it. Every `AGENTS.md` file entry must map prose explicitly to its corresponding
programmatic ratchet gate.

---

## 5. Immediate Implementation Bootstrap Roadmap

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
