"""Read-only off-hours preflight for Phase 16.2 UAT-01."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from marketpilot.qc_api import QCApiClient
from marketpilot.quantconnect_paper import QuantConnectAlgorithmStatus, QuantConnectDeploymentStatus
from marketpilot.telegram import load_telegram_config
from scripts.phase16_2_observe_deployed_session import DEFAULT_DASHBOARD_URL, observe_deployed_session


REQUIRED_ENV_GROUPS = (
    ("QUANTCONNECT_USER_ID",),
    ("QUANTCONNECT_API_TOKEN",),
    ("QC_PROJECT_ID", "QUANTCONNECT_PROJECT_ID"),
    ("QC_DEPLOY_ID", "QUANTCONNECT_LIVE_DEPLOY_ID"),
    ("TELEGRAM_BOT_TOKEN",),
    ("TELEGRAM_CHAT_ID",),
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run read-only UAT-01 deployed preflight checks.")
    parser.add_argument("--dashboard-url", default=os.environ.get("DASHBOARD_HEALTH_URL", DEFAULT_DASHBOARD_URL))
    parser.add_argument("--heartbeat-url", default=os.environ.get("HEARTBEAT_HEALTH_URL"))
    parser.add_argument("--shared-state-url", default=os.environ.get("DASHBOARD_STATE_HEALTH_URL"))
    parser.add_argument("--heartbeat-path", default=os.environ.get("SCHEDULER_HEARTBEAT_PATH", "data/scheduler_heartbeat.jsonl"))
    parser.add_argument("--max-heartbeat-age-seconds", type=int, default=900)
    parser.add_argument("--timeout-seconds", type=int, default=10)
    args = parser.parse_args(argv)

    result = run_preflight(
        env=os.environ,
        dashboard_url=args.dashboard_url,
        heartbeat_url=args.heartbeat_url,
        shared_state_url=args.shared_state_url,
        heartbeat_path=Path(args.heartbeat_path),
        max_heartbeat_age_seconds=args.max_heartbeat_age_seconds,
        timeout_seconds=args.timeout_seconds,
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "passed" else 2


def run_preflight(
    *,
    env: Mapping[str, str],
    dashboard_url: str | None,
    heartbeat_url: str | None,
    shared_state_url: str | None,
    heartbeat_path: Path,
    max_heartbeat_age_seconds: int,
    timeout_seconds: int,
) -> dict[str, object]:
    checks: dict[str, object] = {
        "environment": _check_environment(env),
        "operator_probe_disabled": _check_operator_probe_disabled(env),
        "telegram_configuration": _check_telegram_configuration(env),
        "deployment": _check_quantconnect_deployment(env),
        "deployed_observer": observe_deployed_session(
            dashboard_url=dashboard_url,
            heartbeat_path=heartbeat_path,
            heartbeat_url=heartbeat_url,
            shared_state_url=shared_state_url,
            max_heartbeat_age_seconds=max_heartbeat_age_seconds,
            require_shared_state=True,
            require_heartbeat=True,
            timeout_seconds=timeout_seconds,
        ),
    }
    status = "passed" if all(_check_passed(value) for value in checks.values()) else "blocked_external_not_verified"
    return {
        "status": status,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "paper_trading_only": True,
        "read_only": True,
        "controls_orders": False,
        "controls_scheduler": False,
        "controls_recovery": False,
        "operator_probe_enabled": False,
        "checks": checks,
    }


def _check_environment(env: Mapping[str, str]) -> dict[str, object]:
    present = {"|".join(group): _env_group_value(env, group) is not None for group in REQUIRED_ENV_GROUPS}
    missing = [name for name, exists in present.items() if not exists]
    return {
        "status": "passed" if not missing else "missing_required_env",
        "present": present,
        "missing": missing,
        "values_printed": False,
    }


def _check_operator_probe_disabled(env: Mapping[str, str]) -> dict[str, object]:
    input_kind = str(env.get("MARKETPILOT_RUNTIME_INPUT_KIND") or "none").strip().lower()
    probe_enabled = str(env.get("MARKETPILOT_OPERATOR_PAPER_PROBE_ENABLED") or "false").strip().lower()
    disabled = input_kind in {"", "none"} and probe_enabled in {"", "0", "false", "no", "off"}
    return {
        "status": "passed" if disabled else "temporary_uat_configuration_present",
        "runtime_input_kind": input_kind or "none",
        "operator_probe_enabled": probe_enabled in {"1", "true", "yes", "on"},
        "restore_runtime_input_kind": "none",
        "restore_operator_probe_enabled": "false",
    }


def _check_telegram_configuration(env: Mapping[str, str]) -> dict[str, object]:
    try:
        config = load_telegram_config(env=env)
    except (FileNotFoundError, ValueError) as exc:
        return {"status": "failed", "reason": type(exc).__name__, "values_printed": False}
    return {
        "status": "passed" if config.can_deliver else "not_configured",
        "enabled": config.telegram_enabled,
        "can_deliver": config.can_deliver,
        "values_printed": False,
    }


def _check_quantconnect_deployment(env: Mapping[str, str]) -> dict[str, object]:
    try:
        project_id = int(str(_env_group_value(env, ("QC_PROJECT_ID", "QUANTCONNECT_PROJECT_ID")) or "").strip())
        deploy_id = str(_env_group_value(env, ("QC_DEPLOY_ID", "QUANTCONNECT_LIVE_DEPLOY_ID")) or "").strip()
        if not deploy_id:
            raise ValueError("QC_DEPLOY_ID_missing")
        snapshot = QCApiClient().read_live_algorithm(project_id=project_id, deploy_id=deploy_id)
        orders = QCApiClient().read_live_orders(project_id=project_id, deploy_id=deploy_id)
    except Exception as exc:
        return {
            "status": "failed",
            "reason": type(exc).__name__,
            "detail": _safe_detail(str(exc)),
            "values_printed": False,
        }
    running = (
        snapshot.deployment_status is QuantConnectDeploymentStatus.RUNNING
        or snapshot.algorithm_status is QuantConnectAlgorithmStatus.RUNNING
    )
    positive_cash_equity = snapshot.cash > 0 and snapshot.portfolio_equity > 0
    open_orders = [order for order in orders if str(order.status).lower() not in {"filled", "canceled", "cancelled", "invalid", "rejected"}]
    return {
        "status": "passed" if running and positive_cash_equity and not open_orders else "blocked_external_not_verified",
        "deployment_status": snapshot.deployment_status.value,
        "algorithm_status": snapshot.algorithm_status.value,
        "cash_positive": snapshot.cash > 0,
        "equity_positive": snapshot.portfolio_equity > 0,
        "holdings_count": len(snapshot.holdings),
        "orders_count": len(orders),
        "open_order_count": len(open_orders),
        "unintended_duplicate_order_check": "passed" if not open_orders else "open_orders_present",
        "values_printed": False,
    }


def _check_passed(value: object) -> bool:
    return isinstance(value, Mapping) and value.get("status") == "passed"


def _env_group_value(env: Mapping[str, str], names: tuple[str, ...]) -> str | None:
    for name in names:
        value = str(env.get(name) or "").strip()
        if value:
            return value
    return None


def _safe_detail(value: str) -> str:
    words = ("token", "secret", "password", "credential", "api")
    redacted = value
    for word in words:
        redacted = redacted.replace(word, "[redacted]")
        redacted = redacted.replace(word.upper(), "[redacted]")
    return redacted[:300]


if __name__ == "__main__":
    raise SystemExit(main())
