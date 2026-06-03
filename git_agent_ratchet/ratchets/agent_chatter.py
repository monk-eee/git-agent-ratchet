"""Ratchet B: lexical detection of agent-chatter artifacts leaking into files."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

RATCHET_NAME = "agent_chatter"

# A line containing this literal substring is skipped by the scanner.
# Lets repos that legitimately quote chatter (this very codebase, security
# regression tests, docs explaining the rule) opt out per-line, the same
# way ruff lets you opt out with a noqa comment.
ALLOW_MARKER = "ratchet-allow: agent_chatter"

# Regex signatures sourced directly from the spec table. Each entry pairs a
# compiled pattern with a human-readable label used in failure output.
CHATTER_SIGNATURES: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "sure-i-can-help-with",
        re.compile(r"(?i)(sure,\s)?i\scan\shelp\swith"),
    ),
    (
        "as-an-ai",
        re.compile(r"(?i)as\san\sai,\s(i\s)?"),
    ),
    (
        "i-have-successfully",
        re.compile(r"(?i)i\shave\ssuccessfully\s(modified|updated)"),
    ),
    (
        "now-let-me-check",
        re.compile(r"(?i)now\slet\sme\scheck\sthe\s(docs|dir)"),
    ),
)


@dataclass(frozen=True)
class ChatterMatch:
    """A single line that matched one of the chatter signatures."""

    file: str
    line_number: int
    signature: str
    line: str


def scan_text(text: str, file_label: str) -> list[ChatterMatch]:
    """Scan text and return every line that matches any chatter signature."""
    matches: list[ChatterMatch] = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        if ALLOW_MARKER in raw_line:
            continue
        for signature, pattern in CHATTER_SIGNATURES:
            if pattern.search(raw_line):
                matches.append(
                    ChatterMatch(
                        file=file_label,
                        line_number=line_number,
                        signature=signature,
                        line=raw_line.rstrip(),
                    )
                )
                break
    return matches


def scan_files(paths: Iterable[Path]) -> list[ChatterMatch]:
    """Scan each file in paths; silently skip unreadable or binary files."""
    matches: list[ChatterMatch] = []
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        matches.extend(scan_text(text, file_label=str(path)))
    return matches
