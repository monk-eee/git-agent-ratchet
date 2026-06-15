"""Shared baseline-gate runner for the ratcheting hooks.

Ratchets A, D, E, F, and G share one control flow: scan, load the baseline,
seed it on first run, fail when the metric grows, and ratchet the baseline
down (restaging it) when the metric shrinks. This module owns that flow once
so each hook supplies only its scan results and its failure message.
"""

from __future__ import annotations

import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Protocol

from git_agent_ratchet.baseline import Baseline


class SupportsToDict(Protocol):
    """A ratchet finding that can serialise itself into the baseline registry."""

    def to_dict(self) -> dict[str, object]: ...


def run_ratchet_gate(
    *,
    ratchet_name: str,
    baseline_path: Path,
    current: int,
    items: Sequence[SupportsToDict],
    trip_message: Callable[[int, int], str],
) -> int:
    """Execute the seed / fail-on-growth / ratchet-down flow for one ratchet.

    ``trip_message`` is called with ``(recorded, current)`` only when the gate
    trips, so each hook keeps full control of its stderr diagnostic. Returns the
    process exit code: ``0`` on seed, no-change, or shrink; ``1`` on growth.
    """
    baseline = Baseline.load(baseline_path)
    recorded = baseline.get_metric(ratchet_name)

    if recorded is None:
        _record(baseline, ratchet_name, current, items)
        print(
            f"[ratchet] {ratchet_name}: seeded baseline at {baseline_path} "
            f"(metric_value={current})."
        )
        return 0

    if current > recorded:
        print(trip_message(recorded, current), file=sys.stderr)
        return 1

    if current < recorded:
        _record(baseline, ratchet_name, current, items)
        print(
            f"[ratchet] {ratchet_name}: baseline ratcheted down "
            f"({recorded} -> {current}); registry restaged."
        )
        return 0

    return 0


def _record(
    baseline: Baseline,
    ratchet_name: str,
    current: int,
    items: Sequence[SupportsToDict],
) -> None:
    baseline.set_entry(
        name=ratchet_name,
        metric_value=current,
        items=[item.to_dict() for item in items],
    )
    baseline.save()
