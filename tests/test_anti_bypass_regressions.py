"""Regression tests for ``git_agent_ratchet.ratchets.anti_bypass``.

Each test pins the behaviour of a specific bug. The docstring explains
what went wrong, the impact, and the fix in plain English.
"""

from __future__ import annotations

from git_agent_ratchet.ratchets.anti_bypass import (
    BYPASS_KEY_ENV,
    _normalize,
    evaluate,
)


def test_normalize_preserves_leading_dot_in_dotfiles() -> None:
    """Dotfiles like ``.pre-commit-hooks.yaml`` must keep their leading dot.

    Bug: ``_normalize`` used ``Path(p).as_posix().lstrip("./")``. ``str.lstrip``
    takes a *set of characters*, not a literal prefix, so the call stripped
    any leading ``.`` and ``/`` characters. That mangled every dotfile path:
    ``.pre-commit-hooks.yaml`` -> ``pre-commit-hooks.yaml``,
    ``.env`` -> ``env``, ``.github/workflows/ci.yml`` ->
    ``github/workflows/ci.yml``.

    Impact: the gate output reported the wrong filename to the user (the
    Ratchet C message claimed it was protecting ``pre-commit-hooks.yaml``
    when the actual on-disk file was ``.pre-commit-hooks.yaml``). The
    enforcement itself still fired because both sides of the comparison
    were mangled identically, but the diagnostic noise made the failure
    confusing to debug.

    Fix: strip only the literal ``./`` prefix, leaving any other leading
    dot intact.
    """
    assert _normalize(".pre-commit-hooks.yaml") == ".pre-commit-hooks.yaml"
    assert _normalize(".env") == ".env"
    assert _normalize(".github/workflows/ci.yml") == ".github/workflows/ci.yml"
    assert _normalize("./AGENTS.md") == "AGENTS.md"
    assert _normalize("AGENTS.md") == "AGENTS.md"


def test_blocked_decision_reports_dotfile_with_leading_dot_intact() -> None:
    """End-to-end: blocking on ``.pre-commit-hooks.yaml`` reports the real name.

    Companion to the ``_normalize`` regression above. Before the fix, the
    ``touched_protected_files`` tuple on a blocked decision would contain
    ``"pre-commit-hooks.yaml"`` with the dot stripped -- the exact string
    the user sees in the failure output.
    """
    decision = evaluate(
        staged_files=[".pre-commit-hooks.yaml"],
        protected_files=[".pre-commit-hooks.yaml"],
        env={},
    )
    assert decision.blocked is True
    assert decision.touched_protected_files == (".pre-commit-hooks.yaml",)
    assert BYPASS_KEY_ENV in decision.reason
