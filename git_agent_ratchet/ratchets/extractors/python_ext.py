"""Python source extractor for Ratchet A.

A "helper-shaped" Python declaration is a top-level ``def`` or ``async
def`` whose name starts with a single underscore (``_foo``, ``_run_safe``)
but is not a dunder (``__init__``, ``__repr__``). Methods on classes and
nested functions are out of scope; they don't fork the way module-level
helpers do.
"""

from __future__ import annotations

import ast
from pathlib import Path

NAME = "python"
EXTENSIONS: tuple[str, ...] = (".py",)


def is_private_helper(name: str) -> bool:
    """Return True for private/semi-private identifiers (``_foo``) but not dunders."""
    if not name.startswith("_"):
        return False
    if name.startswith("__") and name.endswith("__"):
        return False
    return True


def collect_top_level_functions(source_path: Path) -> list[str]:
    """Return the names of all top-level function definitions in ``source_path``.

    Unreadable files and syntax errors yield an empty list so the
    scanner never crashes on a half-edited buffer.
    """
    try:
        source = source_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    try:
        tree = ast.parse(source, filename=str(source_path))
    except SyntaxError:
        return []
    return [
        node.name for node in tree.body if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
    ]


def extract_helpers(source_path: Path) -> list[str]:
    """Return the names of all private top-level helpers in a Python module."""
    return [name for name in collect_top_level_functions(source_path) if is_private_helper(name)]
