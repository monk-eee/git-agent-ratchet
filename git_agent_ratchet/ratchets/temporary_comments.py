"""Ratchet G: detect calcified-shortcut markers in source comments.

The prime-directive section of AGENTS.md enumerates the comment shapes
that signal an agent took the expedient path. Each gets shipped with the
best intentions and never removed; the comment itself is the smell. The
authoritative pattern table is :data:`TEMPORARY_SIGNATURES` below -- read
that rather than re-listing the phrases here, so this module does not
trip its own scanner.

The scanner is deliberately cross-language and line-based, mirroring the
Ratchet B (agent_chatter) shape. Any line containing the literal allow
marker ``ratchet-allow: temporary_comments`` is skipped, so files that
legitimately quote the patterns (this scanner, AGENTS.md, the tests)
can opt out per-line without weakening the rule globally.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from git_agent_ratchet.paths import relative_posix

RATCHET_NAME = "temporary_comments"
DEFAULT_EXCLUDE_DIRS = ("tests", "test", "node_modules", ".venv", "venv", "dist", "build")
DEFAULT_EXTENSIONS = (".py", ".ts", ".tsx", ".js", ".jsx", ".cs", ".go", ".rs", ".java", ".kt")

ALLOW_MARKER = "ratchet-allow: temporary_comments"

# Each entry: a stable signature label and a regex matched against the raw
# source line. Patterns target comment-shaped intent rather than the bare
# words -- the literal word ``legacy`` in a class name, for example, is fine.
TEMPORARY_SIGNATURES: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "for-now",
        re.compile(r"(?i)(?<![A-Za-z0-9_])(just\s+)?for\s+now(?![A-Za-z0-9_])"),
    ),
    (
        "back-compat",  # ratchet-allow: temporary_comments
        re.compile(r"(?i)(?<![A-Za-z0-9_])back[-\s]?compat(ibility)?(?![A-Za-z0-9_])"),
    ),
    (
        "transitional-bridge",
        re.compile(
            r"(?i)(?<![A-Za-z0-9_])(transitional\s+bridge|temporary\s+bridge)(?![A-Za-z0-9_])"
        ),
    ),
    (
        "todo-remove-once",
        re.compile(r"(?i)todo:?\s*remove\s+(once|when|after)\b"),
    ),
    (
        "hack-fix-later",
        re.compile(
            r"(?i)(?<![A-Za-z0-9_])(hack|hacky)[:\s].*?(fix\s+later|temporary)(?![A-Za-z0-9_])"
        ),
    ),
)


@dataclass(frozen=True)
class TemporaryMarker:
    """A single source line that matched one of the temporary-comment signatures."""

    file: str
    line: int
    signature: str
    snippet: str

    def to_dict(self) -> dict[str, object]:
        return {
            "file": self.file,
            "line": self.line,
            "signature": self.signature,
            "snippet": self.snippet,
        }


def scan_text(text: str, file_label: str) -> list[TemporaryMarker]:
    """Return every line in ``text`` that matches a temporary-comment signature."""
    matches: list[TemporaryMarker] = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        if ALLOW_MARKER in raw_line:
            continue
        for signature, pattern in TEMPORARY_SIGNATURES:
            if pattern.search(raw_line):
                matches.append(
                    TemporaryMarker(
                        file=file_label,
                        line=line_number,
                        signature=signature,
                        snippet=raw_line.strip()[:200],
                    )
                )
                break
    return matches


def scan_file(source_path: Path, file_label: str | None = None) -> list[TemporaryMarker]:
    """Scan a single file; skip unreadable / binary files silently."""
    label = file_label if file_label is not None else str(source_path)
    try:
        text = source_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    return scan_text(text, file_label=label)


def scan_directory(
    root: Path,
    exclude_dirs: Iterable[str] = DEFAULT_EXCLUDE_DIRS,
    extensions: Iterable[str] = DEFAULT_EXTENSIONS,
) -> list[TemporaryMarker]:
    """Walk ``root`` and return every temporary-comment match across the tree."""
    if not root.exists():
        return []
    anchor = root.parent if root.parent.exists() else root
    excluded = {d.lower() for d in exclude_dirs}
    suffixes = {s.lower() for s in extensions}
    matches: list[TemporaryMarker] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in suffixes:
            continue
        parts = {p.lower() for p in path.parts}
        if parts & excluded:
            continue
        matches.extend(scan_file(path, file_label=relative_posix(path, anchor)))
    matches.sort(key=lambda m: (m.file, m.line))
    return matches


def metric_value(matches: list[TemporaryMarker]) -> int:
    """Return the total count of temporary-comment matches."""
    return len(matches)
