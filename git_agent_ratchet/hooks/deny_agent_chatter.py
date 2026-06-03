"""Hook: ratchet-deny-agent-chatter (Ratchet B)."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from git_agent_ratchet.ratchets.agent_chatter import scan_files


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ratchet-deny-agent-chatter",
        description=(
            "Fail when staged files contain conversational agent-chatter artifacts "
            "(e.g. 'Sure, I can help with...', 'As an AI, ...')."  # ratchet-allow: agent_chatter
        ),
    )
    parser.add_argument(
        "filenames",
        nargs="*",
        help="Files supplied by pre-commit. Each file is scanned for chatter signatures.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    paths = [Path(f) for f in args.filenames]
    matches = scan_files(paths)

    if not matches:
        return 0

    print("[ratchet] agent_chatter: GATE TRIPPED.", file=sys.stderr)
    print(
        "  Conversational agent artifacts detected in the following staged files:",
        file=sys.stderr,
    )
    for match in matches:
        print(
            f"  {match.file}:{match.line_number}  [{match.signature}]  {match.line}",
            file=sys.stderr,
        )
    print(
        "  Fix: remove the conversational preamble/postscript and re-stage the file.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
