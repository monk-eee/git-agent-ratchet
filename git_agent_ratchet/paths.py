"""Shared path utilities used by the ratchet scanners."""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from pathlib import Path


def relative_posix(path: Path, anchor: Path) -> str:
    """Return ``path`` as a posix string, relative to ``anchor`` when possible.

    Falls back to the raw path string if ``path`` does not sit under ``anchor``
    (which happens when callers pass an unrelated working directory).
    """
    try:
        rel = path.resolve().relative_to(anchor.resolve())
    except ValueError:
        rel = path
    return rel.as_posix()


def strip_dot_slash(value: str) -> str:
    """Remove a single leading ``./`` from a posix-style path string.

    Use this instead of ``str.lstrip("./")`` -- ``lstrip`` treats its argument
    as a *set of characters* and would strip every leading ``.``/``/``, mangling
    dotfiles like ``.pre-commit-hooks.yaml`` into ``pre-commit-hooks.yaml``.
    """
    return value[2:] if value.startswith("./") else value


def iter_python_files(root: Path, exclude_dirs: Iterable[str] = ()) -> Iterator[Path]:
    """Yield ``.py`` files under ``root``, skipping any path with an excluded segment.

    The shared walker used by Ratchets D, E, and F. Exclusion is case-insensitive
    and matches any path segment (e.g. ``tests`` filters ``pkg/tests/x.py``).
    """
    excluded = {d.lower() for d in exclude_dirs}
    for path in sorted(root.rglob("*.py")):
        parts = {p.lower() for p in path.parts}
        if parts & excluded:
            continue
        yield path
