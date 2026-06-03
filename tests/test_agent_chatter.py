"""Tests for the regex-based agent-chatter scanner (Ratchet B's pure logic)."""

from __future__ import annotations

from pathlib import Path

import pytest

from git_agent_ratchet.ratchets.agent_chatter import (
    CHATTER_SIGNATURES,
    ChatterMatch,
    scan_files,
    scan_text,
)


# fmt: off
@pytest.mark.parametrize(
    ("text", "expected_signature"),
    [
        ("Sure, I can help with modifying this code...", "sure-i-can-help-with"),  # noqa: E501  ratchet-allow: agent_chatter
        ("# I can help with that fix.", "sure-i-can-help-with"),  # ratchet-allow: agent_chatter
        ("As an AI, I am tasked with maintaining structural parameters", "as-an-ai"),  # noqa: E501  ratchet-allow: agent_chatter
        ("// As an AI, this looks great.", "as-an-ai"),  # ratchet-allow: agent_chatter
        ("I have successfully updated the workspace dependencies.", "i-have-successfully"),  # noqa: E501  ratchet-allow: agent_chatter
        ("I have successfully modified the build pipeline.", "i-have-successfully"),  # noqa: E501  ratchet-allow: agent_chatter
        ("# Now let me check the docs directory to confirm layout...", "now-let-me-check"),  # noqa: E501  ratchet-allow: agent_chatter
        ("Now let me check the dir for stragglers.", "now-let-me-check"),  # ratchet-allow: agent_chatter
    ],
)
# fmt: on
def test_each_signature_fires(text: str, expected_signature: str) -> None:
    matches = scan_text(text, file_label="x")
    assert len(matches) == 1
    assert matches[0].signature == expected_signature


def test_clean_text_returns_no_matches() -> None:
    clean = "def add(a, b):\n    return a + b\n\n# This computes the sum of two numbers.\n"
    assert scan_text(clean, file_label="x") == []


def test_signatures_are_case_insensitive() -> None:
    # fmt: off
    matches = scan_text("SURE, I CAN HELP WITH this", file_label="x")  # ratchet-allow: agent_chatter
    # fmt: on
    assert len(matches) == 1
    assert matches[0].signature == "sure-i-can-help-with"


def test_match_records_line_number_and_text() -> None:
    text = "line one\n# As an AI, here you go\nline three\n"  # ratchet-allow: agent_chatter
    matches = scan_text(text, file_label="some/file.py")

    assert len(matches) == 1
    assert matches[0].line_number == 2
    assert matches[0].file == "some/file.py"
    assert "As an AI" in matches[0].line


def test_only_one_match_per_line_even_if_multiple_signatures_overlap() -> None:
    # The scanner breaks after the first matching signature per line.
    # fmt: off
    text = "Sure, I can help with this. As an AI, I should add that.\n"  # ratchet-allow: agent_chatter
    # fmt: on
    matches = scan_text(text, file_label="x")
    assert len(matches) == 1


def test_scan_files_skips_missing_files(tmp_path: Path) -> None:
    assert scan_files([tmp_path / "missing.txt"]) == []


def test_scan_files_skips_binary_decode_errors(tmp_path: Path) -> None:
    p = tmp_path / "binary.bin"
    p.write_bytes(b"\xff\xfe\xfa\xfb non-utf8 bytes")
    assert scan_files([p]) == []


def test_scan_files_finds_chatter_in_real_file(tmp_path: Path) -> None:
    p = tmp_path / "leaked.md"
    # fmt: off
    p.write_text("# heading\nSure, I can help with that.\n", encoding="utf-8")  # ratchet-allow: agent_chatter
    # fmt: on

    matches = scan_files([p])

    assert len(matches) == 1
    assert matches[0].file == str(p)
    assert matches[0].line_number == 2


def test_signature_table_is_non_empty() -> None:
    assert len(CHATTER_SIGNATURES) >= 4
    for label, pattern in CHATTER_SIGNATURES:
        assert label
        assert pattern.flags  # all patterns are compiled


def test_allow_marker_suppresses_match_on_same_line() -> None:
    # The escape-hatch for docs/tests that legitimately quote chatter.
    # fmt: off
    text = "As an AI, this should still match.\nAs an AI, this should not.  # ratchet-allow: agent_chatter\n"  # ratchet-allow: agent_chatter
    # fmt: on
    matches = scan_text(text, file_label="x")
    assert len(matches) == 1
    assert matches[0].line_number == 1


def test_allow_marker_in_html_comment_works_in_markdown() -> None:
    # fmt: off
    text = '| `(?i)as\\san\\sai,` | "As an AI, ..." | <!-- ratchet-allow: agent_chatter -->\n'
    # fmt: on
    assert scan_text(text, file_label="x.md") == []


def test_chatter_match_is_frozen() -> None:
    m = ChatterMatch(file="x", line_number=1, signature="s", line="l")
    with pytest.raises(Exception):  # noqa: B017 -- FrozenInstanceError under any dataclass impl
        m.file = "y"  # type: ignore[misc]
