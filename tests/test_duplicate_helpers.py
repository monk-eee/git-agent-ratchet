"""Tests for the scanner core of Ratchet A (language-agnostic dispatch)."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from git_agent_ratchet.ratchets.duplicate_helpers import (
    DEFAULT_EXCLUDE_DIRS,
    DuplicateHelper,
    iter_source_files,
    metric_value,
    scan_directory,
)


def _write(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(source).lstrip(), encoding="utf-8")


def test_iter_source_files_filters_by_extension(tmp_path: Path) -> None:
    _write(tmp_path / "src" / "a.py", "x = 1\n")
    _write(tmp_path / "src" / "b.ts", "const x = 1\n")
    _write(tmp_path / "src" / "c.md", "# notes\n")

    files = sorted(p.name for p in iter_source_files(tmp_path, [".py"]))

    assert files == ["a.py"]


def test_iter_source_files_skips_excluded_dirs(tmp_path: Path) -> None:
    _write(tmp_path / "src" / "a.py", "x = 1\n")
    _write(tmp_path / "tests" / "test_a.py", "x = 1\n")
    _write(tmp_path / "test" / "more.py", "x = 1\n")
    _write(tmp_path / "node_modules" / "pkg" / "index.py", "x = 1\n")
    _write(tmp_path / "src" / "sub" / "b.py", "x = 1\n")

    files = sorted(p.name for p in iter_source_files(tmp_path, [".py"], DEFAULT_EXCLUDE_DIRS))

    assert files == ["a.py", "b.py"]


def test_iter_source_files_extension_match_is_case_insensitive(tmp_path: Path) -> None:
    _write(tmp_path / "Module.PY", "x = 1\n")

    files = sorted(p.name for p in iter_source_files(tmp_path, [".py"]))

    assert files == ["Module.PY"]


def test_scan_directory_flags_duplicate_private_helpers(tmp_path: Path) -> None:
    pkg = tmp_path / "pkg"
    _write(pkg / "a.py", "def _shared():\n    pass\n")
    _write(pkg / "b.py", "def _shared():\n    pass\n")
    _write(pkg / "c.py", "def unique():\n    pass\n")

    duplicates = scan_directory(pkg)

    assert len(duplicates) == 1
    assert duplicates[0].name == "_shared"
    assert len(duplicates[0].occurrences) == 2
    assert metric_value(duplicates) == 2


def test_scan_directory_ignores_test_dirs(tmp_path: Path) -> None:
    pkg = tmp_path / "pkg"
    _write(pkg / "src" / "a.py", "def _shared():\n    pass\n")
    _write(pkg / "tests" / "b.py", "def _shared():\n    pass\n")

    duplicates = scan_directory(pkg)

    assert duplicates == []


def test_scan_directory_ignores_non_private_functions(tmp_path: Path) -> None:
    pkg = tmp_path / "pkg"
    _write(pkg / "a.py", "def public():\n    pass\n")
    _write(pkg / "b.py", "def public():\n    pass\n")

    assert scan_directory(pkg) == []


def test_scan_directory_returns_empty_when_root_missing(tmp_path: Path) -> None:
    assert scan_directory(tmp_path / "nope") == []


def test_scan_directory_groups_three_files(tmp_path: Path) -> None:
    pkg = tmp_path / "pkg"
    _write(pkg / "a.py", "def _x():\n    pass\n")
    _write(pkg / "b.py", "def _x():\n    pass\n")
    _write(pkg / "c.py", "def _x():\n    pass\n")

    duplicates = scan_directory(pkg)

    assert metric_value(duplicates) == 3
    assert duplicates[0].name == "_x"


def test_scan_directory_is_idempotent(tmp_path: Path) -> None:
    pkg = tmp_path / "pkg"
    _write(pkg / "a.py", "def _x():\n    pass\n")
    _write(pkg / "b.py", "def _x():\n    pass\n")

    first = scan_directory(pkg)
    second = scan_directory(pkg)

    assert first == second


def test_scan_directory_spans_languages_when_unrestricted(tmp_path: Path) -> None:
    pkg = tmp_path / "pkg"
    _write(pkg / "a.py", "def _shared():\n    pass\n")
    _write(pkg / "b.ts", "function _shared() { return 1; }\n")

    duplicates = scan_directory(pkg)

    assert len(duplicates) == 1
    assert duplicates[0].name == "_shared"
    assert len(duplicates[0].occurrences) == 2


def test_scan_directory_respects_language_filter(tmp_path: Path) -> None:
    pkg = tmp_path / "pkg"
    _write(pkg / "a.py", "def _shared():\n    pass\n")
    _write(pkg / "b.ts", "function _shared() { return 1; }\n")

    duplicates = scan_directory(pkg, languages=["python"])

    assert duplicates == []


def test_scan_directory_unknown_language_silently_drops(tmp_path: Path) -> None:
    pkg = tmp_path / "pkg"
    _write(pkg / "a.py", "def _shared():\n    pass\n")
    _write(pkg / "b.py", "def _shared():\n    pass\n")

    duplicates = scan_directory(pkg, languages=["fortran"])

    assert duplicates == []


def test_duplicate_helper_to_dict_shape() -> None:
    d = DuplicateHelper(name="_foo", occurrences=("a.py", "b.py"))
    assert d.to_dict() == {"name": "_foo", "occurrences": ["a.py", "b.py"]}
