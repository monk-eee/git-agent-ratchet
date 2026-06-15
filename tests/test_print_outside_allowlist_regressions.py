"""Regression tests for ``ratchets.print_outside_allowlist.is_allowed``."""

from __future__ import annotations

from git_agent_ratchet.ratchets.print_outside_allowlist import is_allowed


def test_is_allowed_does_not_match_bare_string_prefix() -> None:
    """A prefix must match a path *segment*, not an arbitrary string prefix.

    Bug: ``is_allowed`` ended its check with ``or label.startswith(norm)``.
    That made a prefix like ``pkg/cli`` wrongly allow ``pkg/client.py``
    (and ``src/util`` allow ``src/utility.py``), silently exempting files
    the operator never intended to allowlist. The fix matches only the exact
    file or a directory boundary (``norm`` + ``/``).
    """
    assert is_allowed("pkg/client.py", ["pkg/cli"]) is False
    assert is_allowed("src/utility.py", ["src/util"]) is False
    # The legitimate directory-prefix and exact-file matches still hold.
    assert is_allowed("pkg/cli/main.py", ["pkg/cli"]) is True
    assert is_allowed("pkg/cli.py", ["pkg/cli.py"]) is True
