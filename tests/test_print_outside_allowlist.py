"""Tests for the print-outside-allowlist scanner (Ratchet F)."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from git_agent_ratchet.ratchets.print_outside_allowlist import (
    PrintCall,
    is_allowed,
    metric_value,
    scan_directory,
    scan_file,
)


def _write(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(source).lstrip(), encoding="utf-8")


def test_scan_file_finds_print_call(tmp_path: Path) -> None:
    src = tmp_path / "mod.py"
    _write(src, "def f():\n    print('hi')\n")

    calls = scan_file(src, file_label="mod.py")

    assert len(calls) == 1
    assert calls[0].file == "mod.py"
    assert calls[0].line == 2


def test_scan_file_ignores_print_inside_strings_and_comments(tmp_path: Path) -> None:
    src = tmp_path / "mod.py"
    _write(
        src,
        """
        # this comment mentions print() but does not call it
        x = "the word print appears here"
        \"\"\"docstring: print() mentioned but not called\"\"\"
        """,
    )

    assert scan_file(src) == []


def test_scan_file_counts_multiple_print_calls(tmp_path: Path) -> None:
    src = tmp_path / "mod.py"
    _write(
        src,
        """
        def f():
            print('one')
            print('two')
            print('three')
        """,
    )

    calls = scan_file(src)

    assert len(calls) == 3


def test_scan_file_returns_empty_on_syntax_error(tmp_path: Path) -> None:
    src = tmp_path / "broken.py"
    src.write_text("def oops(:\n", encoding="utf-8")

    assert scan_file(src) == []


def test_scan_file_returns_empty_on_missing_file(tmp_path: Path) -> None:
    assert scan_file(tmp_path / "absent.py") == []


def test_scan_file_returns_empty_on_binary_file(tmp_path: Path) -> None:
    src = tmp_path / "bin.py"
    src.write_bytes(b"\xff\xfe\x00\x00")

    assert scan_file(src) == []


def test_is_allowed_matches_directory_prefix() -> None:
    assert is_allowed("pkg/hooks/x.py", ["pkg/hooks"]) is True
    assert is_allowed("pkg/hooks/sub/y.py", ["pkg/hooks"]) is True
    assert is_allowed("pkg/other.py", ["pkg/hooks"]) is False


def test_is_allowed_matches_exact_file() -> None:
    assert is_allowed("pkg/cli.py", ["pkg/cli.py"]) is True
    assert is_allowed("pkg/cli_helper.py", ["pkg/cli.py"]) is False


def test_is_allowed_ignores_empty_prefix() -> None:
    assert is_allowed("pkg/x.py", [""]) is False


def test_is_allowed_normalises_windows_paths() -> None:
    assert is_allowed("pkg\\hooks\\x.py", ["pkg/hooks"]) is True


def test_scan_directory_honours_allow_prefix(tmp_path: Path) -> None:
    pkg = tmp_path / "pkg"
    _write(pkg / "hooks" / "h.py", "print('hook output')\n")
    _write(pkg / "core" / "c.py", "print('bad')\n")

    calls = scan_directory(pkg, allow_prefixes=["pkg/hooks"])

    assert len(calls) == 1
    assert "core/c.py" in calls[0].file


def test_scan_directory_excludes_tests_by_default(tmp_path: Path) -> None:
    pkg = tmp_path / "pkg"
    _write(pkg / "a.py", "print('prod')\n")
    _write(pkg / "tests" / "t.py", "print('test')\n")

    calls = scan_directory(pkg)

    assert len(calls) == 1
    assert calls[0].file.endswith("a.py")


def test_scan_directory_returns_empty_when_root_missing(tmp_path: Path) -> None:
    assert scan_directory(tmp_path / "nope") == []


def test_scan_directory_is_idempotent(tmp_path: Path) -> None:
    pkg = tmp_path / "pkg"
    _write(pkg / "a.py", "print('x')\n")

    assert scan_directory(pkg) == scan_directory(pkg)


def test_metric_value_counts_each_call() -> None:
    items = [
        PrintCall(file="a.py", line=1, col=0),
        PrintCall(file="a.py", line=2, col=4),
    ]
    assert metric_value(items) == 2


def test_metric_value_is_zero_for_empty_list() -> None:
    assert metric_value([]) == 0


def test_print_call_to_dict_shape() -> None:
    c = PrintCall(file="a.py", line=7, col=4)
    assert c.to_dict() == {"file": "a.py", "line": 7, "col": 4}
