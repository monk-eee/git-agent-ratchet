"""Baseline registry: load, validate, and persist the ratchet JSON state."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SCHEMA_URL = "https://git-agent-ratchet.org/schemas/v1.json"
DEFAULT_AUTHOR = "git-agent-ratchet-core"


@dataclass
class Baseline:
    """In-memory view of a ratchet baseline registry file."""

    path: Path
    ratchet_meta: dict[str, Any] = field(default_factory=dict)
    baselines: dict[str, dict[str, Any]] = field(default_factory=dict)

    @classmethod
    def load(cls, path: Path) -> Baseline:
        """Load a baseline from disk; return an empty baseline if missing."""
        if not path.exists():
            return cls(path=path, ratchet_meta=_empty_meta(), baselines={})
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        return cls(
            path=path,
            ratchet_meta=data.get("ratchet_meta", _empty_meta()),
            baselines=data.get("baselines", {}),
        )

    def get_metric(self, name: str) -> int | None:
        """Return the stored metric_value for a ratchet, or None if absent."""
        entry = self.baselines.get(name)
        if entry is None:
            return None
        value = entry.get("metric_value")
        return int(value) if value is not None else None

    def set_entry(
        self,
        name: str,
        metric_value: int,
        items: list[dict[str, Any]],
    ) -> None:
        """Replace the stored entry for a ratchet with a fresh metric and item list."""
        self.baselines[name] = {
            "metric_value": int(metric_value),
            "items": items,
        }

    def save(self, repo_signature: str | None = None) -> None:
        """Persist the baseline to disk with stable, deterministic JSON formatting."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        meta = dict(self.ratchet_meta)
        meta["last_updated_by"] = DEFAULT_AUTHOR
        if repo_signature is not None:
            meta["repo_signature"] = repo_signature
        elif "repo_signature" not in meta:
            meta["repo_signature"] = _signature_from_baselines(self.baselines)
        payload = {
            "$schema": SCHEMA_URL,
            "ratchet_meta": meta,
            "baselines": self.baselines,
        }
        text = json.dumps(payload, indent=2, sort_keys=False) + "\n"
        self.path.write_text(text, encoding="utf-8")
        self.ratchet_meta = meta


def _empty_meta() -> dict[str, Any]:
    return {"repo_signature": "", "last_updated_by": DEFAULT_AUTHOR}


def _signature_from_baselines(baselines: dict[str, dict[str, Any]]) -> str:
    """Derive a deterministic content signature for change detection."""
    canonical = json.dumps(baselines, sort_keys=True).encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical).hexdigest()
