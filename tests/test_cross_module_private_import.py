"""Tests for the cross-module-private-import scanner (Ratchet E)."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from git_agent_ratchet.ratchets.cross_module_private_import import (
    PrivateImport,
    is_private_name,
    metric_value,
    scan_directory,
    scan_file,
)


def _write(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(source).lstrip(), encoding="utf-8")


def test_is_private_name_basic_cases() -> None:
    assert is_private_name("_foo") is True
    assert is_private_name("_run_safe") is True
    assert is_private_name("foo") is False
    assert is_private_name("__init__") is False
    assert is_private_name("__repr__") is False
    assert is_private_name("") is False


def test_scan_file_flags_from_import_of_private_name(tmp_path: Path) -> None:
    src = tmp_path / "consumer.py"
    _write(src, "from pkg.helpers import _internal_thing\n")

    found = scan_file(src, file_label="consumer.py")

    assert len(found) == 1
    assert found[0].name == "_internal_thing"
    assert found[0].source_module == "pkg.helpers"
    assert found[0].file == "consumer.py"
    assert found[0].line == 1


def test_scan_file_ignores_relative_imports(tmp_path: Path) -> None:
    src = tmp_path / "consumer.py"
    _write(src, "from . import _sibling_helper\nfrom ..pkg import _other\n")

    assert scan_file(src) == []


def test_scan_file_ignores_dunder_imports(tmp_path: Path) -> None:
    src = tmp_path / "consumer.py"
    _write(src, "from pkg import __version__\n")

    assert scan_file(src) == []


def test_scan_file_ignores_public_imports(tmp_path: Path) -> None:
    src = tmp_path / "consumer.py"
    _write(src, "from pkg.helpers import do_thing, AnotherThing\n")

    assert scan_file(src) == []


def test_scan_file_flags_import_of_private_submodule(tmp_path: Path) -> None:
    src = tmp_path / "consumer.py"
    _write(src, "import pkg._private\n")

    found = scan_file(src)

    assert len(found) == 1
    assert found[0].name == "_private"


def test_scan_file_handles_multiple_aliases_on_one_line(tmp_path: Path) -> None:
    src = tmp_path / "consumer.py"
    _write(src, "from pkg.helpers import public_thing, _bad_one, _also_bad\n")

    found = scan_file(src)

    assert sorted(v.name for v in found) == ["_also_bad", "_bad_one"]
    assert all(v.line == 1 for v in found)


def test_scan_file_returns_empty_on_syntax_error(tmp_path: Path) -> None:
    src = tmp_path / "broken.py"
    src.write_text("def oops(:\n", encoding="utf-8")

    assert scan_file(src) == []


def test_scan_file_returns_empty_on_missing_file(tmp_path: Path) -> None:
    assert scan_file(tmp_path / "absent.py") == []


def test_scan_file_returns_empty_on_binary_file(tmp_path: Path) -> None:
    src = tmp_path / "bin.py"
    src.write_bytes(b"\xff\xfe\x00\x00garbage")

    assert scan_file(src) == []


def test_scan_directory_excludes_tests_by_default(tmp_path: Path) -> None:
    pkg = tmp_path / "pkg"
    _write(pkg / "a.py", "from pkg.helpers import _internal\n")
    _write(pkg / "tests" / "test_a.py", "from pkg.helpers import _internal\n")

    found = scan_directory(pkg)

    assert len(found) == 1
    assert found[0].file.endswith("a.py")


def test_scan_directory_returns_empty_when_root_missing(tmp_path: Path) -> None:
    assert scan_directory(tmp_path / "nope") == []


def test_scan_directory_is_idempotent(tmp_path: Path) -> None:
    pkg = tmp_path / "pkg"
    _write(pkg / "a.py", "from pkg.helpers import _x\n")
    _write(pkg / "b.py", "from pkg.helpers import _y\n")

    first = scan_directory(pkg)
    second = scan_directory(pkg)

    assert first == second


def test_metric_value_counts_each_violation() -> None:
    items = [
        PrivateImport(file="a.py", line=1, name="_x", source_module="m"),
        PrivateImport(file="b.py", line=2, name="_y", source_module="m"),
    ]
    assert metric_value(items) == 2


def test_metric_value_is_zero_for_empty_list() -> None:
    assert metric_value([]) == 0


def test_private_import_to_dict_shape() -> None:
    v = PrivateImport(file="a.py", line=3, name="_x", source_module="pkg.h")
    assert v.to_dict() == {
        "file": "a.py",
        "line": 3,
        "name": "_x",
        "source_module": "pkg.h",
    }
