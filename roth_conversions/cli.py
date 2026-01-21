from __future__ import annotations

import sys

from retirement_toolkit.cli import main as toolkit_main


def main(argv: list[str] | None = None) -> int:
    """Compatibility wrapper.

    The canonical CLI lives in `retirement_toolkit.cli` and namespaces commands:
      retirement-toolkit roth --config ... report

    This wrapper preserves the historical entrypoint:
      roth-conversions --config ... report
    """

    if argv is None:
        argv = sys.argv[1:]

    # The old CLI had no explicit namespace; it was implicitly the Roth tool.
    return int(toolkit_main(["roth", *argv], prog="roth-conversions"))


if __name__ == "__main__":
    raise SystemExit(main())
