"""Sample module for the downstream consumer example.

Clean code so a fresh `pre-commit run --all-files` seeds the baselines
and exits zero. Add a duplicate `_helper` here and in a sibling module
to see Ratchet A trip on the next commit.
"""

from __future__ import annotations


def greet(name: str) -> str:
    return f"hello, {name}"


def main() -> int:
    print(greet("world"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
