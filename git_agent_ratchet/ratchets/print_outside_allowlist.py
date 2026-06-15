"""Ratchet F: detect ``print()`` calls in modules outside an allowlist.

Maps the AGENTS.md ``logging`` rule into a mechanical gate: production
modules must use ``logging.getLogger(__name__)`` rather than ``print()``.
CLI / hook entry-point shims that intentionally write to stderr (so
pre-commit can surface failure output) are allowlisted by path prefix
via ``--allow-prefix`` on the hook.

The scan is AST-based, so the word "print" in strings, comments, and
docstrings is ignored. Only actual ``print(...)`` call expressions count.
"""

from __future__ import annotations

import ast
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from git_agent_ratchet.paths import iter_python_files, relative_posix, strip_dot_slash

RATCHET_NAME = "print_calls"
DEFAULT_EXCLUDE_DIRS = ("tests", "test")


@dataclass(frozen=True)
class PrintCall:
    """A single ``print(...)`` call in production source."""

    file: str
    line: int
    col: int

    def to_dict(self) -> dict[str, object]:
        return {"file": self.file, "line": self.line, "col": self.col}


def _print_calls_in_tree(tree: ast.AST, file_label: str) -> list[PrintCall]:
    calls: list[PrintCall] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name) and func.id == "print":
            calls.append(PrintCall(file=file_label, line=node.lineno, col=node.col_offset))
    return calls


def scan_file(source_path: Path, file_label: str | None = None) -> list[PrintCall]:
    """Return every ``print(...)`` call in ``source_path``."""
    label = file_label if file_label is not None else str(source_path)
    try:
        source = source_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    try:
        tree = ast.parse(source, filename=str(source_path))
    except SyntaxError:
        return []
    return _print_calls_in_tree(tree, label)


def is_allowed(file_label: str, allow_prefixes: Iterable[str]) -> bool:
    """Return True if ``file_label`` is, or lives under, any allowed prefix.

    A prefix matches either the exact file (``pkg/cli.py`` allows ``pkg/cli.py``)
    or a directory it names (``pkg/hooks`` allows ``pkg/hooks/x.py``). It does
    *not* match by bare string prefix, so ``pkg/cli`` never allows
    ``pkg/client.py``.
    """
    label = strip_dot_slash(file_label.replace("\\", "/"))
    for prefix in allow_prefixes:
        norm = strip_dot_slash(prefix.replace("\\", "/")).rstrip("/")
        if not norm:
            continue
        if label == norm or label.startswith(norm + "/"):
            return True
    return False


def scan_directory(
    root: Path,
    exclude_dirs: Iterable[str] = DEFAULT_EXCLUDE_DIRS,
    allow_prefixes: Iterable[str] = (),
) -> list[PrintCall]:
    """Scan ``root`` and return every print() call not under an allowed prefix."""
    if not root.exists():
        return []
    anchor = root.parent if root.parent.exists() else root
    prefixes = tuple(allow_prefixes)
    calls: list[PrintCall] = []
    for py in iter_python_files(root, exclude_dirs):
        label = relative_posix(py, anchor)
        if is_allowed(label, prefixes):
            continue
        calls.extend(scan_file(py, file_label=label))
    calls.sort(key=lambda c: (c.file, c.line, c.col))
    return calls


def metric_value(calls: list[PrintCall]) -> int:
    """Return the total count of non-allowlisted print() calls."""
    return len(calls)
