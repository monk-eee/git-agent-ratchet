"""Tests for the C# extractor (Ratchet A)."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from git_agent_ratchet.ratchets.extractors import csharp_ext


def _write(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(source).lstrip(), encoding="utf-8")


def test_module_attributes_are_stable() -> None:
    assert csharp_ext.NAME == "csharp"
    assert csharp_ext.EXTENSIONS == (".cs",)


def test_private_void_method_captured(tmp_path: Path) -> None:
    src = tmp_path / "Worker.cs"
    _write(
        src,
        """
        class Worker
        {
            private void DoWork(int x)
            {
            }
        }
        """,
    )

    assert csharp_ext.extract_helpers(src) == ["DoWork"]


def test_private_static_method_captured(tmp_path: Path) -> None:
    src = tmp_path / "Util.cs"
    _write(
        src,
        """
        static class Util
        {
            private static string FormatThing(int v) => v.ToString();
        }
        """,
    )

    assert csharp_ext.extract_helpers(src) == ["FormatThing"]


def test_private_async_task_method_captured(tmp_path: Path) -> None:
    src = tmp_path / "Loader.cs"
    _write(
        src,
        """
        class Loader
        {
            private async Task<string> LoadAsync(Uri uri)
            {
                return await Task.FromResult("x");
            }
        }
        """,
    )

    assert csharp_ext.extract_helpers(src) == ["LoadAsync"]


def test_private_generic_method_captured(tmp_path: Path) -> None:
    src = tmp_path / "Cache.cs"
    _write(
        src,
        """
        class Cache
        {
            private static T Resolve<T>(string key) where T : class
            {
                return default;
            }
        }
        """,
    )

    assert csharp_ext.extract_helpers(src) == ["Resolve"]


def test_public_methods_excluded(tmp_path: Path) -> None:
    src = tmp_path / "Api.cs"
    _write(
        src,
        """
        class Api
        {
            public void PublicMethod() {}
            internal void InternalMethod() {}
            protected void ProtectedMethod() {}
        }
        """,
    )

    assert csharp_ext.extract_helpers(src) == []


def test_private_field_not_captured(tmp_path: Path) -> None:
    src = tmp_path / "State.cs"
    _write(
        src,
        """
        class State
        {
            private int _count;
            private readonly string _name = "x";
        }
        """,
    )

    assert csharp_ext.extract_helpers(src) == []


def test_private_property_with_expression_body_not_captured(tmp_path: Path) -> None:
    src = tmp_path / "Counter.cs"
    _write(
        src,
        """
        class Counter
        {
            private int Count => _count;
            private string Label { get; set; }
        }
        """,
    )

    assert csharp_ext.extract_helpers(src) == []


def test_constructor_not_captured(tmp_path: Path) -> None:
    src = tmp_path / "Service.cs"
    _write(
        src,
        """
        class Service
        {
            private Service(int x) { }
        }
        """,
    )

    assert csharp_ext.extract_helpers(src) == []


def test_multiple_private_methods_all_captured(tmp_path: Path) -> None:
    src = tmp_path / "Multi.cs"
    _write(
        src,
        """
        class Multi
        {
            private void One() {}
            private void Two() {}
            private static int Three() => 3;
        }
        """,
    )

    assert csharp_ext.extract_helpers(src) == ["One", "Two", "Three"]


def test_missing_file_returns_empty(tmp_path: Path) -> None:
    assert csharp_ext.extract_helpers(tmp_path / "missing.cs") == []


def test_binary_file_returns_empty(tmp_path: Path) -> None:
    src = tmp_path / "binary.cs"
    src.write_bytes(b"\x80\x81\x82\xff\xfe")

    assert csharp_ext.extract_helpers(src) == []


def test_indented_private_method_still_captured(tmp_path: Path) -> None:
    # C# methods are always inside a class (so always indented). Regex must
    # tolerate leading whitespace, unlike the TS extractor which requires
    # column zero to filter out nested helpers.
    src = tmp_path / "Indented.cs"
    _write(
        src,
        """
        namespace App
        {
            class Inner
            {
                private void DeeplyNested() {}
            }
        }
        """,
    )

    assert csharp_ext.extract_helpers(src) == ["DeeplyNested"]
