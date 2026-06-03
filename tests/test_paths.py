"""Tests for the shared path utilities used by the ratchet scanners."""

from __future__ import annotations

from pathlib import Path

from git_agent_ratchet.paths import relative_posix


def test_relative_posix_returns_posix_path_under_anchor(tmp_path: Path) -> None:
    anchor = tmp_path
    inside = tmp_path / "sub" / "file.py"
    inside.parent.mkdir()
    inside.write_text("x = 1\n", encoding="utf-8")

    assert relative_posix(inside, anchor) == "sub/file.py"


def test_relative_posix_falls_back_when_path_outside_anchor(tmp_path: Path) -> None:
    anchor = tmp_path / "anchor"
    anchor.mkdir()
    outside = tmp_path / "elsewhere" / "file.py"
    outside.parent.mkdir()
    outside.write_text("x = 1\n", encoding="utf-8")

    result = relative_posix(outside, anchor)

    assert result.endswith("elsewhere/file.py")
