"""Tests for the Ratchet H hook entry point (dont-use-powershell)."""

from __future__ import annotations

from pathlib import Path

from git_agent_ratchet.hooks.dont_use_powershell import main


def test_clean_file_passes(tmp_path: Path) -> None:
    p = tmp_path / "clean.py"
    p.write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")

    exit_code = main([str(p)])

    assert exit_code == 0


def test_file_with_powershell_blocks(tmp_path: Path, capsys) -> None:
    p = tmp_path / "leaked.md"
    p.write_text(
        'run: pwsh -NoProfile -Command "Get-ChildItem"\n',  # ratchet-allow: powershell_usage
        encoding="utf-8",
    )

    exit_code = main([str(p)])

    assert exit_code == 1
    err = capsys.readouterr().err
    assert "GATE TRIPPED" in err
    assert "powershell-executable" in err
    assert str(p) in err


def test_no_files_argument_passes(capsys) -> None:
    exit_code = main([])
    assert exit_code == 0
    assert capsys.readouterr().err == ""


def test_multiple_files_one_dirty_blocks(tmp_path: Path) -> None:
    clean = tmp_path / "clean.py"
    clean.write_text("x = 1\n", encoding="utf-8")
    dirty = tmp_path / "dirty.md"
    dirty.write_text(
        "Set-ExecutionPolicy RemoteSigned\n",  # ratchet-allow: powershell_usage
        encoding="utf-8",
    )

    exit_code = main([str(clean), str(dirty)])

    assert exit_code == 1


def test_missing_files_do_not_crash(tmp_path: Path) -> None:
    exit_code = main([str(tmp_path / "nope.txt")])
    assert exit_code == 0
