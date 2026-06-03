"""Tests for the TypeScript / JavaScript extractor (Ratchet A)."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from git_agent_ratchet.ratchets.extractors import typescript_ext


def _write(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(source).lstrip(), encoding="utf-8")


def test_module_attributes_are_stable() -> None:
    assert typescript_ext.NAME == "typescript"
    assert ".ts" in typescript_ext.EXTENSIONS
    assert ".tsx" in typescript_ext.EXTENSIONS
    assert ".js" in typescript_ext.EXTENSIONS
    assert ".jsx" in typescript_ext.EXTENSIONS
    assert ".mjs" in typescript_ext.EXTENSIONS
    assert ".cjs" in typescript_ext.EXTENSIONS


def test_function_declaration_captured(tmp_path: Path) -> None:
    src = tmp_path / "mod.ts"
    _write(
        src,
        """
        function safeExec(cmd: string) {
            return cmd;
        }
        """,
    )

    assert typescript_ext.extract_helpers(src) == ["safeExec"]


def test_async_function_declaration_captured(tmp_path: Path) -> None:
    src = tmp_path / "mod.ts"
    _write(
        src,
        """
        async function loadConfig() {
            return {};
        }
        """,
    )

    assert typescript_ext.extract_helpers(src) == ["loadConfig"]


def test_generic_function_declaration_captured(tmp_path: Path) -> None:
    src = tmp_path / "mod.ts"
    _write(
        src,
        """
        function identity<T>(value: T): T {
            return value;
        }
        """,
    )

    assert typescript_ext.extract_helpers(src) == ["identity"]


def test_exported_function_excluded(tmp_path: Path) -> None:
    src = tmp_path / "mod.ts"
    _write(
        src,
        """
        export function publicFn() {
            return 1;
        }

        export default function defaultFn() {
            return 2;
        }
        """,
    )

    assert typescript_ext.extract_helpers(src) == []


def test_arrow_const_captured(tmp_path: Path) -> None:
    src = tmp_path / "mod.ts"
    _write(
        src,
        """
        const formatDate = (d: Date): string => d.toISOString();
        const noArgs = () => 42;
        const async_one = async () => await Promise.resolve(1);
        """,
    )

    assert typescript_ext.extract_helpers(src) == ["formatDate", "noArgs", "async_one"]


def test_exported_arrow_const_excluded(tmp_path: Path) -> None:
    src = tmp_path / "mod.ts"
    _write(
        src,
        """
        export const publicArrow = () => 1;
        """,
    )

    assert typescript_ext.extract_helpers(src) == []


def test_const_function_expression_captured(tmp_path: Path) -> None:
    src = tmp_path / "mod.ts"
    _write(
        src,
        """
        const helper = function (x: number) {
            return x + 1;
        };
        const asyncHelper = async function () {
            return 1;
        };
        """,
    )

    assert typescript_ext.extract_helpers(src) == ["helper", "asyncHelper"]


def test_nested_arrow_inside_function_ignored(tmp_path: Path) -> None:
    src = tmp_path / "mod.ts"
    _write(
        src,
        """
        function outer() {
            const inner = (x: number) => x + 1;
            return inner(1);
        }
        """,
    )

    assert typescript_ext.extract_helpers(src) == ["outer"]


def test_plain_const_value_not_captured(tmp_path: Path) -> None:
    src = tmp_path / "mod.ts"
    _write(
        src,
        """
        const COUNT = 42;
        const NAMES = ["a", "b"];
        const config: Config = { x: 1 };
        """,
    )

    assert typescript_ext.extract_helpers(src) == []


def test_missing_file_returns_empty(tmp_path: Path) -> None:
    assert typescript_ext.extract_helpers(tmp_path / "missing.ts") == []


def test_binary_file_returns_empty(tmp_path: Path) -> None:
    src = tmp_path / "binary.ts"
    src.write_bytes(b"\x80\x81\x82\xff\xfe")

    assert typescript_ext.extract_helpers(src) == []


def test_jsx_file_recognised(tmp_path: Path) -> None:
    src = tmp_path / "component.jsx"
    _write(
        src,
        """
        function helper() {
            return 1;
        }
        """,
    )

    assert typescript_ext.extract_helpers(src) == ["helper"]
