"""Ratchet H: lexical detection of PowerShell command usage in staged files."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

RATCHET_NAME = "dont_use_powershell"

# Per-line escape hatch for docs/tests that legitimately quote a blocked token.
ALLOW_MARKER = "ratchet-allow: powershell_usage"

POWERSHELL_SIGNATURES: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "powershell-executable",
        re.compile(r"(?i)(^|\s)(powershell(\.exe)?|pwsh(\.exe)?)(?=\s+[-/])"),
    ),
    (
        "powershell-script-extension",
        re.compile(r"(?i)(^|\s)[\w./\\-]+\.ps1(?=\s|$|['\"])"),
    ),
    (
        "powershell-cmdlet",
        re.compile(
            r"(?i)(^|\s)(Get-ChildItem|Select-String|ForEach-Object|Where-Object|"
            r"Set-ExecutionPolicy|Invoke-Expression|Start-Process)(?=\s|$)"
        ),
    ),
    (
        "powershell-env-prefix",
        re.compile(r"(?i)(^|\s)\$env:[A-Za-z_][A-Za-z0-9_]*"),
    ),
)


@dataclass(frozen=True)
class PowerShellMatch:
    """A single line that matched one of the PowerShell usage signatures."""

    file: str
    line_number: int
    signature: str
    line: str


def scan_text(text: str, file_label: str) -> list[PowerShellMatch]:
    """Scan text and return every line that matches any PowerShell signature."""
    matches: list[PowerShellMatch] = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        if ALLOW_MARKER in raw_line:
            continue
        for signature, pattern in POWERSHELL_SIGNATURES:
            if pattern.search(raw_line):
                matches.append(
                    PowerShellMatch(
                        file=file_label,
                        line_number=line_number,
                        signature=signature,
                        line=raw_line.rstrip(),
                    )
                )
                break
    return matches


def scan_files(paths: Iterable[Path]) -> list[PowerShellMatch]:
    """Scan each file in paths; silently skip unreadable or binary files."""
    matches: list[PowerShellMatch] = []
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        matches.extend(scan_text(text, file_label=str(path)))
    return matches
