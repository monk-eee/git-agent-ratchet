"""TypeScript / JavaScript source extractor for Ratchet A.

Regex-based and intentionally conservative. We trade off recall for
precision: the goal is to flag the high-signal fork pattern of an
*unexported* top-level helper appearing in two or more files, without
pulling in a Node-side parser as a runtime dependency.

Definition of "helper-shaped" for TS/JS:

- A top-level ``function NAME(...)`` (or ``async function``) declared at
  column zero and not preceded by ``export``.
- A top-level ``const NAME = (...) => ...`` (or ``async`` / ``function``
  variant) at column zero and not preceded by ``export``.

Anything indented is assumed to be inside another function, class, or
block and is out of scope. Repos running ratchets are assumed to be
prettier/eslint-shaped; if they aren't, the noise floor is the user's
problem to fix before adopting the gate.
"""

from __future__ import annotations

import re
from pathlib import Path

NAME = "typescript"
EXTENSIONS: tuple[str, ...] = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs")

_EXPORTED = r"(?P<exp>export\s+(?:default\s+)?)?"
_IDENT = r"[A-Za-z_$][\w$]*"

# function NAME(  /  async function NAME<T>(
_FUNCTION_RE = re.compile(rf"^{_EXPORTED}(?:async\s+)?function\s+(?P<name>{_IDENT})\s*[(<]")

# const|let|var NAME [: TYPE] = (args) => ...    or    = async (args) => ...
# Restricted to column zero so we never match a nested arrow inside a function body.
_ARROW_RE = re.compile(
    rf"^{_EXPORTED}(?:const|let|var)\s+(?P<name>{_IDENT})\b"
    r"[^=\n]*=\s*(?:async\s+)?(?:\([^)\n]*\)|<[^>\n]+>\s*\([^)\n]*\)|"
    rf"{_IDENT})(?:\s*:\s*[^=\n]+)?\s*=>"
)

# const|let|var NAME = function ...
_CONST_FN_RE = re.compile(
    rf"^{_EXPORTED}(?:const|let|var)\s+(?P<name>{_IDENT})\b" r"[^=\n]*=\s*(?:async\s+)?function\b"
)

_PATTERNS = (_FUNCTION_RE, _ARROW_RE, _CONST_FN_RE)


def extract_helpers(source_path: Path) -> list[str]:
    """Return names of unexported top-level functions / arrow consts."""
    try:
        text = source_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    names: list[str] = []
    for line in text.splitlines():
        for pattern in _PATTERNS:
            match = pattern.match(line)
            if match is None:
                continue
            if match.group("exp"):
                break
            names.append(match.group("name"))
            break
    return names
