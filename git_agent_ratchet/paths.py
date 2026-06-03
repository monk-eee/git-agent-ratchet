"""Shared path utilities used by the ratchet scanners."""

from __future__ import annotations

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
