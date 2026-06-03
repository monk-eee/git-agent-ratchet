"""Unified CLI dispatcher: `git-agent-ratchet <subcommand>`."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from git_agent_ratchet._version import __version__
from git_agent_ratchet.hooks import anti_bypass, deny_agent_chatter, no_duplicate_helpers

SUBCOMMANDS = {
    "no-duplicate-helpers": no_duplicate_helpers.main,
    "deny-agent-chatter": deny_agent_chatter.main,
    "anti-bypass": anti_bypass.main,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="git-agent-ratchet",
        description=(
            "git-agent-ratchet: deterministic git ratchets for guarding against agent drift."
        ),
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "subcommand",
        choices=sorted(SUBCOMMANDS),
        help="The ratchet to invoke.",
    )
    parser.add_argument(
        "args",
        nargs=argparse.REMAINDER,
        help="Arguments forwarded to the chosen subcommand.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    handler = SUBCOMMANDS[args.subcommand]
    return handler(args.args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
