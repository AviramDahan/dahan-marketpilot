"""Monitor-only scheduler heartbeat checker for GitHub Actions."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping
from urllib.error import URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from marketpilot.scheduler_health import SchedulerHealthStatus, evaluate_scheduler_heartbeat


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check MarketPilot scheduler heartbeat freshness.")
    parser.add_argument("--heartbeat-path", default="data/scheduler_heartbeat.jsonl")
    parser.add_argument("--heartbeat-url", default=None)
    parser.add_argument("--max-age-seconds", type=int, default=900)
    parser.add_argument("--now-utc", default=None)
    parser.add_argument("--timeout-seconds", type=int, default=20)
    args = parser.parse_args(argv)

    now = _parse_now(args.now_utc)
    if args.heartbeat_url:
        payload = _read_remote_heartbeat(args.heartbeat_url, timeout_seconds=args.timeout_seconds)
        print(json.dumps(payload, sort_keys=True))
        return 0 if _remote_heartbeat_ok(payload) else 2

    check = evaluate_scheduler_heartbeat(
        Path(args.heartbeat_path),
        now=now,
        max_age_seconds=args.max_age_seconds,
    )
    print(json.dumps(check.to_json_dict(), sort_keys=True))
    return 0 if check.status is SchedulerHealthStatus.OK else 2


def _read_remote_heartbeat(url: str, *, timeout_seconds: int) -> dict[str, object]:
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "MarketPilot-Heartbeat-Monitor"})
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            loaded = json.loads(response.read().decode("utf-8"))
    except (OSError, TimeoutError, URLError, json.JSONDecodeError) as exc:
        return {
            "status": "failed",
            "reason": type(exc).__name__,
            "paper_trading_only": True,
            "monitor_only": True,
            "controls_scheduler": False,
            "controls_orders": False,
            "controls_recovery": False,
        }
    if not isinstance(loaded, dict):
        raise SystemExit("remote heartbeat payload must be a JSON object")
    return _sanitize_remote_payload(loaded)


def _sanitize_remote_payload(payload: dict[str, object]) -> dict[str, object]:
    allowed_keys = {
        "status",
        "checked_at",
        "latest_heartbeat_at",
        "age_seconds",
        "reason",
        "worker_state",
        "paper_trading_only",
        "monitor_only",
        "controls_scheduler",
        "controls_orders",
        "controls_recovery",
    }
    return {key: payload.get(key) for key in sorted(allowed_keys)}


def _remote_heartbeat_ok(payload: Mapping[str, object]) -> bool:
    return (
        payload.get("status") in {"ok", "passed"}
        and payload.get("paper_trading_only") is True
        and payload.get("monitor_only") is True
        and payload.get("controls_scheduler") is False
        and payload.get("controls_orders") is False
    )


def _parse_now(value: str | None) -> datetime | None:
    if value is None:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise SystemExit("--now-utc must be timezone-aware")
    return parsed.astimezone(timezone.utc)


if __name__ == "__main__":
    raise SystemExit(main())
