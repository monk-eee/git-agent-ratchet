"""Hook: ratchet-no-temporary-comments (Ratchet G)."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from git_agent_ratchet.hooks.gate import run_ratchet_gate
from git_agent_ratchet.ratchets.temporary_comments import (
    RATCHET_NAME,
    TemporaryMarker,
    metric_value,
    scan_directory,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ratchet-no-temporary-comments",
        description=(
            "Fail when the count of calcified-shortcut comment markers "
            "(see TEMPORARY_SIGNATURES in the scanner module) exceeds the "
            "recorded baseline."
        ),
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=Path("config/ratchets/temporary_comments.json"),
        help="Path to the JSON baseline registry file.",
    )
    parser.add_argument(
        "--dir",
        dest="directory",
        type=Path,
        default=Path("src"),
        help="Directory tree to scan.",
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


def _emit_matches(matches: list[TemporaryMarker]) -> str:
    if not matches:
        return "  (none)"
    return "\n".join(f"  - {m.file}:{m.line}  [{m.signature}]  {m.snippet}" for m in matches)


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    exclude = (
        tuple(args.exclude)
        if args.exclude
        else ("tests", "test", "node_modules", ".venv", "venv", "dist", "build")
    )
    matches = scan_directory(args.directory, exclude_dirs=exclude)

    def trip_message(recorded: int, current: int) -> str:
        return (
            f"[ratchet] {RATCHET_NAME}: GATE TRIPPED.\n"
            f"  baseline metric_value = {recorded}\n"
            f"  current  metric_value = {current}\n"
            f"  delta                 = +{current - recorded}\n"
            f"  temporary-comment markers now present:\n{_emit_matches(matches)}\n"
            f"  Rule: calcified-shortcut comments (see TEMPORARY_SIGNATURES) "
            f"signal an expedient-path commit and never get removed.\n"
            f"  Fix: either land the real change in the same commit so the comment "
            f"goes away, or add 'ratchet-allow: temporary_comments' to the line "
            f"if it legitimately quotes the rule (docs / tests / this ratchet)."
        )

    return run_ratchet_gate(
        ratchet_name=RATCHET_NAME,
        baseline_path=args.baseline,
        current=metric_value(matches),
        items=matches,
        trip_message=trip_message,
    )


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
