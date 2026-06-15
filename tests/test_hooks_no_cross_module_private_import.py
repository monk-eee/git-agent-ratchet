"""Tests for the Ratchet E hook entry point (no-cross-module-private-import)."""

from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent

from git_agent_ratchet.hooks.no_cross_module_private_import import _emit_violations, main


def _write(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(source).lstrip(), encoding="utf-8")


def test_first_run_seeds_baseline_and_passes(tmp_path: Path, capsys) -> None:
    pkg = tmp_path / "pkg"
    _write(pkg / "a.py", "from pkg.helpers import _internal\n")
    baseline = tmp_path / "private_imports.json"

    exit_code = main(["--baseline", str(baseline), "--dir", str(pkg)])

    assert exit_code == 0
    data = json.loads(baseline.read_text(encoding="utf-8"))
    assert data["baselines"]["cross_module_private_imports"]["metric_value"] == 1
    assert "seeded baseline" in capsys.readouterr().out


def test_subsequent_run_with_growth_fails(tmp_path: Path, capsys) -> None:
    pkg = tmp_path / "pkg"
    _write(pkg / "a.py", "from pkg.helpers import _internal\n")
    baseline = tmp_path / "b.json"

    main(["--baseline", str(baseline), "--dir", str(pkg)])  # seed at 1

    _write(pkg / "b.py", "from pkg.helpers import _another_internal\n")
    exit_code = main(["--baseline", str(baseline), "--dir", str(pkg)])

    assert exit_code == 1
    err = capsys.readouterr().err
    assert "GATE TRIPPED" in err
    assert "+1" in err


def test_subsequent_run_with_shrinkage_ratchets_down(tmp_path: Path, capsys) -> None:
    pkg = tmp_path / "pkg"
    _write(pkg / "a.py", "from pkg.helpers import _x\n")
    _write(pkg / "b.py", "from pkg.helpers import _y\n")
    baseline = tmp_path / "b.json"

    main(["--baseline", str(baseline), "--dir", str(pkg)])  # seed at 2

    (pkg / "b.py").unlink()
    exit_code = main(["--baseline", str(baseline), "--dir", str(pkg)])

    assert exit_code == 0
    data = json.loads(baseline.read_text(encoding="utf-8"))
    assert data["baselines"]["cross_module_private_imports"]["metric_value"] == 1
    assert "ratcheted down" in capsys.readouterr().out


def test_steady_state_passes_silently(tmp_path: Path, capsys) -> None:
    pkg = tmp_path / "pkg"
    _write(pkg / "a.py", "from pkg.helpers import _x\n")
    baseline = tmp_path / "b.json"

    main(["--baseline", str(baseline), "--dir", str(pkg)])
    capsys.readouterr()

    exit_code = main(["--baseline", str(baseline), "--dir", str(pkg)])
    assert exit_code == 0
    out = capsys.readouterr()
    assert out.out == ""
    assert out.err == ""


def test_clean_tree_seeds_zero(tmp_path: Path) -> None:
    pkg = tmp_path / "pkg"
    _write(pkg / "a.py", "from pkg.helpers import public_thing\n")
    baseline = tmp_path / "b.json"

    main(["--baseline", str(baseline), "--dir", str(pkg)])
    data = json.loads(baseline.read_text(encoding="utf-8"))
    assert data["baselines"]["cross_module_private_imports"]["metric_value"] == 0


def test_filenames_positional_args_are_ignored(tmp_path: Path) -> None:
    pkg = tmp_path / "pkg"
    _write(pkg / "a.py", "from pkg.h import _x\n")
    baseline = tmp_path / "b.json"

    exit_code = main(
        [
            "--baseline",
            str(baseline),
            "--dir",
            str(pkg),
            "anything.py",
        ]
    )
    assert exit_code == 0


def test_emit_violations_renders_none_when_empty() -> None:
    assert _emit_violations([]) == "  (none)"
