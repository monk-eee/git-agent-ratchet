"""Tests for the Ratchet A hook entry point (no-duplicate-helpers)."""

from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent

from git_agent_ratchet.hooks.no_duplicate_helpers import main


def _write_py(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(source).lstrip(), encoding="utf-8")


def test_first_run_seeds_baseline_and_passes(tmp_path: Path, capsys) -> None:
    pkg = tmp_path / "pkg"
    _write_py(pkg / "a.py", "def _shared():\n    pass\n")
    _write_py(pkg / "b.py", "def _shared():\n    pass\n")
    baseline = tmp_path / "duplicates.json"

    exit_code = main(["--baseline", str(baseline), "--dir", str(pkg)])

    assert exit_code == 0
    assert baseline.exists()
    data = json.loads(baseline.read_text(encoding="utf-8"))
    assert data["baselines"]["duplicate_helpers"]["metric_value"] == 2

    out = capsys.readouterr().out
    assert "seeded baseline" in out


def test_subsequent_run_with_growth_fails(tmp_path: Path, capsys) -> None:
    pkg = tmp_path / "pkg"
    _write_py(pkg / "a.py", "def _shared():\n    pass\n")
    _write_py(pkg / "b.py", "def _shared():\n    pass\n")
    baseline = tmp_path / "duplicates.json"

    main(["--baseline", str(baseline), "--dir", str(pkg)])  # seed at 2

    _write_py(pkg / "c.py", "def _shared():\n    pass\n")
    exit_code = main(["--baseline", str(baseline), "--dir", str(pkg)])

    assert exit_code == 1
    err = capsys.readouterr().err
    assert "GATE TRIPPED" in err
    assert "+1" in err


def test_subsequent_run_with_shrinkage_ratchets_baseline_down(tmp_path: Path, capsys) -> None:
    pkg = tmp_path / "pkg"
    _write_py(pkg / "a.py", "def _shared():\n    pass\n")
    _write_py(pkg / "b.py", "def _shared():\n    pass\n")
    _write_py(pkg / "c.py", "def _shared():\n    pass\n")
    baseline = tmp_path / "duplicates.json"

    main(["--baseline", str(baseline), "--dir", str(pkg)])  # seed at 3

    (pkg / "c.py").unlink()
    exit_code = main(["--baseline", str(baseline), "--dir", str(pkg)])

    assert exit_code == 0
    data = json.loads(baseline.read_text(encoding="utf-8"))
    assert data["baselines"]["duplicate_helpers"]["metric_value"] == 2

    out = capsys.readouterr().out
    assert "ratcheted down" in out


def test_steady_state_passes_silently_into_stdout(tmp_path: Path, capsys) -> None:
    pkg = tmp_path / "pkg"
    _write_py(pkg / "a.py", "def _shared():\n    pass\n")
    _write_py(pkg / "b.py", "def _shared():\n    pass\n")
    baseline = tmp_path / "duplicates.json"

    main(["--baseline", str(baseline), "--dir", str(pkg)])  # seed
    capsys.readouterr()  # discard seed output

    exit_code = main(["--baseline", str(baseline), "--dir", str(pkg)])

    assert exit_code == 0
    out = capsys.readouterr()
    assert out.out == ""
    assert out.err == ""


def test_clean_directory_seeds_zero_baseline(tmp_path: Path) -> None:
    pkg = tmp_path / "pkg"
    _write_py(pkg / "a.py", "def public():\n    pass\n")
    baseline = tmp_path / "duplicates.json"

    exit_code = main(["--baseline", str(baseline), "--dir", str(pkg)])

    assert exit_code == 0
    data = json.loads(baseline.read_text(encoding="utf-8"))
    assert data["baselines"]["duplicate_helpers"]["metric_value"] == 0


def test_filenames_positional_args_are_ignored(tmp_path: Path) -> None:
    pkg = tmp_path / "pkg"
    _write_py(pkg / "a.py", "def _shared():\n    pass\n")
    _write_py(pkg / "b.py", "def _shared():\n    pass\n")
    baseline = tmp_path / "duplicates.json"

    # pre-commit passes filenames positionally; the hook must ignore them and scan --dir.
    exit_code = main(
        [
            "--baseline",
            str(baseline),
            "--dir",
            str(pkg),
            "anything.py",
            "ignored.py",
        ]
    )

    assert exit_code == 0
