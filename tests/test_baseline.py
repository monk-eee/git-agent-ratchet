"""Tests for the Baseline registry: load, mutate, save, signature, idempotency."""

from __future__ import annotations

import json
from pathlib import Path

from git_agent_ratchet.baseline import (
    DEFAULT_AUTHOR,
    SCHEMA_URL,
    Baseline,
    _signature_from_baselines,
)


def test_load_missing_file_returns_empty_baseline(tmp_path: Path) -> None:
    path = tmp_path / "missing.json"
    baseline = Baseline.load(path)
    assert baseline.path == path
    assert baseline.baselines == {}
    assert baseline.ratchet_meta["last_updated_by"] == DEFAULT_AUTHOR


def test_load_existing_file_round_trips_baselines(tmp_path: Path) -> None:
    path = tmp_path / "duplicates.json"
    payload = {
        "$schema": SCHEMA_URL,
        "ratchet_meta": {"repo_signature": "sha256:abc", "last_updated_by": "x"},
        "baselines": {
            "duplicate_helpers": {
                "metric_value": 2,
                "items": [{"name": "_foo", "occurrences": ["a.py", "b.py"]}],
            }
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")

    baseline = Baseline.load(path)

    assert baseline.get_metric("duplicate_helpers") == 2
    assert baseline.baselines["duplicate_helpers"]["items"][0]["name"] == "_foo"


def test_get_metric_returns_none_for_unknown_ratchet(tmp_path: Path) -> None:
    baseline = Baseline(path=tmp_path / "b.json")
    assert baseline.get_metric("not-there") is None


def test_set_entry_replaces_and_save_writes_canonical_json(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "duplicates.json"
    baseline = Baseline(path=path)

    baseline.set_entry(
        name="duplicate_helpers",
        metric_value=3,
        items=[{"name": "_foo", "occurrences": ["a.py", "b.py", "c.py"]}],
    )
    baseline.save()

    raw = path.read_text(encoding="utf-8")
    data = json.loads(raw)

    assert data["$schema"] == SCHEMA_URL
    assert data["baselines"]["duplicate_helpers"]["metric_value"] == 3
    assert data["ratchet_meta"]["last_updated_by"] == DEFAULT_AUTHOR
    assert raw.endswith("\n"), "save() must end with a trailing newline for git-friendliness"


def test_save_creates_parent_directories(tmp_path: Path) -> None:
    path = tmp_path / "deeply" / "nested" / "duplicates.json"
    baseline = Baseline(path=path)
    baseline.set_entry("duplicate_helpers", 0, [])
    baseline.save()

    assert path.exists()


def test_save_then_load_is_idempotent(tmp_path: Path) -> None:
    path = tmp_path / "duplicates.json"
    a = Baseline(path=path)
    a.set_entry("duplicate_helpers", 1, [{"name": "_foo", "occurrences": ["a.py", "b.py"]}])
    a.save(repo_signature="sha256:fixed")

    first_text = path.read_text(encoding="utf-8")

    b = Baseline.load(path)
    b.save(repo_signature="sha256:fixed")
    second_text = path.read_text(encoding="utf-8")

    assert first_text == second_text, "load + save with the same signature must be byte-identical"


def test_signature_from_baselines_is_deterministic() -> None:
    a = {"duplicate_helpers": {"metric_value": 1, "items": []}}
    b = {"duplicate_helpers": {"metric_value": 1, "items": []}}
    assert _signature_from_baselines(a) == _signature_from_baselines(b)
    assert _signature_from_baselines(a).startswith("sha256:")


def test_signature_changes_when_baseline_changes() -> None:
    a = {"duplicate_helpers": {"metric_value": 1, "items": []}}
    b = {"duplicate_helpers": {"metric_value": 2, "items": []}}
    assert _signature_from_baselines(a) != _signature_from_baselines(b)
