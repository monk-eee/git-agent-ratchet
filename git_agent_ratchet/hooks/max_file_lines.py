"""Hook: ratchet-max-file-lines (Ratchet D)."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from git_agent_ratchet.hooks.gate import run_ratchet_gate
from git_agent_ratchet.ratchets.max_file_lines import (
    DEFAULT_MAX_LINES,
    RATCHET_NAME,
    OversizedFile,
    metric_value,
    scan_directory,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ratchet-max-file-lines",
        description=(
            "Fail when the total line overage across over-sized source files "
            "exceeds the recorded baseline. Shrinks are recorded automatically "
            "and staged back into the commit."
        ),
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=Path("config/ratchets/file_lines.json"),
        help="Path to the JSON baseline registry file.",
    )
    parser.add_argument(
        "--dir",
        dest="directory",
        type=Path,
        default=Path("src"),
        help="Directory tree to scan for over-sized files.",
    )
    parser.add_argument(
        "--max",
        dest="max_lines",
        type=int,
        default=DEFAULT_MAX_LINES,
        help=f"Per-file line-count limit (default: {DEFAULT_MAX_LINES}).",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=None,
        help="Directory name to exclude (repeatable). Defaults to tests/test.",
    )
    parser.add_argument(
        "filenames",
        nargs="*",
        help="Files supplied by pre-commit (ignored; full directory scan is used).",
    )
    return parser


def _emit_oversized(oversized: list[OversizedFile], max_lines: int) -> str:
    if not oversized:
        return "  (none)"
    lines = []
    for f in oversized:
        lines.append(f"  - {f.path}: {f.line_count} lines (+{f.overage} over {max_lines})")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    exclude = tuple(args.exclude) if args.exclude else ("tests", "test")
    oversized = scan_directory(args.directory, max_lines=args.max_lines, exclude_dirs=exclude)

    def trip_message(recorded: int, current: int) -> str:
        return (
            f"[ratchet] {RATCHET_NAME}: GATE TRIPPED.\n"
            f"  baseline overage = {recorded}\n"
            f"  current  overage = {current}\n"
            f"  delta            = +{current - recorded}\n"
            f"  over-sized files (max={args.max_lines}):\n"
            f"{_emit_oversized(oversized, args.max_lines)}\n"
            f"  Rule: per-file line counts may not grow past their recorded baseline.\n"
            f"  Fix: split the file into focused modules, or extract a helper into "
            f"an existing module that already owns the concept."
        )

    return run_ratchet_gate(
        ratchet_name=RATCHET_NAME,
        baseline_path=args.baseline,
        current=metric_value(oversized),
        items=oversized,
        trip_message=trip_message,
    )


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
