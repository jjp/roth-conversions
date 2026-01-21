from __future__ import annotations

import argparse

from .commands.roth import add_roth_subcommands


def build_parser(*, prog: str = "retirement-toolkit") -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog=prog,
        description="Retirement Toolkit (multi-use-case CLI)",
    )

    sub = p.add_subparsers(dest="tool", required=True)

    # Namespaced command groups
    add_roth_subcommands(sub)

    return p


def main(argv: list[str] | None = None, *, prog: str | None = None) -> int:
    parser = build_parser(prog=prog or "retirement-toolkit")
    args = parser.parse_args(argv)

    # All subcommands set `func`.
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
