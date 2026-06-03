"""Ratchet A: AST-driven detection of duplicate private helper functions."""

from __future__ import annotations

import ast
from collections import defaultdict
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path

RATCHET_NAME = "duplicate_helpers"
DEFAULT_EXCLUDE_DIRS = ("tests", "test")


@dataclass(frozen=True)
class DuplicateHelper:
    """A private helper function name found in two or more files."""

    name: str
    occurrences: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {"name": self.name, "occurrences": list(self.occurrences)}


def is_private_helper(name: str) -> bool:
    """Return True for private/semi-private identifiers (_foo) but not dunders (__foo__)."""
    if not name.startswith("_"):
        return False
    if name.startswith("__") and name.endswith("__"):
        return False
    return True


def iter_python_files(
    root: Path, exclude_dirs: Iterable[str] = DEFAULT_EXCLUDE_DIRS
) -> Iterator[Path]:
    """Yield .py files under root, skipping any path containing an excluded dir name."""
    excluded = {d.lower() for d in exclude_dirs}
    for path in sorted(root.rglob("*.py")):
        parts = {p.lower() for p in path.parts}
        if parts & excluded:
            continue
        yield path


def collect_top_level_functions(source_path: Path) -> list[str]:
    """Return the names of all top-level function definitions in source_path."""
    try:
        source = source_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    try:
        tree = ast.parse(source, filename=str(source_path))
    except SyntaxError:
        return []
    return [
        node.name for node in tree.body if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    ]


def scan_directory(
    root: Path,
    exclude_dirs: Iterable[str] = DEFAULT_EXCLUDE_DIRS,
) -> list[DuplicateHelper]:
    """Scan root and return all private helper names that appear in 2+ files."""
    if not root.exists():
        return []
    grouped: dict[str, set[str]] = defaultdict(set)
    for py_file in iter_python_files(root, exclude_dirs):
        rel = _relative_posix(py_file, root.parent if root.parent.exists() else root)
        for fn_name in collect_top_level_functions(py_file):
            if is_private_helper(fn_name):
                grouped[fn_name].add(rel)
    duplicates = [
        DuplicateHelper(name=name, occurrences=tuple(sorted(paths)))
        for name, paths in grouped.items()
        if len(paths) >= 2
    ]
    duplicates.sort(key=lambda d: d.name)
    return duplicates


def _relative_posix(path: Path, anchor: Path) -> str:
    try:
        rel = path.resolve().relative_to(anchor.resolve())
    except ValueError:
        rel = path
    return rel.as_posix()


def metric_value(duplicates: list[DuplicateHelper]) -> int:
    """Compute the total occurrence count across all duplicate helper groups."""
    return sum(len(d.occurrences) for d in duplicates)
