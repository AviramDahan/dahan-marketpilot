"""Read-only off-hours preflight for Phase 16.2 UAT-01."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping

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
    deployed_observer = observe_deployed_session(
        dashboard_url=dashboard_url,
        heartbeat_path=heartbeat_path,
        heartbeat_url=heartbeat_url,
        shared_state_url=shared_state_url,
        max_heartbeat_age_seconds=max_heartbeat_age_seconds,
        require_shared_state=True,
        require_heartbeat=True,
        timeout_seconds=timeout_seconds,
    )
    observer_checks = deployed_observer.get("checks") if isinstance(deployed_observer, Mapping) else {}
    shared_state = observer_checks.get("shared_state") if isinstance(observer_checks, Mapping) else {}
    checks: dict[str, object] = {
        "environment": _check_environment(env),
        "operator_probe_disabled": _check_operator_probe_disabled(env),
        "telegram_configuration": _check_telegram_configuration(env),
        "deployment": _check_quantconnect_deployment(env),
        "identity_diagnostics": _check_identity_diagnostics(env, deployed_observer),
        "deployed_observer": deployed_observer,
        "reconciliation": _check_reconciliation(shared_state if isinstance(shared_state, Mapping) else {}, max_age_seconds=max_heartbeat_age_seconds),
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
        client = QCApiClient()
        snapshot = client.read_live_algorithm(project_id=project_id, deploy_id=deploy_id)
        orders = client.read_live_orders(project_id=project_id, deploy_id=deploy_id)
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
    open_orders = [order for order in orders if _is_open_order_status(getattr(order, "status", ""))]
    order_readiness = evaluate_probe_order_readiness(
        orders,
        correlation_id=str(env.get("MARKETPILOT_UAT_CORRELATION_ID") or "").strip() or None,
        expected_order_tag=str(env.get("MARKETPILOT_EXPECTED_ORDER_TAG") or "").strip() or None,
        idempotency_key=str(env.get("MARKETPILOT_UAT_IDEMPOTENCY_KEY") or "").strip() or None,
        symbol=str(env.get("MARKETPILOT_OPERATOR_PAPER_PROBE_SYMBOL") or "").strip().upper() or None,
        side=str(env.get("MARKETPILOT_OPERATOR_PAPER_PROBE_SIDE") or "buy").strip().lower() or None,
    )
    return {
        "status": "passed" if running and positive_cash_equity and order_readiness["readiness_decision"] == "passed" else "blocked_external_not_verified",
        "deployment_status": snapshot.deployment_status.value,
        "algorithm_status": snapshot.algorithm_status.value,
        "cash_positive": snapshot.cash > 0,
        "equity_positive": snapshot.portfolio_equity > 0,
        "holdings_count": len(snapshot.holdings),
        "orders_count": len(orders),
        "open_order_count": len(open_orders),
        "order_readiness": order_readiness,
        "values_printed": False,
    }


def _check_identity_diagnostics(env: Mapping[str, str], deployed_observer: Mapping[str, object]) -> dict[str, object]:
    project_source = _env_group_source(env, ("QC_PROJECT_ID", "QUANTCONNECT_PROJECT_ID"))
    deploy_source = _env_group_source(env, ("QC_DEPLOY_ID", "QUANTCONNECT_LIVE_DEPLOY_ID"))
    project_present = project_source is not None
    deploy_id = str(_env_group_value(env, ("QC_DEPLOY_ID", "QUANTCONNECT_LIVE_DEPLOY_ID")) or "").strip()
    observer_checks = deployed_observer.get("checks") if isinstance(deployed_observer, Mapping) else {}
    heartbeat = observer_checks.get("heartbeat") if isinstance(observer_checks, Mapping) else {}
    shared_state = observer_checks.get("shared_state") if isinstance(observer_checks, Mapping) else {}
    deployment_read_shape: dict[str, object] = {"status": "not_run"}
    order_read_shape: dict[str, object] = {"status": "not_run"}
    if project_present and deploy_id:
        try:
            project_id = int(str(_env_group_value(env, ("QC_PROJECT_ID", "QUANTCONNECT_PROJECT_ID")) or "").strip())
            client = QCApiClient()
            snapshot = client.read_live_algorithm(project_id=project_id, deploy_id=deploy_id)
            deployment_read_shape = {
                "status": "read",
                "deployment_status": snapshot.deployment_status.value,
                "algorithm_status": snapshot.algorithm_status.value,
                "orders_count": len(snapshot.orders),
                "fills_count": len(snapshot.fills),
            }
            orders = client.read_live_orders(project_id=project_id, deploy_id=deploy_id)
            order_read_shape = {
                "status": "read",
                "order_count": len(orders),
                "filled_count": sum(1 for order in orders if str(getattr(order, "status", "")).lower() == "filled"),
                "raw_payload_exposed": False,
            }
        except Exception as exc:
            order_read_shape = {
                "status": "read_failed",
                "reason": type(exc).__name__,
                "raw_payload_exposed": False,
            }
    return {
        "status": "passed" if project_present and deploy_id else "missing_identity",
        "project_id_present": project_present,
        "project_id_source": project_source,
        "deploy_id_source": deploy_source,
        "deploy_id_preview": _safe_deploy_id_preview(deploy_id),
        "deploy_id_hash": _safe_hash(deploy_id),
        "deployment_read_shape": deployment_read_shape,
        "order_read_shape": order_read_shape,
        "market_window_status": heartbeat.get("market_window_status") if isinstance(heartbeat, Mapping) else None,
        "heartbeat_source_timestamp": heartbeat.get("latest_heartbeat_at") if isinstance(heartbeat, Mapping) else None,
        "shared_state_source_timestamp": shared_state.get("source_timestamp") if isinstance(shared_state, Mapping) else None,
        "deploy_id_rotation_possible": True,
        "values_printed": False,
        "read_only": True,
    }


def _check_reconciliation(shared_state: Mapping[str, object], *, max_age_seconds: int) -> dict[str, object]:
    sync_status = str(shared_state.get("sync_status") or "").strip()
    source = str(shared_state.get("source") or "").strip().lower()
    source_timestamp_text = str(shared_state.get("source_timestamp") or "").strip()
    freshness_level = str(shared_state.get("freshness_level") or "").strip().lower() or None
    source_timestamp = _parse_timezone_aware(source_timestamp_text)
    age_seconds = None
    if source_timestamp is not None:
        age_seconds = max(0, int((datetime.now(timezone.utc) - source_timestamp).total_seconds()))
    fresh_enough = age_seconds is not None and age_seconds <= max_age_seconds and freshness_level in {"fresh", "ok", None}
    passed = (
        sync_status == "success"
        and shared_state.get("reconciliation_clean") is True
        and source == "quantconnect"
        and source_timestamp is not None
        and fresh_enough
    )
    return {
        "status": "passed" if passed else "blocked_external_not_verified",
        "sync_status": sync_status or None,
        "reconciliation_clean": shared_state.get("reconciliation_clean") is True,
        "source": source or None,
        "source_timestamp": source_timestamp.astimezone(timezone.utc).isoformat() if source_timestamp else None,
        "freshness_level": freshness_level,
        "age_seconds": age_seconds,
        "generation": _safe_int(shared_state.get("generation")),
        "fresh_enough_for_market_gate": fresh_enough,
        "values_printed": False,
    }


def evaluate_probe_order_readiness(
    orders: Iterable[object],
    *,
    correlation_id: str | None,
    expected_order_tag: str | None,
    idempotency_key: str | None,
    symbol: str | None,
    side: str | None,
) -> dict[str, object]:
    total_open = 0
    matching_probe = 0
    duplicate = 0
    leftover = 0
    ambiguous = 0
    for order in orders:
        if not _is_open_order_status(getattr(order, "status", "")):
            continue
        total_open += 1
        order_tag = str(getattr(order, "tag", "") or "")
        order_idempotency_key = str(getattr(order, "idempotency_key", "") or "")
        order_signal_id = str(getattr(order, "signal_id", "") or "")
        order_symbol = str(getattr(order, "symbol", "") or "").upper()
        order_side = _order_side(order)
        metadata_known = bool(order_tag or order_idempotency_key or order_signal_id)
        matches_correlation = bool(correlation_id and correlation_id in {order_idempotency_key, order_signal_id})
        matches_tag = bool(expected_order_tag and order_tag == expected_order_tag)
        matches_idempotency = bool(idempotency_key and order_idempotency_key == idempotency_key)
        symbol_side_match = bool(symbol and order_symbol == symbol.upper() and side and order_side == side)
        is_probe_leftover = "operator" in order_tag.lower() or "probe" in order_tag.lower() or "operator" in order_idempotency_key.lower() or "probe" in order_idempotency_key.lower()
        if matches_correlation or matches_tag or matches_idempotency:
            matching_probe += 1
        if symbol_side_match and is_probe_leftover:
            duplicate += 1
        if is_probe_leftover and not (matches_correlation or matches_tag or matches_idempotency):
            leftover += 1
        if symbol_side_match and not metadata_known:
            ambiguous += 1
    readiness = "passed" if matching_probe == 0 and duplicate == 0 and leftover == 0 and ambiguous == 0 else "blocked"
    return {
        "total_open_order_count": total_open,
        "matching_probe_order_count": matching_probe,
        "duplicate_order_status": "passed" if duplicate == 0 else "blocked",
        "duplicate_symbol_side_count": duplicate,
        "leftover_probe_status": "passed" if leftover == 0 else "blocked",
        "leftover_probe_count": leftover,
        "ambiguous_order_count": ambiguous,
        "readiness_decision": readiness,
        "raw_orders_exposed": False,
    }


def _check_passed(value: object) -> bool:
    return isinstance(value, Mapping) and value.get("status") == "passed"


def _is_open_order_status(status: object) -> bool:
    return str(status or "").strip().lower() not in {"filled", "canceled", "cancelled", "invalid", "rejected", "closed"}


def _order_side(order: object) -> str | None:
    quantity = getattr(order, "quantity", None)
    try:
        parsed = float(str(quantity))
    except (TypeError, ValueError):
        return None
    if parsed > 0:
        return "buy"
    if parsed < 0:
        return "sell"
    return None


def _env_group_value(env: Mapping[str, str], names: tuple[str, ...]) -> str | None:
    for name in names:
        value = str(env.get(name) or "").strip()
        if value:
            return value
    return None


def _env_group_source(env: Mapping[str, str], names: tuple[str, ...]) -> str | None:
    for name in names:
        value = str(env.get(name) or "").strip()
        if value:
            return name
    return None


def _safe_deploy_id_preview(deploy_id: str) -> str:
    value = str(deploy_id or "").strip()
    if len(value) <= 12:
        return value
    return f"{value[:6]}...{value[-6:]}"


def _safe_hash(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def _safe_detail(value: str) -> str:
    words = ("token", "secret", "password", "credential", "api")
    redacted = value
    for word in words:
        redacted = redacted.replace(word, "[redacted]")
        redacted = redacted.replace(word.upper(), "[redacted]")
    return redacted[:300]


def _parse_timezone_aware(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed.astimezone(timezone.utc)


def _safe_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None


if __name__ == "__main__":
    raise SystemExit(main())
