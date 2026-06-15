"""Hook: ratchet-no-print-outside-allowlist (Ratchet F)."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from git_agent_ratchet.hooks.gate import run_ratchet_gate
from git_agent_ratchet.ratchets.print_outside_allowlist import (
    RATCHET_NAME,
    PrintCall,
    metric_value,
    scan_directory,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ratchet-no-print-outside-allowlist",
        description=(
            "Fail when the count of print() calls outside the allowlisted "
            "path prefixes exceeds the recorded baseline."
        ),
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=Path("config/ratchets/print_calls.json"),
        help="Path to the JSON baseline registry file.",
    )
    parser.add_argument(
        "--dir",
        dest="directory",
        type=Path,
        default=Path("src"),
        help="Directory tree to scan for print() calls.",
    )
    parser.add_argument(
        "--allow-prefix",
        action="append",
        default=None,
        dest="allow_prefixes",
        help=(
            "Posix path prefix where print() is allowed (repeatable). "
            "Typically the CLI entry point and the hook shims."
        ),
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


def _emit_calls(calls: list[PrintCall]) -> str:
    if not calls:
        return "  (none)"
    return "\n".join(f"  - {c.file}:{c.line}:{c.col}" for c in calls)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    exclude = tuple(args.exclude) if args.exclude else ("tests", "test")
    allow_prefixes = tuple(args.allow_prefixes) if args.allow_prefixes else ()
    calls = scan_directory(
        args.directory,
        exclude_dirs=exclude,
        allow_prefixes=allow_prefixes,
    )

    def trip_message(recorded: int, current: int) -> str:
        return (
            f"[ratchet] {RATCHET_NAME}: GATE TRIPPED.\n"
            f"  baseline metric_value = {recorded}\n"
            f"  current  metric_value = {current}\n"
            f"  delta                 = +{current - recorded}\n"
            f"  print() calls outside the allowlist:\n{_emit_calls(calls)}\n"
            f"  Rule: production modules use logging.getLogger(__name__), not print().\n"
            f"  Fix: replace the print() with a logger call, or move the code into an "
            f"allowlisted CLI/hook shim if it is genuinely user-facing output."
        )

    return run_ratchet_gate(
        ratchet_name=RATCHET_NAME,
        baseline_path=args.baseline,
        current=metric_value(calls),
        items=calls,
        trip_message=trip_message,
    )


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
