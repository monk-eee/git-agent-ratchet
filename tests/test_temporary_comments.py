"""Tests for the temporary-comments scanner (Ratchet G)."""

from __future__ import annotations

from pathlib import Path

import pytest

from git_agent_ratchet.ratchets.temporary_comments import (
    TEMPORARY_SIGNATURES,
    TemporaryMarker,
    metric_value,
    scan_directory,
    scan_file,
    scan_text,
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_signature_table_is_non_empty() -> None:
    assert len(TEMPORARY_SIGNATURES) >= 4
    for label, pattern in TEMPORARY_SIGNATURES:
        assert label
        assert pattern.flags


@pytest.mark.parametrize(
    "line,expected_sig",
    [
        ("# for now we ignore this", "for-now"),
        ("// just for now", "for-now"),
        ("/* back-compat shim until v2 */", "back-compat"),
        ("# backcompat fallback", "back-compat"),
        ("// transitional bridge: kill after migration", "transitional-bridge"),
        ("# TODO: remove once feature flag lands", "todo-remove-once"),
        ("# todo remove when X migrates", "todo-remove-once"),
        ("# HACK: fix later", "hack-fix-later"),
    ],
)
def test_scan_text_matches_known_signatures(line: str, expected_sig: str) -> None:
    matches = scan_text(line + "\n", file_label="x.py")
    assert len(matches) == 1
    assert matches[0].signature == expected_sig


def test_scan_text_skips_lines_with_allow_marker() -> None:
    text = (
        "# for now we accept this  # ratchet-allow: temporary_comments\n"
        "# legitimate temporary bridge -- ratchet-allow: temporary_comments\n"
    )
    assert scan_text(text, file_label="x.py") == []


def test_scan_text_records_line_numbers_and_snippet() -> None:
    text = "x = 1\ny = 2  # back-compat for the v0 API\nz = 3\n"
    matches = scan_text(text, file_label="x.py")
    assert len(matches) == 1
    assert matches[0].line == 2
    assert "back-compat" in matches[0].snippet


def test_scan_text_breaks_on_first_signature_per_line() -> None:
    # A line that hits two patterns is counted once (the scanner short-circuits).
    text = "# for now this is a back-compat shim\n"
    matches = scan_text(text, file_label="x.py")
    assert len(matches) == 1


def test_scan_text_does_not_match_unrelated_words() -> None:
    text = "class LegacyClient: pass\nbackup_compat = True\nformat_now()\n"
    matches = scan_text(text, file_label="x.py")
    assert matches == []


def test_scan_file_handles_missing_file(tmp_path: Path) -> None:
    assert scan_file(tmp_path / "absent.py") == []


def test_scan_file_handles_binary_file(tmp_path: Path) -> None:
    p = tmp_path / "bin.py"
    p.write_bytes(b"\xff\xfe\x00\x00")
    assert scan_file(p) == []


def test_scan_directory_walks_supported_extensions(tmp_path: Path) -> None:
    pkg = tmp_path / "pkg"
    _write(pkg / "a.py", "# for now\n")
    _write(pkg / "b.ts", "// back-compat\n")
    _write(pkg / "c.cs", "// transitional bridge\n")
    _write(pkg / "d.md", "# for now\n")  # md is not in default extensions

    matches = scan_directory(pkg)

    files = {m.file.split("/")[-1] for m in matches}
    assert files == {"a.py", "b.ts", "c.cs"}


def test_scan_directory_excludes_tests_and_vendor_dirs_by_default(tmp_path: Path) -> None:
    pkg = tmp_path / "pkg"
    _write(pkg / "src.py", "# for now\n")
    _write(pkg / "tests" / "t.py", "# for now\n")
    _write(pkg / "node_modules" / "dep.py", "# for now\n")
    _write(pkg / ".venv" / "lib.py", "# for now\n")

    matches = scan_directory(pkg)

    assert len(matches) == 1
    assert matches[0].file.endswith("src.py")


def test_scan_directory_returns_empty_when_root_missing(tmp_path: Path) -> None:
    assert scan_directory(tmp_path / "nope") == []


def test_scan_directory_is_idempotent(tmp_path: Path) -> None:
    pkg = tmp_path / "pkg"
    _write(pkg / "a.py", "# for now\n")

    assert scan_directory(pkg) == scan_directory(pkg)


def test_metric_value_counts_each_match() -> None:
    items = [
        TemporaryMarker(file="a.py", line=1, signature="for-now", snippet="..."),
        TemporaryMarker(file="b.py", line=2, signature="back-compat", snippet="..."),
    ]
    assert metric_value(items) == 2


def test_metric_value_is_zero_for_empty_list() -> None:
    assert metric_value([]) == 0


def test_temporary_marker_to_dict_shape() -> None:
    m = TemporaryMarker(file="a.py", line=3, signature="for-now", snippet="x")
    assert m.to_dict() == {
        "file": "a.py",
        "line": 3,
        "signature": "for-now",
        "snippet": "x",
    }
