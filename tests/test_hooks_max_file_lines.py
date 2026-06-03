"""Tests for the Ratchet D hook entry point (max-file-lines)."""

from __future__ import annotations

import json
from pathlib import Path

from git_agent_ratchet.hooks.max_file_lines import _emit_oversized, main
from git_agent_ratchet.ratchets.max_file_lines import OversizedFile


def _write(path: Path, n_lines: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "\n".join(f"x_{i} = {i}" for i in range(n_lines)) + ("\n" if n_lines else "")
    path.write_text(body, encoding="utf-8")


def test_first_run_seeds_baseline_and_passes(tmp_path: Path, capsys) -> None:
    pkg = tmp_path / "pkg"
    _write(pkg / "a.py", 500)
    _write(pkg / "b.py", 200)
    baseline = tmp_path / "file_lines.json"

    exit_code = main(["--baseline", str(baseline), "--dir", str(pkg), "--max", "350"])

    assert exit_code == 0
    data = json.loads(baseline.read_text(encoding="utf-8"))
    entry = data["baselines"]["max_file_lines"]
    assert entry["metric_value"] == 150
    assert len(entry["items"]) == 1
    assert entry["items"][0]["path"].endswith("a.py")
    assert "seeded baseline" in capsys.readouterr().out


def test_subsequent_run_with_growth_fails(tmp_path: Path, capsys) -> None:
    pkg = tmp_path / "pkg"
    _write(pkg / "a.py", 400)
    baseline = tmp_path / "file_lines.json"

    assert main(["--baseline", str(baseline), "--dir", str(pkg), "--max", "350"]) == 0

    # Grow a.py past its baseline.
    _write(pkg / "a.py", 500)

    exit_code = main(["--baseline", str(baseline), "--dir", str(pkg), "--max", "350"])

    assert exit_code == 1
    err = capsys.readouterr().err
    assert "GATE TRIPPED" in err
    assert "a.py" in err
    assert "+100" in err


def test_subsequent_run_with_shrinkage_ratchets_baseline_down(tmp_path: Path, capsys) -> None:
    pkg = tmp_path / "pkg"
    _write(pkg / "a.py", 500)
    baseline = tmp_path / "file_lines.json"

    assert main(["--baseline", str(baseline), "--dir", str(pkg), "--max", "350"]) == 0
    capsys.readouterr()

    # Trim the file below its old size (still oversized but smaller).
    _write(pkg / "a.py", 400)

    exit_code = main(["--baseline", str(baseline), "--dir", str(pkg), "--max", "350"])

    assert exit_code == 0
    data = json.loads(baseline.read_text(encoding="utf-8"))
    assert data["baselines"]["max_file_lines"]["metric_value"] == 50
    assert "ratcheted down" in capsys.readouterr().out


def test_steady_state_passes_silently(tmp_path: Path, capsys) -> None:
    pkg = tmp_path / "pkg"
    _write(pkg / "a.py", 400)
    baseline = tmp_path / "file_lines.json"

    main(["--baseline", str(baseline), "--dir", str(pkg), "--max", "350"])
    capsys.readouterr()

    exit_code = main(["--baseline", str(baseline), "--dir", str(pkg), "--max", "350"])

    assert exit_code == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_clean_directory_seeds_zero_baseline(tmp_path: Path) -> None:
    pkg = tmp_path / "pkg"
    _write(pkg / "small.py", 100)
    baseline = tmp_path / "file_lines.json"

    exit_code = main(["--baseline", str(baseline), "--dir", str(pkg), "--max", "350"])

    assert exit_code == 0
    data = json.loads(baseline.read_text(encoding="utf-8"))
    assert data["baselines"]["max_file_lines"]["metric_value"] == 0
    assert data["baselines"]["max_file_lines"]["items"] == []


def test_filenames_positional_args_are_ignored(tmp_path: Path) -> None:
    pkg = tmp_path / "pkg"
    _write(pkg / "a.py", 100)
    baseline = tmp_path / "file_lines.json"

    # pre-commit passes filenames positionally; the hook must ignore them and scan --dir.
    exit_code = main(
        [
            "--baseline",
            str(baseline),
            "--dir",
            str(pkg),
            "--max",
            "350",
            "anything.py",
            "ignored.py",
        ]
    )

    assert exit_code == 0


def test_emit_oversized_renders_none_when_empty() -> None:
    assert _emit_oversized([], 350) == "  (none)"


def test_emit_oversized_renders_one_line_per_file() -> None:
    files = [OversizedFile(path="big.py", line_count=400, overage=50)]
    out = _emit_oversized(files, 350)
    assert "big.py" in out
    assert "400" in out
    assert "+50" in out


def test_exclude_flag_overrides_default(tmp_path: Path) -> None:
    pkg = tmp_path / "pkg"
    _write(pkg / "tests" / "fixture.py", 500)
    _write(pkg / "vendor" / "blob.py", 500)
    baseline = tmp_path / "file_lines.json"

    # Override the default tests/test exclude with vendor only; tests now scans.
    exit_code = main(
        [
            "--baseline",
            str(baseline),
            "--dir",
            str(pkg),
            "--max",
            "350",
            "--exclude",
            "vendor",
        ]
    )

    assert exit_code == 0
    data = json.loads(baseline.read_text(encoding="utf-8"))
    items = data["baselines"]["max_file_lines"]["items"]
    paths = " ".join(i["path"] for i in items)
    assert "tests/fixture.py" in paths
    assert "vendor" not in paths
