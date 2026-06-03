"""Tests for the Ratchet C hook entry point (anti-bypass)."""

from __future__ import annotations

from git_agent_ratchet.hooks.anti_bypass import main
from git_agent_ratchet.ratchets.anti_bypass import BYPASS_KEY_ENV


def test_no_protected_files_in_staged_set_passes(monkeypatch) -> None:
    monkeypatch.delenv(BYPASS_KEY_ENV, raising=False)
    exit_code = main(
        ["--enforce-files", "AGENTS.md,.pre-commit-config.yaml", "README.md", "src/x.py"]
    )
    assert exit_code == 0


def test_protected_file_touched_without_key_blocks(monkeypatch, capsys) -> None:
    monkeypatch.delenv(BYPASS_KEY_ENV, raising=False)
    for sig in ("CURSOR_AGENT", "CLAUDECODE", "AIDER", "COPILOT_AGENT"):
        monkeypatch.delenv(sig, raising=False)

    exit_code = main(["--enforce-files", "AGENTS.md", "AGENTS.md"])

    assert exit_code == 1
    err = capsys.readouterr().err
    assert "GATE TRIPPED" in err
    assert "AGENTS.md" in err
    assert BYPASS_KEY_ENV in err


def test_bypass_key_set_allows_through(monkeypatch, capsys) -> None:
    monkeypatch.setenv(BYPASS_KEY_ENV, "i-am-a-human")

    exit_code = main(["--enforce-files", "AGENTS.md", "AGENTS.md"])

    assert exit_code == 0
    # Stderr must not contain the secret value.
    err = capsys.readouterr().err
    assert "i-am-a-human" not in err


def test_agent_signal_named_in_failure_output(monkeypatch, capsys) -> None:
    monkeypatch.delenv(BYPASS_KEY_ENV, raising=False)
    monkeypatch.setenv("AIDER", "1")

    exit_code = main(["--enforce-files", "AGENTS.md", "AGENTS.md"])

    assert exit_code == 1
    err = capsys.readouterr().err
    assert "AIDER" in err


def test_enforce_files_splits_and_trims(monkeypatch) -> None:
    monkeypatch.delenv(BYPASS_KEY_ENV, raising=False)
    for sig in ("CURSOR_AGENT", "CLAUDECODE", "AIDER", "COPILOT_AGENT"):
        monkeypatch.delenv(sig, raising=False)

    exit_code = main(
        [
            "--enforce-files",
            " AGENTS.md , .pre-commit-config.yaml , config/ratchets/duplicates.json ",
            "config/ratchets/duplicates.json",
        ]
    )

    assert exit_code == 1


def test_secret_never_logged(monkeypatch, capsys) -> None:
    secret = "ratchet-secret-must-not-leak"
    monkeypatch.setenv(BYPASS_KEY_ENV, secret)

    main(["--enforce-files", "AGENTS.md", "AGENTS.md"])

    captured = capsys.readouterr()
    assert secret not in captured.out
    assert secret not in captured.err
