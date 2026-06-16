"""Tests for the regex-based PowerShell usage scanner (Ratchet H)."""

from __future__ import annotations

from pathlib import Path

import pytest

from git_agent_ratchet.ratchets.powershell_usage import (
    POWERSHELL_SIGNATURES,
    PowerShellMatch,
    scan_files,
    scan_text,
)


@pytest.mark.parametrize(
    ("text", "expected_signature"),
    [
        (
            'powershell -NoProfile -Command "Get-ChildItem"  # ratchet-allow: powershell_usage',
            "powershell-executable",
        ),
        (
            "pwsh -NoLogo -Command ./script.ps1  # ratchet-allow: powershell_usage",
            "powershell-executable",
        ),
        (
            "./scripts/bootstrap.ps1  # ratchet-allow: powershell_usage",
            "powershell-script-extension",
        ),
        ("Get-ChildItem -Path .  # ratchet-allow: powershell_usage", "powershell-cmdlet"),
        ('$env:PATH = "x"  # ratchet-allow: powershell_usage', "powershell-env-prefix"),
    ],
)
def test_each_signature_fires(text: str, expected_signature: str) -> None:
    matches = scan_text(text.replace("  # ratchet-allow: powershell_usage", ""), file_label="x")
    assert len(matches) == 1
    assert matches[0].signature == expected_signature


def test_clean_text_returns_no_matches() -> None:
    clean = "def add(a, b):\n    return a + b\n"
    assert scan_text(clean, file_label="x") == []


def test_match_records_line_number_and_text() -> None:
    text = 'line one\nrun: powershell -Command "echo hi"\nline three\n'  # ratchet-allow: powershell_usage
    matches = scan_text(text, file_label="some/file.yml")

    assert len(matches) == 1
    assert matches[0].line_number == 2
    assert matches[0].file == "some/file.yml"
    assert "powershell" in matches[0].line


def test_only_one_match_per_line_even_if_multiple_signatures_overlap() -> None:
    text = "pwsh -Command ./build.ps1\n"  # ratchet-allow: powershell_usage
    matches = scan_text(text, file_label="x")
    assert len(matches) == 1


def test_scan_files_skips_missing_files(tmp_path: Path) -> None:
    assert scan_files([tmp_path / "missing.txt"]) == []


def test_scan_files_skips_binary_decode_errors(tmp_path: Path) -> None:
    p = tmp_path / "binary.bin"
    p.write_bytes(b"\xff\xfe\xfa\xfb non-utf8 bytes")
    assert scan_files([p]) == []


def test_scan_files_finds_match_in_real_file(tmp_path: Path) -> None:
    p = tmp_path / "leaked.md"
    p.write_text(
        "# heading\nSet-ExecutionPolicy RemoteSigned\n",  # ratchet-allow: powershell_usage
        encoding="utf-8",
    )

    matches = scan_files([p])

    assert len(matches) == 1
    assert matches[0].file == str(p)
    assert matches[0].line_number == 2


def test_signature_table_is_non_empty() -> None:
    assert len(POWERSHELL_SIGNATURES) >= 4
    for label, pattern in POWERSHELL_SIGNATURES:
        assert label
        assert pattern.flags


def test_allow_marker_suppresses_match_on_same_line() -> None:
    text = (
        "powershell -NoProfile\n"  # ratchet-allow: powershell_usage
        "Use powershell here.  # ratchet-allow: powershell_usage\n"
    )
    matches = scan_text(text, file_label="x")
    assert len(matches) == 1
    assert matches[0].line_number == 1


def test_powershell_match_is_frozen() -> None:
    m = PowerShellMatch(file="x", line_number=1, signature="s", line="l")
    with pytest.raises(Exception):  # noqa: B017 -- FrozenInstanceError under any dataclass impl
        m.file = "y"  # type: ignore[misc]
