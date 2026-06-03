"""Tests for the anti-bypass policy engine (Ratchet C's pure logic)."""

from __future__ import annotations

from git_agent_ratchet.ratchets.anti_bypass import (
    AGENT_ENV_SIGNATURES,
    BYPASS_KEY_ENV,
    bypass_key_present,
    detect_agent_signal,
    evaluate,
)


def test_no_protected_files_means_no_block() -> None:
    decision = evaluate(
        staged_files=["README.md", "src/x.py"],
        protected_files=["AGENTS.md"],
        env={},
    )
    assert decision.blocked is False
    assert decision.touched_protected_files == ()


def test_protected_file_with_no_bypass_key_blocks() -> None:
    decision = evaluate(
        staged_files=["AGENTS.md"],
        protected_files=["AGENTS.md"],
        env={},
    )
    assert decision.blocked is True
    assert decision.touched_protected_files == ("AGENTS.md",)
    assert BYPASS_KEY_ENV in decision.reason


def test_bypass_key_present_allows_through() -> None:
    decision = evaluate(
        staged_files=["AGENTS.md"],
        protected_files=["AGENTS.md"],
        env={BYPASS_KEY_ENV: "let-me-in"},
    )
    assert decision.blocked is False
    assert decision.touched_protected_files == ("AGENTS.md",)
    assert "human bypass granted" in decision.reason


def test_empty_bypass_key_does_not_count_as_present() -> None:
    decision = evaluate(
        staged_files=["AGENTS.md"],
        protected_files=["AGENTS.md"],
        env={BYPASS_KEY_ENV: "   "},
    )
    assert decision.blocked is True


def test_agent_signal_detection_surfaces_first_match() -> None:
    env = {"CLAUDECODE": "1", "CURSOR_AGENT": "1"}
    signal = detect_agent_signal(env)
    assert signal in AGENT_ENV_SIGNATURES
    # First match in the priority list wins.
    assert signal == "CURSOR_AGENT"


def test_no_agent_signal_returns_none() -> None:
    assert detect_agent_signal({}) is None
    assert detect_agent_signal({"PATH": "/usr/bin"}) is None


def test_agent_signal_named_in_blocked_reason() -> None:
    decision = evaluate(
        staged_files=["AGENTS.md"],
        protected_files=["AGENTS.md"],
        env={"AIDER": "1"},
    )
    assert decision.blocked is True
    assert decision.agent_signal == "AIDER"
    assert "AIDER" in decision.reason


def test_path_normalisation_matches_protected_set() -> None:
    decision = evaluate(
        staged_files=["./config/ratchets/duplicates.json"],
        protected_files=["config/ratchets/duplicates.json"],
        env={},
    )
    assert decision.blocked is True
    assert "config/ratchets/duplicates.json" in decision.touched_protected_files


def test_bypass_key_present_helper_strips_whitespace() -> None:
    assert bypass_key_present({BYPASS_KEY_ENV: ""}) is False
    assert bypass_key_present({BYPASS_KEY_ENV: "   "}) is False
    assert bypass_key_present({BYPASS_KEY_ENV: "x"}) is True
    assert bypass_key_present({}) is False


def test_reason_never_echoes_bypass_key_value() -> None:
    # Ratchet C must not leak the secret value into stderr/logs.
    secret = "super-sensitive-secret-value-do-not-leak"
    decision = evaluate(
        staged_files=["AGENTS.md"],
        protected_files=["AGENTS.md"],
        env={BYPASS_KEY_ENV: secret},
    )
    assert decision.blocked is False
    assert secret not in decision.reason
