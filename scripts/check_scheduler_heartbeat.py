"""Monitor-only scheduler heartbeat checker for GitHub Actions."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from marketpilot.scheduler_health import SchedulerHealthStatus, evaluate_scheduler_heartbeat


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check MarketPilot scheduler heartbeat freshness.")
    parser.add_argument("--heartbeat-path", default="data/scheduler_heartbeat.jsonl")
    parser.add_argument("--max-age-seconds", type=int, default=900)
    parser.add_argument("--now-utc", default=None)
    args = parser.parse_args(argv)

    now = _parse_now(args.now_utc)
    check = evaluate_scheduler_heartbeat(
        Path(args.heartbeat_path),
        now=now,
        max_age_seconds=args.max_age_seconds,
    )
    print(json.dumps(check.to_json_dict(), sort_keys=True))
    return 0 if check.status is SchedulerHealthStatus.OK else 2


def _parse_now(value: str | None) -> datetime | None:
    if value is None:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise SystemExit("--now-utc must be timezone-aware")
    return parsed.astimezone(timezone.utc)


if __name__ == "__main__":
    raise SystemExit(main())

