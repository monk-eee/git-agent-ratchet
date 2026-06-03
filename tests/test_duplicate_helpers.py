"""Tests for the AST-based duplicate-helper scanner (Ratchet A's pure logic)."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from git_agent_ratchet.ratchets.duplicate_helpers import (
    DEFAULT_EXCLUDE_DIRS,
    DuplicateHelper,
    collect_top_level_functions,
    is_private_helper,
    iter_python_files,
    metric_value,
    scan_directory,
)


def _write(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(source).lstrip(), encoding="utf-8")


def test_is_private_helper_classifies_correctly() -> None:
    assert is_private_helper("_foo") is True
    assert is_private_helper("_run_command") is True
    assert is_private_helper("foo") is False
    assert is_private_helper("__init__") is False
    assert is_private_helper("__dunder__") is False


def test_collect_top_level_functions_returns_only_top_level(tmp_path: Path) -> None:
    src = tmp_path / "mod.py"
    _write(
        src,
        """
        def _top_one():
            def _inner():
                pass

        async def _top_two():
            pass

        class C:
            def _method(self):
                pass
        """,
    )

    names = collect_top_level_functions(src)

    assert names == ["_top_one", "_top_two"]


def test_collect_top_level_functions_handles_syntax_error(tmp_path: Path) -> None:
    src = tmp_path / "broken.py"
    src.write_text("def _bad(:\n    pass\n", encoding="utf-8")

    assert collect_top_level_functions(src) == []


def test_collect_top_level_functions_handles_missing_file(tmp_path: Path) -> None:
    assert collect_top_level_functions(tmp_path / "does_not_exist.py") == []


def test_iter_python_files_skips_excluded_dirs(tmp_path: Path) -> None:
    _write(tmp_path / "src" / "a.py", "x = 1\n")
    _write(tmp_path / "tests" / "test_a.py", "x = 1\n")
    _write(tmp_path / "test" / "more.py", "x = 1\n")
    _write(tmp_path / "src" / "sub" / "b.py", "x = 1\n")

    files = sorted(p.name for p in iter_python_files(tmp_path, DEFAULT_EXCLUDE_DIRS))

    assert files == ["a.py", "b.py"]


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


def test_duplicate_helper_to_dict_shape() -> None:
    d = DuplicateHelper(name="_foo", occurrences=("a.py", "b.py"))
    assert d.to_dict() == {"name": "_foo", "occurrences": ["a.py", "b.py"]}
