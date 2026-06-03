"""Ratchet C: cryptographic human anti-bypass guard for ratchet config files."""

from __future__ import annotations

import os
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

RATCHET_NAME = "anti_bypass"

BYPASS_KEY_ENV = "HUMAN_RATCHET_BYPASS_KEY"

# Environment signatures that strongly suggest an automated agent process is
# driving the commit. Presence of ANY of these elevates the guard's sensitivity.
AGENT_ENV_SIGNATURES: tuple[str, ...] = (
    "CURSOR_AGENT",
    "CLAUDE_CODE",
    "CLAUDECODE",
    "AIDER",
    "AIDER_AUTO_COMMIT",
    "COPILOT_AGENT",
    "GITHUB_COPILOT_AGENT",
    "CODEX_AGENT",
    "OPENAI_AGENT",
)


@dataclass(frozen=True)
class BypassDecision:
    """Outcome of an anti-bypass evaluation."""

    blocked: bool
    reason: str
    touched_protected_files: tuple[str, ...]
    agent_signal: str | None


def _normalize(path: str | Path) -> str:
    return Path(path).as_posix().lstrip("./")


def detect_agent_signal(env: dict[str, str] | None = None) -> str | None:
    """Return the name of the first detected agent env var, or None."""
    source = env if env is not None else os.environ
    for key in AGENT_ENV_SIGNATURES:
        if source.get(key):
            return key
    return None


def bypass_key_present(env: dict[str, str] | None = None) -> bool:
    """Return True iff HUMAN_RATCHET_BYPASS_KEY is set to a non-empty value."""
    source = env if env is not None else os.environ
    return bool(source.get(BYPASS_KEY_ENV, "").strip())


def evaluate(
    staged_files: Iterable[str | Path],
    protected_files: Iterable[str | Path],
    env: dict[str, str] | None = None,
) -> BypassDecision:
    """Decide whether the current commit must be blocked by the anti-bypass guard."""
    protected_norm = {_normalize(p) for p in protected_files}
    touched = tuple(
        sorted({_normalize(f) for f in staged_files if _normalize(f) in protected_norm})
    )
    agent_signal = detect_agent_signal(env)
    has_key = bypass_key_present(env)

    if not touched:
        return BypassDecision(
            blocked=False,
            reason="no protected files in staged set",
            touched_protected_files=(),
            agent_signal=agent_signal,
        )
    if has_key:
        return BypassDecision(
            blocked=False,
            reason=f"{BYPASS_KEY_ENV} present; human bypass granted",
            touched_protected_files=touched,
            agent_signal=agent_signal,
        )
    if agent_signal:
        reason = (
            f"protected ratchet file mutation detected with agent signal "
            f"'{agent_signal}' and no {BYPASS_KEY_ENV}"
        )
    else:
        reason = (
            f"protected ratchet file mutation detected with no {BYPASS_KEY_ENV}; "
            "human intent must be asserted explicitly"
        )
    return BypassDecision(
        blocked=True,
        reason=reason,
        touched_protected_files=touched,
        agent_signal=agent_signal,
    )
