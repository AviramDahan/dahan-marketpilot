"""Read-only Phase 16.2 deployed-session observer."""

from __future__ import annotations

import argparse
import json
import os
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
from marketpilot.shared_state import load_dashboard_payload_from_env

from scripts.check_scheduler_heartbeat import _annotate_monitor_window, _read_remote_heartbeat, _remote_heartbeat_ok
from scripts.verify_render_golive import _check_dashboard_url


DEFAULT_DASHBOARD_URL = "https://dahan-marketpilot-dashboard.onrender.com"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Observe Phase 16.2 deployed session evidence.")
    parser.add_argument("--dashboard-url", default=os.environ.get("DASHBOARD_HEALTH_URL", DEFAULT_DASHBOARD_URL))
    parser.add_argument("--heartbeat-path", default=os.environ.get("SCHEDULER_HEARTBEAT_PATH", "data/scheduler_heartbeat.jsonl"))
    parser.add_argument("--heartbeat-url", default=os.environ.get("HEARTBEAT_HEALTH_URL"))
    parser.add_argument("--shared-state-url", default=os.environ.get("DASHBOARD_STATE_HEALTH_URL"))
    parser.add_argument("--max-heartbeat-age-seconds", type=int, default=900)
    parser.add_argument("--require-shared-state", action="store_true")
    parser.add_argument("--require-heartbeat", action="store_true")
    parser.add_argument("--timeout-seconds", type=int, default=10)
    args = parser.parse_args(argv)

    result = observe_deployed_session(
        dashboard_url=args.dashboard_url,
        heartbeat_path=Path(args.heartbeat_path),
        heartbeat_url=args.heartbeat_url,
        shared_state_url=args.shared_state_url,
        max_heartbeat_age_seconds=args.max_heartbeat_age_seconds,
        require_shared_state=args.require_shared_state,
        require_heartbeat=args.require_heartbeat,
        timeout_seconds=args.timeout_seconds,
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "passed" else 2


def observe_deployed_session(
    *,
    dashboard_url: str | None,
    heartbeat_path: Path,
    heartbeat_url: str | None,
    shared_state_url: str | None,
    max_heartbeat_age_seconds: int,
    require_shared_state: bool,
    require_heartbeat: bool,
    timeout_seconds: int,
) -> dict[str, object]:
    checks = {
        "dashboard_url": _check_dashboard_url(dashboard_url, timeout_seconds=timeout_seconds),
        "shared_state": _check_shared_state(
            shared_state_url=shared_state_url,
            timeout_seconds=timeout_seconds,
        ),
        "heartbeat": _check_heartbeat(
            heartbeat_path,
            heartbeat_url=heartbeat_url,
            max_age_seconds=max_heartbeat_age_seconds,
            timeout_seconds=timeout_seconds,
        ),
        "local_computer_independence": {
            "status": "operator_evidence_required",
            "detail": "Confirm Render worker generated heartbeat/shared-state while local scheduler is not running.",
        },
    }
    status = _overall_status(
        checks,
        require_shared_state=require_shared_state,
        require_heartbeat=require_heartbeat,
    )
    return {
        "status": status,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "paper_trading_only": True,
        "market_session_observation": status == "passed",
        "checks": checks,
    }


def _check_shared_state(*, shared_state_url: str | None, timeout_seconds: int) -> dict[str, object]:
    if shared_state_url:
        payload = _read_remote_shared_state(shared_state_url, timeout_seconds=timeout_seconds)
        payload["status"] = "passed" if _remote_shared_state_ok(payload) else payload.get("status", "failed")
        return payload
    try:
        snapshot = load_dashboard_payload_from_env()
    except Exception as exc:
        return {"status": "failed", "reason": type(exc).__name__, "detail": _redact_text(str(exc))}
    if snapshot is None:
        return {"status": "not_run", "reason": "REDIS_URL_missing_or_dashboard_payload_absent"}
    payload = dict(snapshot.payload)
    return {
        "status": "passed",
        "key": snapshot.key,
        "source": payload.get("source"),
        "authority": payload.get("authority"),
        "source_timestamp": payload.get("source_timestamp"),
        "freshness_level": payload.get("freshness_level"),
        "paper_trading_only": payload.get("paper_trading_only") is True,
    }


def _read_remote_shared_state(url: str, *, timeout_seconds: int) -> dict[str, object]:
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "MarketPilot-Deployed-Session-Observer"})
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
        return {
            "status": "failed",
            "reason": "remote_shared_state_payload_not_object",
            "paper_trading_only": True,
            "monitor_only": True,
            "controls_scheduler": False,
            "controls_orders": False,
            "controls_recovery": False,
        }
    return _sanitize_remote_shared_state(loaded)


def _sanitize_remote_shared_state(payload: Mapping[str, object]) -> dict[str, object]:
    allowed_keys = {
        "status",
        "checked_at",
        "source",
        "authority",
        "source_timestamp",
        "age_seconds",
        "freshness_level",
        "reason",
        "read_only_dashboard",
        "paper_trading_only",
        "monitor_only",
        "controls_scheduler",
        "controls_orders",
        "controls_recovery",
    }
    return {key: payload.get(key) for key in sorted(allowed_keys)}


def _remote_shared_state_ok(payload: Mapping[str, object]) -> bool:
    return (
        payload.get("status") in {"ok", "passed"}
        and payload.get("monitor_only") is True
        and payload.get("read_only_dashboard") is True
        and payload.get("paper_trading_only") is True
        and payload.get("controls_scheduler") is False
        and payload.get("controls_orders") is False
        and payload.get("controls_recovery") is False
    )


def _check_heartbeat(
    path: Path,
    *,
    heartbeat_url: str | None,
    max_age_seconds: int,
    timeout_seconds: int,
) -> dict[str, object]:
    if heartbeat_url:
        payload = _read_remote_heartbeat(heartbeat_url, timeout_seconds=timeout_seconds)
        payload = _annotate_monitor_window(payload, now=None)
        payload["status"] = "passed" if _remote_heartbeat_ok(payload, now=None) else payload.get("status", "failed")
        return payload
    check = evaluate_scheduler_heartbeat(path, max_age_seconds=max_age_seconds)
    payload = check.to_json_dict()
    payload["status"] = "passed" if check.status is SchedulerHealthStatus.OK else check.status.value
    payload["monitor_only"] = True
    payload["controls_scheduler"] = False
    payload["controls_orders"] = False
    payload["controls_recovery"] = False
    return payload


def _overall_status(
    checks: Mapping[str, Mapping[str, object]],
    *,
    require_shared_state: bool,
    require_heartbeat: bool,
) -> str:
    if any(check.get("status") == "failed" for check in checks.values()):
        return "failed"
    required = [checks["dashboard_url"], checks["shared_state"], checks["heartbeat"]]
    if require_shared_state:
        required.append(checks["shared_state"])
    if require_heartbeat:
        required.append(checks["heartbeat"])
    if all(check.get("status") == "passed" for check in required):
        return "passed"
    return "blocked_external_not_verified"


def _redact_text(value: str) -> str:
    redacted = value
    for key in ("REDIS_URL", "DASHBOARD_PASSWORD", "TOKEN", "SECRET", "PASSWORD"):
        redacted = redacted.replace(key.lower(), "[redacted]").replace(key, "[redacted]")
    return redacted


if __name__ == "__main__":
    raise SystemExit(main())
