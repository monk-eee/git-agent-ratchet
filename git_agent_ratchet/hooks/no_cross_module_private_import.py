"""Hook: ratchet-no-cross-module-private-import (Ratchet E)."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from git_agent_ratchet.hooks.gate import run_ratchet_gate
from git_agent_ratchet.ratchets.cross_module_private_import import (
    RATCHET_NAME,
    PrivateImport,
    metric_value,
    scan_directory,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ratchet-no-cross-module-private-import",
        description=(
            "Fail when the count of cross-module imports of underscore-prefixed "
            "names exceeds the recorded baseline. Shrinks are recorded automatically "
            "and staged back into the commit."
        ),
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=Path("config/ratchets/private_imports.json"),
        help="Path to the JSON baseline registry file.",
    )
    parser.add_argument(
        "--dir",
        dest="directory",
        type=Path,
        default=Path("src"),
        help="Directory tree to scan for cross-module private imports.",
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


def _emit_violations(violations: list[PrivateImport]) -> str:
    if not violations:
        return "  (none)"
    return "\n".join(
        f"  - {v.file}:{v.line}  {v.name} <- {v.source_module or '?'}" for v in violations
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    exclude = tuple(args.exclude) if args.exclude else ("tests", "test")
    violations = scan_directory(args.directory, exclude_dirs=exclude)

    def trip_message(recorded: int, current: int) -> str:
        return (
            f"[ratchet] {RATCHET_NAME}: GATE TRIPPED.\n"
            f"  baseline metric_value = {recorded}\n"
            f"  current  metric_value = {current}\n"
            f"  delta                 = +{current - recorded}\n"
            f"  cross-module private imports now present:\n{_emit_violations(violations)}\n"
            f"  Rule: underscore-prefixed names are private to their defining module.\n"
            f"  Fix: drop the leading underscore (make it public), import from the "
            f"defining module's intended public surface, or move the helper into the "
            f"consumer's own module."
        )

    return run_ratchet_gate(
        ratchet_name=RATCHET_NAME,
        baseline_path=args.baseline,
        current=metric_value(violations),
        items=violations,
        trip_message=trip_message,
    )


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
