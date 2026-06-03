"""Hook: ratchet-anti-bypass (Ratchet C)."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from git_agent_ratchet.ratchets.anti_bypass import BYPASS_KEY_ENV, evaluate


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ratchet-anti-bypass",
        description=(
            "Fail when an automated process attempts to mutate protected ratchet "
            "configuration files without the human bypass key."
        ),
    )
    parser.add_argument(
        "--enforce-files",
        required=True,
        help=(
            "Comma-separated list of repo-relative file paths that may only be "
            "mutated when HUMAN_RATCHET_BYPASS_KEY is set."
        ),
    )
    parser.add_argument(
        "filenames",
        nargs="*",
        help="Staged files supplied by pre-commit.",
    )
    return parser


def _split_enforce_files(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    protected = _split_enforce_files(args.enforce_files)
    decision = evaluate(staged_files=args.filenames, protected_files=protected)

    if not decision.blocked:
        return 0

    print("[ratchet] anti_bypass: GATE TRIPPED.", file=sys.stderr)
    print(f"  reason: {decision.reason}", file=sys.stderr)
    print("  protected files in this commit:", file=sys.stderr)
    for path in decision.touched_protected_files:
        print(f"    - {path}", file=sys.stderr)
    if decision.agent_signal:
        print(f"  agent signal: {decision.agent_signal}", file=sys.stderr)
    print(
        f"  Fix: a human operator must export {BYPASS_KEY_ENV}=<value> in their "
        f"shell and re-run the commit. Agents must not set this variable.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
