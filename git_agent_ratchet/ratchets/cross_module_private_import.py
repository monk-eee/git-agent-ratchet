"""Ratchet E: detect cross-module imports of underscore-prefixed names.

A leading underscore is the Python convention for "this name is private to
its defining module". Importing such a name from another module breaks the
contract -- the owner can no longer rename or remove it without searching
for absolute-import consumers. This ratchet flags every such import so the
count can shrink (or stay flat) but never grow.

Only absolute imports are flagged. Relative imports (``from . import _foo``)
stay inside the package and are considered the author's prerogative.
"""

from __future__ import annotations

import ast
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from git_agent_ratchet.paths import iter_python_files, relative_posix

RATCHET_NAME = "cross_module_private_imports"
DEFAULT_EXCLUDE_DIRS = ("tests", "test")


@dataclass(frozen=True)
class PrivateImport:
    """A single cross-module import of a private name."""

    file: str
    line: int
    name: str
    source_module: str

    def to_dict(self) -> dict[str, object]:
        return {
            "file": self.file,
            "line": self.line,
            "name": self.name,
            "source_module": self.source_module,
        }


def is_private_name(name: str) -> bool:
    """Return True for ``_foo`` / ``_bar`` but not for dunders (``__init__``)."""
    if not name.startswith("_"):
        return False
    if name.startswith("__") and name.endswith("__"):
        return False
    return True


def _violations_in_tree(tree: ast.AST, file_label: str) -> list[PrivateImport]:
    found: list[PrivateImport] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            # Relative imports (``from . import _x``) are intra-package and OK.
            if node.level and node.level > 0:
                continue
            module = node.module or ""
            for alias in node.names:
                if is_private_name(alias.name):
                    found.append(
                        PrivateImport(
                            file=file_label,
                            line=node.lineno,
                            name=alias.name,
                            source_module=module,
                        )
                    )
        elif isinstance(node, ast.Import):
            for alias in node.names:
                dotted = alias.name
                # ``import pkg._private`` or ``import pkg.sub._helper`` -- flag
                # if any non-root segment is private. The root package name is
                # almost never underscore-prefixed and isn't the failure mode.
                segments = dotted.split(".")
                for seg in segments[1:]:
                    if is_private_name(seg):
                        found.append(
                            PrivateImport(
                                file=file_label,
                                line=node.lineno,
                                name=seg,
                                source_module=dotted,
                            )
                        )
                        break
    return found


def scan_file(source_path: Path, file_label: str | None = None) -> list[PrivateImport]:
    """Return every private cross-module import in ``source_path``.

    Unreadable files and syntax errors yield an empty list so the scanner
    never crashes on a half-edited buffer.
    """
    label = file_label if file_label is not None else str(source_path)
    try:
        source = source_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    try:
        tree = ast.parse(source, filename=str(source_path))
    except SyntaxError:
        return []
    return _violations_in_tree(tree, label)


def scan_directory(
    root: Path,
    exclude_dirs: Iterable[str] = DEFAULT_EXCLUDE_DIRS,
) -> list[PrivateImport]:
    """Scan ``root`` recursively and return every cross-module private import."""
    if not root.exists():
        return []
    anchor = root.parent if root.parent.exists() else root
    violations: list[PrivateImport] = []
    for py in iter_python_files(root, exclude_dirs):
        violations.extend(scan_file(py, file_label=relative_posix(py, anchor)))
    violations.sort(key=lambda v: (v.file, v.line, v.name))
    return violations


def metric_value(violations: list[PrivateImport]) -> int:
    """Return the total count of cross-module private imports."""
    return len(violations)
