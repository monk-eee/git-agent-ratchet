"""Tests for the Python language extractor (Ratchet A)."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from git_agent_ratchet.ratchets.extractors import python_ext


def _write(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(source).lstrip(), encoding="utf-8")


def test_is_private_helper_classifies_correctly() -> None:
    assert python_ext.is_private_helper("_foo") is True
    assert python_ext.is_private_helper("_run_command") is True
    assert python_ext.is_private_helper("foo") is False
    assert python_ext.is_private_helper("__init__") is False
    assert python_ext.is_private_helper("__dunder__") is False


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

    assert python_ext.collect_top_level_functions(src) == ["_top_one", "_top_two"]


def test_collect_top_level_functions_handles_syntax_error(tmp_path: Path) -> None:
    src = tmp_path / "broken.py"
    src.write_text("def _bad(:\n    pass\n", encoding="utf-8")

    assert python_ext.collect_top_level_functions(src) == []


def test_collect_top_level_functions_handles_missing_file(tmp_path: Path) -> None:
    assert python_ext.collect_top_level_functions(tmp_path / "does_not_exist.py") == []


def test_collect_top_level_functions_handles_binary_file(tmp_path: Path) -> None:
    src = tmp_path / "binary.py"
    src.write_bytes(b"\x80\x81\x82\xff\xfe")

    assert python_ext.collect_top_level_functions(src) == []


def test_extract_helpers_returns_only_private_top_levels(tmp_path: Path) -> None:
    src = tmp_path / "mod.py"
    _write(
        src,
        """
        def public():
            pass

        def _private():
            pass

        async def _async_private():
            pass

        def __dunder__():
            pass
        """,
    )

    assert python_ext.extract_helpers(src) == ["_private", "_async_private"]


def test_extract_helpers_empty_when_no_helpers(tmp_path: Path) -> None:
    src = tmp_path / "mod.py"
    _write(src, "x = 1\n")

    assert python_ext.extract_helpers(src) == []


def test_module_attributes_are_stable() -> None:
    assert python_ext.NAME == "python"
    assert python_ext.EXTENSIONS == (".py",)
