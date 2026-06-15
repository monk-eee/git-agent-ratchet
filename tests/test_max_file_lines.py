"""Tests for the line-count scanner (Ratchet D's pure logic)."""

from __future__ import annotations

from pathlib import Path

from git_agent_ratchet.ratchets.max_file_lines import (
    DEFAULT_EXCLUDE_DIRS,
    DEFAULT_MAX_LINES,
    OversizedFile,
    count_lines,
    iter_python_files,
    metric_value,
    scan_directory,
)


def _write(path: Path, n_lines: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "\n".join(f"x_{i} = {i}" for i in range(n_lines)) + ("\n" if n_lines else "")
    path.write_text(body, encoding="utf-8")


def test_defaults_are_sensible() -> None:
    assert DEFAULT_MAX_LINES == 350
    assert DEFAULT_EXCLUDE_DIRS == ("tests", "test")


def test_count_lines_handles_empty_file(tmp_path: Path) -> None:
    p = tmp_path / "empty.py"
    p.write_text("", encoding="utf-8")
    assert count_lines(p) == 0


def test_count_lines_no_trailing_newline(tmp_path: Path) -> None:
    p = tmp_path / "no_eol.py"
    p.write_text("a\nb\nc", encoding="utf-8")
    assert count_lines(p) == 3


def test_count_lines_with_trailing_newline(tmp_path: Path) -> None:
    p = tmp_path / "with_eol.py"
    p.write_text("a\nb\nc\n", encoding="utf-8")
    assert count_lines(p) == 3


def test_count_lines_returns_zero_for_missing_file(tmp_path: Path) -> None:
    assert count_lines(tmp_path / "nope.py") == 0


def test_count_lines_returns_zero_for_binary_file(tmp_path: Path) -> None:
    p = tmp_path / "binary.py"
    p.write_bytes(b"\xff\xfe\x00\x00garbage")
    assert count_lines(p) == 0


def test_iter_python_files_skips_excluded_dirs(tmp_path: Path) -> None:
    pkg = tmp_path / "pkg"
    _write(pkg / "real.py", 3)
    _write(pkg / "tests" / "test_real.py", 3)

    found = {p.name for p in iter_python_files(pkg, exclude_dirs=DEFAULT_EXCLUDE_DIRS)}

    assert "real.py" in found
    assert "test_real.py" not in found


def test_scan_directory_returns_empty_when_root_missing(tmp_path: Path) -> None:
    assert scan_directory(tmp_path / "nope") == []


def test_scan_directory_flags_oversized_files(tmp_path: Path) -> None:
    pkg = tmp_path / "pkg"
    _write(pkg / "small.py", 100)
    _write(pkg / "big.py", 500)
    _write(pkg / "huge.py", 700)

    result = scan_directory(pkg, max_lines=350)

    paths = [f.path for f in result]
    assert "small.py" not in " ".join(paths)
    # Sorted by overage descending: huge (+350) before big (+150).
    assert result[0].path.endswith("huge.py")
    assert result[0].line_count == 700
    assert result[0].overage == 350
    assert result[1].path.endswith("big.py")
    assert result[1].line_count == 500
    assert result[1].overage == 150


def test_scan_directory_excludes_test_dirs_by_default(tmp_path: Path) -> None:
    pkg = tmp_path / "pkg"
    _write(pkg / "src.py", 500)
    _write(pkg / "tests" / "fixture.py", 800)

    result = scan_directory(pkg, max_lines=350)

    assert len(result) == 1
    assert result[0].path.endswith("src.py")


def test_scan_directory_respects_custom_max(tmp_path: Path) -> None:
    pkg = tmp_path / "pkg"
    _write(pkg / "a.py", 60)

    assert scan_directory(pkg, max_lines=100) == []
    result = scan_directory(pkg, max_lines=50)
    assert len(result) == 1
    assert result[0].overage == 10


def test_scan_directory_is_idempotent(tmp_path: Path) -> None:
    pkg = tmp_path / "pkg"
    _write(pkg / "a.py", 400)
    _write(pkg / "b.py", 360)

    first = scan_directory(pkg, max_lines=350)
    second = scan_directory(pkg, max_lines=350)

    assert first == second


def test_metric_value_sums_overage() -> None:
    files = [
        OversizedFile(path="a.py", line_count=400, overage=50),
        OversizedFile(path="b.py", line_count=500, overage=150),
    ]
    assert metric_value(files) == 200


def test_metric_value_is_zero_for_empty_list() -> None:
    assert metric_value([]) == 0


def test_oversized_file_to_dict_shape() -> None:
    f = OversizedFile(path="a.py", line_count=400, overage=50)
    assert f.to_dict() == {"path": "a.py", "line_count": 400, "overage": 50}
