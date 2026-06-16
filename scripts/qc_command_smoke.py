"""Run a guarded QuantConnect Paper command smoke with sanitized output.

SIMULATED PAPER TRADING ONLY - NOT FINANCIAL ADVICE.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any

from marketpilot.qc_api import QCApiClient


ENABLE_ENV = "MARKETPILOT_QC_COMMAND_SMOKE_ENABLED"
REQUIRED_ENV = (
    "QUANTCONNECT_USER_ID",
    "QUANTCONNECT_API_TOKEN",
    "QC_PROJECT_ID",
    "QC_DEPLOY_ID",
)
SAFE_ID_ENV = ("QC_PROJECT_ID", "QC_DEPLOY_ID", "QC_COMPILE_ID", "QC_NODE_ID", "QC_VERSION_ID")
SECRET_MARKERS = ("TOKEN", "SECRET", "PASSWORD", "AUTH", "KEY")


def build_marketpilot_signal_command(*, now_utc: datetime | None = None) -> dict[str, object]:
    now = now_utc or datetime.now(timezone.utc)
    return {
        "command_type": "marketpilot_signal",
        "correlation_id": f"qc-smoke-{now.strftime('%Y%m%d%H%M%S')}",
        "signal_id": f"qc-smoke-sig-{now.strftime('%Y%m%d%H%M%S')}",
        "idempotency_key": f"qc-smoke-order-{now.strftime('%Y%m%d%H%M%S')}",
        "symbol": "SPY",
        "quantity": 1,
        "signal_time_utc": now.isoformat(),
        "expires_at_utc": (now + timedelta(minutes=20)).isoformat(),
        "strategy_mode": "daily_only",
        "primary_setup": "external_smoke_test",
        "paper_trading_only": True,
        "command_delivery_is_order_execution": False,
    }


def build_typed_order_command_probe(*, now_utc: datetime | None = None) -> dict[str, object]:
    command = build_marketpilot_signal_command(now_utc=now_utc)
    return {
        "$type": "MarketPilotSignalCommand",
        "parameters": command,
    }


def build_command(label: str, *, now_utc: datetime | None = None) -> dict[str, object]:
    if label == "marketpilot_signal":
        return build_marketpilot_signal_command(now_utc=now_utc)
    if label == "typed_order_command_probe":
        return build_typed_order_command_probe(now_utc=now_utc)
    raise ValueError(f"unsupported command label: {label}")


def summarize_env() -> dict[str, str]:
    summary: dict[str, str] = {}
    for name in REQUIRED_ENV + SAFE_ID_ENV:
        if name in summary:
            continue
        value = os.environ.get(name, "").strip()
        if not value:
            summary[name] = "missing"
        elif any(marker in name.upper() for marker in SECRET_MARKERS):
            summary[name] = "configured_redacted"
        else:
            summary[name] = value
    return summary


def sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        clean = {}
        for key, item in value.items():
            key_text = str(key)
            if any(marker in key_text.upper() for marker in SECRET_MARKERS):
                clean[key_text] = "REDACTED"
            else:
                clean[key_text] = sanitize(item)
        return clean
    if isinstance(value, list):
        return [sanitize(item) for item in value[:20]]
    if isinstance(value, str) and len(value) > 160:
        return f"{value[:160]}..."
    return value


def _enabled() -> bool:
    return os.environ.get(ENABLE_ENV, "").strip() == "1"


def _require_enabled() -> None:
    if not _enabled():
        raise SystemExit(f"Set {ENABLE_ENV}=1 to run this paper-only smoke.")


def _read_int_env(name: str) -> int:
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return int(value)


def _read_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def run_smoke(*, command_label: str, dry_run: bool, polls: int, poll_seconds: int) -> dict[str, object]:
    _require_enabled()
    now = datetime.now(timezone.utc)
    command = build_command(command_label, now_utc=now)
    result: dict[str, object] = {
        "status": "dry_run" if dry_run else "running",
        "checked_at_utc": now.isoformat(),
        "paper_trading_only": True,
        "command_label": command_label,
        "environment": summarize_env(),
        "command_preview": sanitize(command),
    }
    if dry_run:
        return result

    project_id = _read_int_env("QC_PROJECT_ID")
    deploy_id = _read_env("QC_DEPLOY_ID")
    client = QCApiClient()

    result["command_api_success"] = client.create_live_command(
        project_id=project_id,
        command=command,
    )

    observations: list[dict[str, object]] = []
    for index in range(polls):
        if index:
            import time

            time.sleep(poll_seconds)
        logs = client.read_live_logs(project_id=project_id, deploy_id=deploy_id)
        orders = client.read_live_orders_page(
            project_id=project_id,
            deploy_id=deploy_id,
            start=0,
            end=20,
        )
        live_logs = logs.get("LiveLogs") or logs.get("logs") or []
        raw_orders = orders.get("orders") or []
        order_rows = list(raw_orders.values()) if isinstance(raw_orders, dict) else list(raw_orders)
        observations.append(
            {
                "poll": index,
                "live_log_count": len(live_logs) if isinstance(live_logs, list) else 0,
                "live_logs_tail": sanitize(live_logs[-10:] if isinstance(live_logs, list) else live_logs),
                "order_count": len(order_rows),
                "orders": sanitize(order_rows[:5]),
            }
        )
        if order_rows or any("MarketPilot command" in str(line) for line in live_logs):
            break

    result["observations"] = observations
    result["status"] = (
        "callback_or_order_observed"
        if any(obs.get("order_count") or obs.get("live_log_count") for obs in observations)
        else "api_accepted_no_callback_or_order_observed"
    )
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--command-label",
        choices=("marketpilot_signal", "typed_order_command_probe"),
        default="marketpilot_signal",
    )
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--polls", type=int, default=12)
    parser.add_argument("--poll-seconds", type=int, default=5)
    args = parser.parse_args(argv)

    output = run_smoke(
        command_label=args.command_label,
        dry_run=args.dry_run,
        polls=args.polls,
        poll_seconds=args.poll_seconds,
    )
    print(json.dumps(sanitize(output), indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
