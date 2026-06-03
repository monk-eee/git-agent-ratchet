"""Ratchet D: line-count enforcement for source files.

The 350-line soft rule from AGENTS.md, made mechanical. Files larger than
the threshold are recorded in the baseline; the total overage (sum of
``line_count - max`` across over-sized files) is the headline metric and
is permitted to shrink or stay flat across commits, never to grow.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path

from git_agent_ratchet.paths import relative_posix

RATCHET_NAME = "max_file_lines"
DEFAULT_EXCLUDE_DIRS = ("tests", "test")
DEFAULT_MAX_LINES = 350


@dataclass(frozen=True)
class OversizedFile:
    """A source file whose line count exceeds the configured threshold."""

    path: str
    line_count: int
    overage: int

    def to_dict(self) -> dict[str, object]:
        return {"path": self.path, "line_count": self.line_count, "overage": self.overage}


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


def count_lines(source_path: Path) -> int:
    """Return the line count of source_path, or 0 if the file cannot be read."""
    try:
        text = source_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return 0
    if not text:
        return 0
    # Mirror `wc -l` style: a final newline does not add a phantom blank line.
    return len(text.splitlines())


def scan_directory(
    root: Path,
    max_lines: int = DEFAULT_MAX_LINES,
    exclude_dirs: Iterable[str] = DEFAULT_EXCLUDE_DIRS,
) -> list[OversizedFile]:
    """Scan root and return every .py file whose line count exceeds max_lines."""
    if not root.exists():
        return []
    anchor = root.parent if root.parent.exists() else root
    oversized: list[OversizedFile] = []
    for py_file in iter_python_files(root, exclude_dirs):
        lines = count_lines(py_file)
        if lines > max_lines:
            oversized.append(
                OversizedFile(
                    path=relative_posix(py_file, anchor),
                    line_count=lines,
                    overage=lines - max_lines,
                )
            )
    oversized.sort(key=lambda f: (-f.overage, f.path))
    return oversized


def metric_value(oversized: list[OversizedFile]) -> int:
    """Compute the total line overage across all over-sized files."""
    return sum(f.overage for f in oversized)
