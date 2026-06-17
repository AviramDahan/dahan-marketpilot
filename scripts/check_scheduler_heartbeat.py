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

from marketpilot.scheduler_calendar import evaluate_market_session
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
        payload = _annotate_monitor_window(payload, now=now)
        print(json.dumps(payload, sort_keys=True))
        return 0 if _remote_heartbeat_ok(payload, now=now) else 2

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


def _monitor_flags_ok(payload: Mapping[str, object]) -> bool:
    return (
        payload.get("status") in {"ok", "passed", "stale"}
        and payload.get("monitor_only") is True
        and payload.get("paper_trading_only") is True
        and payload.get("controls_scheduler") is False
        and payload.get("controls_orders") is False
        and payload.get("controls_recovery") is False
    )


def _annotate_monitor_window(payload: Mapping[str, object], *, now: datetime | None) -> dict[str, object]:
    annotated = dict(payload)
    decision = evaluate_market_session(now=now)
    annotated["market_window_status"] = decision.status.value
    annotated["market_window_reason"] = decision.reason.value if decision.reason else None
    annotated["heartbeat_required_now"] = decision.eligible_for_orders
    return annotated


def _remote_heartbeat_ok(payload: Mapping[str, object], *, now: datetime | None = None) -> bool:
    if not _monitor_flags_ok(payload):
        return False
    if payload.get("status") in {"ok", "passed"}:
        return True
    return payload.get("status") == "stale" and payload.get("reason") == "heartbeat_stale" and _market_is_closed(now=now)


def _market_is_closed(*, now: datetime | None) -> bool:
    return not evaluate_market_session(now=now).eligible_for_orders


def _parse_now(value: str | None) -> datetime | None:
    if value is None:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise SystemExit("--now-utc must be timezone-aware")
    return parsed.astimezone(timezone.utc)


if __name__ == "__main__":
    raise SystemExit(main())
