"""Hook: ratchet-dont-use-powershell (Ratchet H)."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from git_agent_ratchet.ratchets.powershell_usage import scan_files


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ratchet-dont-use-powershell",
        description=(
            "Fail when staged files contain PowerShell commands or script references "
            "(powershell/pwsh, .ps1, common cmdlets)."
        ),
    )
    parser.add_argument(
        "filenames",
        nargs="*",
        help="Files supplied by pre-commit. Each file is scanned for PowerShell usage.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    paths = [Path(f) for f in args.filenames]
    matches = scan_files(paths)

    if not matches:
        return 0

    print("[ratchet] dont_use_powershell: GATE TRIPPED.", file=sys.stderr)
    print(
        "  PowerShell usage detected in staged files. This repo enforces portable shell usage.",
        file=sys.stderr,
    )
    for match in matches:
        print(
            f"  {match.file}:{match.line_number}  [{match.signature}]  {match.line}",
            file=sys.stderr,
        )
    print(
        "  Fix: replace with cross-platform alternatives (Python/uv shell-neutral commands) "
        "and re-stage.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
