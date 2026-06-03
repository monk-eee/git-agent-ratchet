"""Ratchet A: cross-language detection of duplicate private helper functions."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path

from git_agent_ratchet.paths import relative_posix
from git_agent_ratchet.ratchets.extractors import select

RATCHET_NAME = "duplicate_helpers"
DEFAULT_EXCLUDE_DIRS = (
    "tests",
    "test",
    "node_modules",
    "bin",
    "obj",
    ".venv",
    "venv",
    "dist",
    "build",
)


@dataclass(frozen=True)
class DuplicateHelper:
    """A private helper function name found in two or more files."""

    name: str
    occurrences: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {"name": self.name, "occurrences": list(self.occurrences)}


def iter_source_files(
    root: Path,
    extensions: Iterable[str],
    exclude_dirs: Iterable[str] = DEFAULT_EXCLUDE_DIRS,
) -> Iterator[Path]:
    """Yield files under ``root`` whose suffix is in ``extensions``."""
    excluded = {d.lower() for d in exclude_dirs}
    suffixes = {s.lower() for s in extensions}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in suffixes:
            continue
        parts = {p.lower() for p in path.parts}
        if parts & excluded:
            continue
        yield path


def scan_directory(
    root: Path,
    exclude_dirs: Iterable[str] = DEFAULT_EXCLUDE_DIRS,
    languages: Iterable[str] | None = None,
) -> list[DuplicateHelper]:
    """Scan ``root`` and return helper names that appear in 2+ files.

    When ``languages`` is ``None``, every registered extractor runs.
    Each extractor is responsible for filtering to its language's notion
    of a "private helper", so this function never has to know.
    """
    if not root.exists():
        return []
    extractors = select(languages)
    grouped: dict[str, set[str]] = defaultdict(set)
    anchor = root.parent if root.parent.exists() else root
    for extractor in extractors:
        for src in iter_source_files(root, extractor.EXTENSIONS, exclude_dirs):
            rel = relative_posix(src, anchor)
            for name in extractor.extract_helpers(src):
                grouped[name].add(rel)
    duplicates = [
        DuplicateHelper(name=name, occurrences=tuple(sorted(paths)))
        for name, paths in grouped.items()
        if len(paths) >= 2
    ]
    duplicates.sort(key=lambda d: d.name)
    return duplicates


def metric_value(duplicates: list[DuplicateHelper]) -> int:
    """Compute the total occurrence count across all duplicate helper groups."""
    return sum(len(d.occurrences) for d in duplicates)
