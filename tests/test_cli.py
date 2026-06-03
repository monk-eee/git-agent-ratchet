"""Tests for the unified `git-agent-ratchet` CLI dispatcher."""

from __future__ import annotations

from pathlib import Path

import pytest

from git_agent_ratchet._version import __version__
from git_agent_ratchet.cli import SUBCOMMANDS, main


def test_subcommand_table_lists_all_three_ratchets() -> None:
    assert set(SUBCOMMANDS) == {
        "no-duplicate-helpers",
        "deny-agent-chatter",
        "anti-bypass",
    }


def test_version_flag_prints_package_version(capsys) -> None:
    with pytest.raises(SystemExit) as excinfo:
        main(["--version"])
    assert excinfo.value.code == 0
    out = capsys.readouterr().out
    assert __version__ in out


def test_missing_subcommand_errors(capsys) -> None:
    with pytest.raises(SystemExit) as excinfo:
        main([])
    assert excinfo.value.code != 0


def test_unknown_subcommand_errors(capsys) -> None:
    with pytest.raises(SystemExit) as excinfo:
        main(["not-a-real-subcommand"])
    assert excinfo.value.code != 0


def test_dispatch_to_no_duplicate_helpers_seeds_baseline(tmp_path: Path) -> None:
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "a.py").write_text("def public():\n    pass\n", encoding="utf-8")
    baseline = tmp_path / "duplicates.json"

    exit_code = main(
        [
            "no-duplicate-helpers",
            "--baseline",
            str(baseline),
            "--dir",
            str(pkg),
        ]
    )

    assert exit_code == 0
    assert baseline.exists()


def test_dispatch_to_deny_agent_chatter_passes_on_clean_file(tmp_path: Path) -> None:
    p = tmp_path / "clean.py"
    p.write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")

    exit_code = main(["deny-agent-chatter", str(p)])

    assert exit_code == 0


def test_dispatch_to_anti_bypass_blocks_protected_mutation(monkeypatch) -> None:
    monkeypatch.delenv("HUMAN_RATCHET_BYPASS_KEY", raising=False)

    exit_code = main(
        [
            "anti-bypass",
            "--enforce-files",
            "AGENTS.md",
            "AGENTS.md",
        ]
    )

    assert exit_code == 1


def test_module_entrypoint_runs_via_python_m(monkeypatch) -> None:
    """`python -m git_agent_ratchet --version` executes the __main__ shim end-to-end."""
    import runpy
    import sys

    monkeypatch.setattr(sys, "argv", ["git-agent-ratchet", "--version"])
    with pytest.raises(SystemExit) as excinfo:
        runpy.run_module("git_agent_ratchet", run_name="__main__")
    assert excinfo.value.code == 0
