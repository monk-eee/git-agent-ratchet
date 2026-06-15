"""Tests for the Ratchet G hook entry point (no-temporary-comments)."""

from __future__ import annotations

import json
from pathlib import Path

from git_agent_ratchet.hooks.no_temporary_comments import _emit_matches, main


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_first_run_seeds_baseline_and_passes(tmp_path: Path, capsys) -> None:
    pkg = tmp_path / "pkg"
    _write(pkg / "a.py", "# for now this works\n")
    baseline = tmp_path / "b.json"

    exit_code = main(["--baseline", str(baseline), "--dir", str(pkg)])

    assert exit_code == 0
    data = json.loads(baseline.read_text(encoding="utf-8"))
    assert data["baselines"]["temporary_comments"]["metric_value"] == 1
    assert "seeded baseline" in capsys.readouterr().out


def test_growth_fails(tmp_path: Path, capsys) -> None:
    pkg = tmp_path / "pkg"
    _write(pkg / "a.py", "# for now\n")
    baseline = tmp_path / "b.json"
    main(["--baseline", str(baseline), "--dir", str(pkg)])

    _write(pkg / "b.py", "# back-compat shim\n")
    exit_code = main(["--baseline", str(baseline), "--dir", str(pkg)])

    assert exit_code == 1
    err = capsys.readouterr().err
    assert "GATE TRIPPED" in err
    assert "temporary-comment markers" in err


def test_shrinkage_ratchets_down(tmp_path: Path) -> None:
    pkg = tmp_path / "pkg"
    _write(pkg / "a.py", "# for now\n# back-compat\n")
    baseline = tmp_path / "b.json"
    main(["--baseline", str(baseline), "--dir", str(pkg)])

    _write(pkg / "a.py", "# for now\n")
    exit_code = main(["--baseline", str(baseline), "--dir", str(pkg)])

    assert exit_code == 0
    data = json.loads(baseline.read_text(encoding="utf-8"))
    assert data["baselines"]["temporary_comments"]["metric_value"] == 1


def test_allow_marker_is_respected(tmp_path: Path) -> None:
    pkg = tmp_path / "pkg"
    _write(pkg / "a.py", "# for now  # ratchet-allow: temporary_comments\n")
    baseline = tmp_path / "b.json"

    exit_code = main(["--baseline", str(baseline), "--dir", str(pkg)])
    assert exit_code == 0
    data = json.loads(baseline.read_text(encoding="utf-8"))
    assert data["baselines"]["temporary_comments"]["metric_value"] == 0


def test_steady_state_passes_silently(tmp_path: Path, capsys) -> None:
    pkg = tmp_path / "pkg"
    _write(pkg / "a.py", "# for now\n")
    baseline = tmp_path / "b.json"
    main(["--baseline", str(baseline), "--dir", str(pkg)])
    capsys.readouterr()

    exit_code = main(["--baseline", str(baseline), "--dir", str(pkg)])
    assert exit_code == 0
    out = capsys.readouterr()
    assert out.out == ""
    assert out.err == ""


def test_filenames_positional_args_are_ignored(tmp_path: Path) -> None:
    pkg = tmp_path / "pkg"
    _write(pkg / "a.py", "# for now\n")
    baseline = tmp_path / "b.json"

    exit_code = main(["--baseline", str(baseline), "--dir", str(pkg), "x.py"])
    assert exit_code == 0


def test_emit_matches_renders_none_when_empty() -> None:
    assert _emit_matches([]) == "  (none)"
