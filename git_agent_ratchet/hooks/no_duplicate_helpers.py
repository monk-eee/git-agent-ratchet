"""Hook: ratchet-no-duplicate-helpers (Ratchet A)."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from git_agent_ratchet.baseline import Baseline
from git_agent_ratchet.ratchets.duplicate_helpers import (
    RATCHET_NAME,
    DuplicateHelper,
    metric_value,
    scan_directory,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ratchet-no-duplicate-helpers",
        description=(
            "Fail when the count of duplicate private helper functions across the "
            "target directory exceeds the recorded baseline. Shrinks are recorded "
            "automatically and staged back into the commit."
        ),
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=Path("config/ratchets/duplicates.json"),
        help="Path to the JSON baseline registry file.",
    )
    parser.add_argument(
        "--dir",
        dest="directory",
        type=Path,
        default=Path("src"),
        help="Directory tree to scan for duplicate helpers.",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=None,
        help="Directory name to exclude (repeatable). Defaults to tests/test.",
    )
    parser.add_argument(
        "--lang",
        dest="languages",
        action="append",
        default=None,
        choices=["python", "typescript", "csharp"],
        help=(
            "Restrict scanning to one or more languages (repeatable). "
            "Default: all registered extractors."
        ),
    )
    parser.add_argument(
        "filenames",
        nargs="*",
        help="Files supplied by pre-commit (ignored; full directory scan is used).",
    )
    return parser


def _emit_duplicates(duplicates: list[DuplicateHelper]) -> str:
    if not duplicates:
        return "  (none)"
    lines = []
    for dup in duplicates:
        occ = ", ".join(dup.occurrences)
        lines.append(f"  - {dup.name} -> [{occ}]")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    exclude = tuple(args.exclude) if args.exclude else ("tests", "test")
    duplicates = scan_directory(
        args.directory,
        exclude_dirs=exclude,
        languages=args.languages,
    )
    current = metric_value(duplicates)

    baseline = Baseline.load(args.baseline)
    recorded = baseline.get_metric(RATCHET_NAME)

    if recorded is None:
        baseline.set_entry(
            name=RATCHET_NAME,
            metric_value=current,
            items=[d.to_dict() for d in duplicates],
        )
        baseline.save()
        print(
            f"[ratchet] {RATCHET_NAME}: seeded baseline at {args.baseline} "
            f"(metric_value={current})."
        )
        return 0

    if current > recorded:
        print(
            f"[ratchet] {RATCHET_NAME}: GATE TRIPPED.\n"
            f"  baseline metric_value = {recorded}\n"
            f"  current  metric_value = {current}\n"
            f"  delta                 = +{current - recorded}\n"
            f"  duplicates now present:\n{_emit_duplicates(duplicates)}\n"
            f"  Rule: duplicate-helper occurrences are not permitted to grow.\n"
            f"  Fix: reuse the existing helper instead of forking a new one, "
            f"or rename the new function so it's not a private helper.",
            file=sys.stderr,
        )
        return 1

    if current < recorded:
        baseline.set_entry(
            name=RATCHET_NAME,
            metric_value=current,
            items=[d.to_dict() for d in duplicates],
        )
        baseline.save()
        print(
            f"[ratchet] {RATCHET_NAME}: baseline ratcheted down "
            f"({recorded} -> {current}); registry restaged."
        )
        return 0

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
