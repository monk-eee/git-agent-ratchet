"""Language extractor registry for Ratchet A.

Each extractor is a small module exposing three public attributes:

- ``NAME``: short string id (``python``, ``typescript``, ``csharp``).
- ``EXTENSIONS``: tuple of lowercase file suffixes (with leading dot) the
  extractor knows how to read.
- ``extract_helpers(path) -> list[str]``: returns the names of
  "helper-shaped" declarations whose duplication across files is the
  failure mode the ratchet is meant to catch. The exact definition of
  "helper-shaped" is language-specific (Python: leading underscore on a
  top-level def; TS/JS: unexported top-level function or arrow const;
  C#: ``private`` method) and lives inside each extractor.

Each extractor module is treated as a structural type with those three
attributes; that is the public contract callers should rely on.
"""

from __future__ import annotations

from collections.abc import Iterable
from types import ModuleType

from . import csharp_ext, python_ext, typescript_ext

EXTRACTORS: tuple[ModuleType, ...] = (python_ext, typescript_ext, csharp_ext)


def select(languages: Iterable[str] | None) -> tuple[ModuleType, ...]:
    """Return the registered extractors filtered by language ``NAME``.

    ``None`` means "all". Unknown names are silently dropped so a hook
    invocation with a typo fails closed (zero extractors -> zero scans
    -> empty duplicate list -> the gate either seeds or holds steady,
    and the user notices because nothing is being checked).
    """
    if languages is None:
        return EXTRACTORS
    wanted = {name.lower() for name in languages}
    return tuple(e for e in EXTRACTORS if e.NAME in wanted)
