"""Tests for the shared baseline-gate runner (`hooks.gate`)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from git_agent_ratchet.baseline import Baseline
from git_agent_ratchet.hooks.gate import run_ratchet_gate

RATCHET = "demo_ratchet"


@dataclass(frozen=True)
class _Finding:
    name: str

    def to_dict(self) -> dict[str, object]:
        return {"name": self.name}


def _trip(recorded: int, current: int) -> str:
    return f"TRIPPED recorded={recorded} current={current}"


def _baseline_path(tmp_path: Path) -> Path:
    return tmp_path / "baseline.json"


def test_seed_on_first_run_writes_baseline_and_returns_zero(tmp_path, capsys) -> None:
    path = _baseline_path(tmp_path)
    rc = run_ratchet_gate(
        ratchet_name=RATCHET,
        baseline_path=path,
        current=2,
        items=[_Finding("a"), _Finding("b")],
        trip_message=_trip,
    )
    assert rc == 0
    assert path.exists()
    assert Baseline.load(path).get_metric(RATCHET) == 2
    assert "seeded baseline" in capsys.readouterr().out


def test_equal_metric_is_a_silent_pass(tmp_path, capsys) -> None:
    path = _baseline_path(tmp_path)
    baseline = Baseline.load(path)
    baseline.set_entry(name=RATCHET, metric_value=3, items=[])
    baseline.save()

    rc = run_ratchet_gate(
        ratchet_name=RATCHET,
        baseline_path=path,
        current=3,
        items=[],
        trip_message=_trip,
    )
    assert rc == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_growth_trips_the_gate_and_prints_message_to_stderr(tmp_path, capsys) -> None:
    path = _baseline_path(tmp_path)
    baseline = Baseline.load(path)
    baseline.set_entry(name=RATCHET, metric_value=1, items=[])
    baseline.save()

    rc = run_ratchet_gate(
        ratchet_name=RATCHET,
        baseline_path=path,
        current=4,
        items=[_Finding("x")],
        trip_message=_trip,
    )
    assert rc == 1
    captured = capsys.readouterr()
    assert "TRIPPED recorded=1 current=4" in captured.err
    # A tripped gate must not rewrite the baseline.
    assert Baseline.load(path).get_metric(RATCHET) == 1


def test_shrink_ratchets_baseline_down_and_restages(tmp_path, capsys) -> None:
    path = _baseline_path(tmp_path)
    baseline = Baseline.load(path)
    baseline.set_entry(name=RATCHET, metric_value=5, items=[{"name": "old"}])
    baseline.save()

    rc = run_ratchet_gate(
        ratchet_name=RATCHET,
        baseline_path=path,
        current=2,
        items=[_Finding("a"), _Finding("b")],
        trip_message=_trip,
    )
    assert rc == 0
    assert Baseline.load(path).get_metric(RATCHET) == 2
    assert "ratcheted down" in capsys.readouterr().out
