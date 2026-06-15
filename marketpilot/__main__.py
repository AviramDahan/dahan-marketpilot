"""Command-line entrypoint for MarketPilot utilities."""

from __future__ import annotations

from marketpilot.sync import _main as sync_main


def main() -> int:
    return sync_main()


if __name__ == "__main__":
    raise SystemExit(main())
