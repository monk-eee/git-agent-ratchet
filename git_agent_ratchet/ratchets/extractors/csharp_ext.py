"""C# source extractor for Ratchet A.

Regex-based detection of ``private`` (and ``private static``) methods.
The class declaring the method is ignored: the rule fires on the method
*name* regardless of containing type, because the failure mode is agents
pasting the same helper into two unrelated classes.

Definition of "helper-shaped" for C#:

- Any line declaring a method whose first modifier token is ``private``.
- Optional modifiers (``static``, ``async``, ``virtual``, ``override``,
  ``sealed``, ``new``, ``unsafe``, ``extern``, ``partial``, ``readonly``)
  are tolerated in any order between ``private`` and the return type.
- The return type may carry one level of generics, an optional ``?``
  nullability marker, and ``[]`` array brackets.
- Properties (``private int Count => _count;``) are excluded because
  they don't end with ``(`` or ``<``.
- Constructors (``private MyClass(...)``) are excluded because the
  regex requires two identifiers between ``private`` and ``(``.
"""

from __future__ import annotations

import re
from pathlib import Path

NAME = "csharp"
EXTENSIONS: tuple[str, ...] = (".cs",)

_MODIFIERS = r"static|async|virtual|override|sealed|new|unsafe|extern|partial|readonly|abstract"
_RETURN_TYPE = r"[A-Za-z_][\w.]*(?:<[^>\n]+>)?\??(?:\[\])?"
_METHOD_NAME = r"[A-Za-z_][\w$]*"

_PRIVATE_METHOD_RE = re.compile(
    rf"^\s*private\b(?:\s+(?:{_MODIFIERS}))*\s+(?:{_RETURN_TYPE})"
    rf"\s+(?P<name>{_METHOD_NAME})\s*[(<]"
)


def extract_helpers(source_path: Path) -> list[str]:
    """Return names of private methods declared in the source file."""
    try:
        text = source_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    names: list[str] = []
    for line in text.splitlines():
        match = _PRIVATE_METHOD_RE.match(line)
        if match is not None:
            names.append(match.group("name"))
    return names
