"""Tests for the Ratchet F hook entry point (no-print-outside-allowlist)."""

from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent

from git_agent_ratchet.hooks.no_print_outside_allowlist import _emit_calls, main


def _write(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(source).lstrip(), encoding="utf-8")


def test_first_run_seeds_baseline_and_passes(tmp_path: Path, capsys) -> None:
    pkg = tmp_path / "pkg"
    _write(pkg / "a.py", "print('hi')\n")
    baseline = tmp_path / "b.json"

    exit_code = main(["--baseline", str(baseline), "--dir", str(pkg)])

    assert exit_code == 0
    data = json.loads(baseline.read_text(encoding="utf-8"))
    assert data["baselines"]["print_calls"]["metric_value"] == 1
    assert "seeded baseline" in capsys.readouterr().out


def test_growth_fails(tmp_path: Path, capsys) -> None:
    pkg = tmp_path / "pkg"
    _write(pkg / "a.py", "print('a')\n")
    baseline = tmp_path / "b.json"
    main(["--baseline", str(baseline), "--dir", str(pkg)])

    _write(pkg / "b.py", "print('b')\n")
    exit_code = main(["--baseline", str(baseline), "--dir", str(pkg)])

    assert exit_code == 1
    err = capsys.readouterr().err
    assert "GATE TRIPPED" in err


def test_shrinkage_ratchets_down(tmp_path: Path) -> None:
    pkg = tmp_path / "pkg"
    _write(pkg / "a.py", "print('a')\nprint('a2')\n")
    baseline = tmp_path / "b.json"
    main(["--baseline", str(baseline), "--dir", str(pkg)])

    _write(pkg / "a.py", "print('a')\n")
    exit_code = main(["--baseline", str(baseline), "--dir", str(pkg)])

    assert exit_code == 0
    data = json.loads(baseline.read_text(encoding="utf-8"))
    assert data["baselines"]["print_calls"]["metric_value"] == 1


def test_allow_prefix_excludes_files_from_scan(tmp_path: Path) -> None:
    pkg = tmp_path / "pkg"
    _write(pkg / "hooks" / "h.py", "print('hook stderr output')\n")
    _write(pkg / "core" / "c.py", "import logging\n")
    baseline = tmp_path / "b.json"

    exit_code = main(
        [
            "--baseline",
            str(baseline),
            "--dir",
            str(pkg),
            "--allow-prefix",
            "pkg/hooks",
        ]
    )

    assert exit_code == 0
    data = json.loads(baseline.read_text(encoding="utf-8"))
    assert data["baselines"]["print_calls"]["metric_value"] == 0


def test_steady_state_passes_silently(tmp_path: Path, capsys) -> None:
    pkg = tmp_path / "pkg"
    _write(pkg / "a.py", "print('x')\n")
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
    _write(pkg / "a.py", "print('x')\n")
    baseline = tmp_path / "b.json"

    exit_code = main(["--baseline", str(baseline), "--dir", str(pkg), "x.py"])
    assert exit_code == 0


def test_emit_calls_renders_none_when_empty() -> None:
    assert _emit_calls([]) == "  (none)"
