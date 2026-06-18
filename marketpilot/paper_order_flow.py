from __future__ import annotations

"""Local simulated paper deployment and signal submission gates."""


import json
import os
import time
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from json import JSONDecodeError
from pathlib import Path
from typing import Any, Mapping, Sequence

from marketpilot.audit_journal import AppendOnlyJsonlAuditJournal, AuditJournalRecord
from marketpilot.constants import PAPER_TRADING_ONLY
from marketpilot.order_lifecycle import OrderIntent, OrderLifecycleState
from marketpilot.paper_command_models import (
    MarketPilotSignalCommand,
    SignalFreshnessPolicy,
    build_deployment_idempotency_key,
    parse_order_tag,
)
from marketpilot.qc_api import QCApiClient
from marketpilot.quantconnect_paper import QuantConnectPaperOrder
from marketpilot.sync import read_last_sync_record


SYNC_FRESHNESS_MAX_AGE_SECONDS = 600


@dataclass(frozen=True)
class PaperDeploymentResult:
    status: str
    idempotency_key: str
    api_called: bool
    response: Mapping[str, object] = field(default_factory=dict)
    reason: str | None = None


@dataclass(frozen=True)
class PaperSignalSubmissionResult:
    status: str
    idempotency_key: str
    command_delivered: bool
    order_executed: bool = False
    reason: str | None = None
    command_payload: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class SyncGateDecision:
    accepted: bool
    reason: str
    age_seconds: int | None = None
    record: Mapping[str, object] | None = None


@dataclass(frozen=True)
class QuantConnectOrderObservation:
    quantconnect_order_id: str
    symbol: str
    lifecycle_state: OrderLifecycleState | None
    raw_status: str
    quantity: int | None
    filled_quantity: int | None
    remaining_quantity: int | None
    average_fill_price: str | None
    submitted_at: datetime | None
    last_fill_at: datetime | None
    rejection_reason: str | None
    tag: str | None
    signal_id: str | None
    idempotency_key: str | None
    raw_payload: Mapping[str, object]
    parse_warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class QuantConnectOrderPollResult:
    observed_count: int
    audit_record_count: int
    warning_count: int
    observations: tuple[QuantConnectOrderObservation, ...]
    attempt_count: int = 1
    attempts: tuple[Mapping[str, object], ...] = ()
    status: str = "completed"
    reason: str | None = None


def deploy_paper_algorithm(
    *,
    project_id: int,
    compile_id: str,
    node_id: str,
    version_id: str,
    data_providers: Mapping[str, Mapping[str, object]],
    strategy_version: str,
    config_version: str,
    ledger_path: str | Path,
    client: QCApiClient | None = None,
) -> PaperDeploymentResult:
    """Deploy a paper algorithm once per deterministic deployment key."""

    _assert_paper_only()
    key = build_deployment_idempotency_key(
        project_id=project_id,
        compile_id=compile_id,
        node_id=node_id,
        version_id=version_id,
        data_providers=data_providers,
        strategy_version=strategy_version,
        config_version=config_version,
    )
    path = Path(ledger_path)
    if _ledger_contains(path, key):
        return PaperDeploymentResult(
            status="duplicate_deployment_rejected",
            idempotency_key=key,
            api_called=False,
            reason="duplicate_deployment_idempotency_key",
        )

    api_client = client or QCApiClient()
    response = api_client.create_live_algorithm(
        project_id=project_id,
        compile_id=compile_id,
        node_id=node_id,
        version_id=version_id,
        data_providers=data_providers,
    )
    _append_ledger_record(
        path,
        {
            "record_type": "paper_deployment",
            "idempotency_key": key,
            "project_id": project_id,
            "compile_id": compile_id,
            "node_id": node_id,
            "version_id": version_id,
            "strategy_version": strategy_version,
            "config_version": config_version,
            "paper_trading_only": True,
            "created_at_utc": _utc_iso(datetime.now(timezone.utc)),
        },
    )
    return PaperDeploymentResult(
        status="deployed",
        idempotency_key=key,
        api_called=True,
        response=dict(response),
    )


def parse_quantconnect_live_order(
    order: QuantConnectPaperOrder | Mapping[str, Any],
    *,
    order_key: object | None = None,
) -> QuantConnectOrderObservation:
    """Parse one authoritative QuantConnect live-order record.

    The parser preserves raw status and payload evidence. It does not infer fill
    quantities or prices when QuantConnect did not provide them.
    """

    raw_payload: Mapping[str, object]
    warnings: list[str] = []
    if isinstance(order, QuantConnectPaperOrder):
        raw_payload = order.raw_payload or {
            "quantconnect_order_id": order.quantconnect_order_id,
            "symbol": order.symbol,
            "status": order.status,
            "raw_status": order.raw_status,
            "quantity": order.quantity,
            "filled_quantity": order.filled_quantity,
            "remaining_quantity": order.remaining_quantity,
            "average_fill_price": order.average_fill_price,
            "submitted_at": order.submitted_at.isoformat(),
            "tag": order.tag,
            "rejection_reason": order.rejection_reason,
        }
        raw_status = order.raw_status or order.status
        tag = order.tag
        parsed_tag = parse_order_tag(tag) if tag else None
        signal_id = order.signal_id or (parsed_tag or {}).get("signal_id")
        idempotency_key = order.idempotency_key or (parsed_tag or {}).get("idempotency_key")
        filled_quantity = _order_int_field(
            raw_payload,
            "quantityFilled",
            "filledQuantity",
            "fillQuantity",
            "QuantityFilled",
            "filled_quantity",
            fallback=order.filled_quantity,
        )
        remaining_quantity = _order_int_field(
            raw_payload,
            "remainingQuantity",
            "quantityRemaining",
            "RemainingQuantity",
            "remaining_quantity",
            fallback=order.remaining_quantity,
        )
        return _build_order_observation(
            quantconnect_order_id=order.quantconnect_order_id,
            symbol=order.symbol,
            raw_status=raw_status,
            quantity=order.quantity,
            filled_quantity=filled_quantity,
            remaining_quantity=remaining_quantity,
            average_fill_price=order.average_fill_price,
            submitted_at=order.submitted_at,
            last_fill_at=_order_datetime_field(raw_payload, "lastFillTime", "LastFillTime", "filledAt", "filled_at"),
            rejection_reason=order.rejection_reason,
            tag=tag,
            signal_id=signal_id,
            idempotency_key=idempotency_key,
            raw_payload=raw_payload,
            warnings=warnings,
        )

    raw_payload = dict(order)
    tag = _order_string_field(raw_payload, "tag", "Tag", "orderTag", "OrderTag")
    parsed_tag = parse_order_tag(tag) if tag else None
    raw_status = _order_string_field(raw_payload, "status", "Status", "orderStatus", "OrderStatus") or "unknown"
    quantconnect_order_id = _order_string_field(
        raw_payload, "id", "orderId", "OrderId", "quantconnect_order_id"
    )
    if not quantconnect_order_id and order_key is not None:
        quantconnect_order_id = str(order_key)
    if not quantconnect_order_id:
        quantconnect_order_id = "UNKNOWN"
        warnings.append("missing_quantconnect_order_id")

    signal_id = (parsed_tag or {}).get("signal_id") or _order_string_field(raw_payload, "signal_id", "signalId")
    idempotency_key = (parsed_tag or {}).get("idempotency_key") or _order_string_field(
        raw_payload, "idempotency_key", "idempotencyKey"
    )
    return _build_order_observation(
        quantconnect_order_id=quantconnect_order_id,
        symbol=_order_symbol(raw_payload),
        raw_status=raw_status,
        quantity=_order_int_field(raw_payload, "quantity", "Quantity"),
        filled_quantity=_order_int_field(
            raw_payload, "quantityFilled", "filledQuantity", "fillQuantity", "QuantityFilled"
        ),
        remaining_quantity=_order_int_field(
            raw_payload, "remainingQuantity", "quantityRemaining", "RemainingQuantity"
        ),
        average_fill_price=_order_string_field(
            raw_payload, "averageFillPrice", "AverageFillPrice", "fillPrice", "price"
        ),
        submitted_at=_order_datetime_field(raw_payload, "createdTime", "CreatedTime", "time", "Time"),
        last_fill_at=_order_datetime_field(raw_payload, "lastFillTime", "LastFillTime", "filledAt"),
        rejection_reason=_order_string_field(
            raw_payload, "message", "Message", "rejectionReason", "RejectionReason"
        ),
        tag=tag,
        signal_id=signal_id,
        idempotency_key=idempotency_key,
        raw_payload=raw_payload,
        warnings=warnings,
    )


def parse_quantconnect_live_orders(
    orders: Mapping[str, Any] | Sequence[QuantConnectPaperOrder | Mapping[str, Any]],
) -> tuple[QuantConnectOrderObservation, ...]:
    """Parse a QuantConnect live-orders page or a typed order sequence."""

    if isinstance(orders, Mapping):
        raw_orders = orders.get("orders", orders)
        if isinstance(raw_orders, Mapping):
            return tuple(
                parse_quantconnect_live_order(raw_order, order_key=order_key)
                for order_key, raw_order in raw_orders.items()
                if isinstance(raw_order, (Mapping, QuantConnectPaperOrder))
            )
        if isinstance(raw_orders, Sequence) and not isinstance(raw_orders, (str, bytes)):
            return tuple(
                parse_quantconnect_live_order(raw_order)
                for raw_order in raw_orders
                if isinstance(raw_order, (Mapping, QuantConnectPaperOrder))
            )
        return ()

    return tuple(parse_quantconnect_live_order(raw_order) for raw_order in orders)


def poll_quantconnect_order_updates(
    *,
    project_id: int,
    deploy_id: str,
    audit_journal_path: str | Path,
    correlation_id: str,
    expected_signal_id: str | None = None,
    expected_idempotency_key: str | None = None,
    client: QCApiClient | None = None,
    observed_at_utc: datetime | None = None,
    max_attempts: int = 1,
    retry_sleep_seconds: float = 0.0,
) -> QuantConnectOrderPollResult:
    """Poll authoritative QuantConnect live orders and mirror evidence to JSONL."""

    _assert_paper_only()
    observed_at = _aware_utc(observed_at_utc or datetime.now(timezone.utc), "observed_at_utc")
    api_client = client or QCApiClient()
    attempts = _read_live_orders_with_bounded_retries(
        api_client,
        project_id=project_id,
        deploy_id=deploy_id,
        expected_signal_id=expected_signal_id,
        expected_idempotency_key=expected_idempotency_key,
        max_attempts=max_attempts,
        retry_sleep_seconds=retry_sleep_seconds,
    )
    observations = attempts[-1].get("observations", ()) if attempts else ()
    journal = AppendOnlyJsonlAuditJournal(audit_journal_path)

    audit_count = 0
    for observation in observations:
        _append_audit(
            journal,
            event_type=_audit_event_type_for_observation(observation),
            timestamp=observed_at,
            correlation_id=correlation_id,
            payload=_audit_payload_for_observation(
                observation,
                project_id=project_id,
                deploy_id=deploy_id,
                correlation_id=correlation_id,
                observed_at=observed_at,
            ),
        )
        audit_count += 1

    warning_count = sum(1 for observation in observations if observation.parse_warnings)
    reason = None
    status = "completed"
    if attempts and attempts[-1].get("status") == "api_error":
        status = "api_error"
        reason = str(attempts[-1].get("reason") or "api_error")
    elif not observations:
        status = "not_found"
        reason = "matching_order_not_found"
    return QuantConnectOrderPollResult(
        observed_count=len(observations),
        audit_record_count=audit_count,
        warning_count=warning_count,
        observations=observations,
        attempt_count=len(attempts),
        attempts=tuple(_sanitize_order_read_attempt(attempt) for attempt in attempts),
        status=status,
        reason=reason,
    )


def _read_live_orders_with_bounded_retries(
    api_client: QCApiClient,
    *,
    project_id: int,
    deploy_id: str,
    expected_signal_id: str | None,
    expected_idempotency_key: str | None,
    max_attempts: int,
    retry_sleep_seconds: float,
) -> list[dict[str, object]]:
    attempts: list[dict[str, object]] = []
    bounded_attempts = max(1, int(max_attempts or 1))
    sleep_seconds = max(0.0, float(retry_sleep_seconds or 0.0))
    for attempt_number in range(1, bounded_attempts + 1):
        observed_at = datetime.now(timezone.utc)
        try:
            raw_orders = api_client.read_live_orders(project_id=project_id, deploy_id=deploy_id)
            parsed = parse_quantconnect_live_orders(raw_orders)
            observations = _filter_expected_observations(
                parsed,
                expected_signal_id=expected_signal_id,
                expected_idempotency_key=expected_idempotency_key,
            )
            attempts.append(
                {
                    "attempt": attempt_number,
                    "status": "read",
                    "observed_at_utc": _utc_iso(observed_at),
                    "deploy_id_preview": _safe_deploy_id_preview(deploy_id),
                    "deploy_id_hash": _safe_deploy_id_hash(deploy_id),
                    "order_count": len(parsed),
                    "matching_order_count": len(observations),
                    "observations": observations,
                    "read_only": True,
                }
            )
            if observations:
                break
        except Exception as exc:
            attempts.append(
                {
                    "attempt": attempt_number,
                    "status": "api_error",
                    "observed_at_utc": _utc_iso(observed_at),
                    "deploy_id_preview": _safe_deploy_id_preview(deploy_id),
                    "deploy_id_hash": _safe_deploy_id_hash(deploy_id),
                    "order_count": 0,
                    "matching_order_count": 0,
                    "reason": type(exc).__name__,
                    "read_only": True,
                }
            )
            if attempt_number == bounded_attempts:
                break
        if attempt_number < bounded_attempts and sleep_seconds > 0:
            time.sleep(sleep_seconds)
    return attempts


def _sanitize_order_read_attempt(attempt: Mapping[str, object]) -> dict[str, object]:
    return {
        "attempt": attempt.get("attempt"),
        "status": attempt.get("status"),
        "observed_at_utc": attempt.get("observed_at_utc"),
        "deploy_id_preview": attempt.get("deploy_id_preview"),
        "deploy_id_hash": attempt.get("deploy_id_hash"),
        "order_count": attempt.get("order_count"),
        "matching_order_count": attempt.get("matching_order_count"),
        "reason": attempt.get("reason"),
        "read_only": True,
    }


def read_signal_order_fill_trace(
    *,
    audit_journal_path: str | Path,
    signal_id: str | None = None,
    idempotency_key: str | None = None,
) -> tuple[dict[str, object], ...]:
    """Read an ordered signal-to-order-to-fill chain from local audit evidence."""

    if not (signal_id or idempotency_key):
        raise ValueError("signal_id or idempotency_key is required.")
    records = AppendOnlyJsonlAuditJournal(audit_journal_path).read_records()
    filtered: list[dict[str, object]] = []
    for record in records:
        payload = record.get("payload", {})
        if not isinstance(payload, Mapping):
            continue
        signal_matches = signal_id is not None and payload.get("signal_id") == signal_id
        key_matches = idempotency_key is not None and payload.get("idempotency_key") == idempotency_key
        if signal_matches or key_matches:
            filtered.append(record)
    return tuple(sorted(filtered, key=lambda record: str(record.get("timestamp", ""))))


def submit_signal_command(
    *,
    project_id: int,
    deploy_id: str,
    intent: OrderIntent,
    correlation_id: str,
    signal_id: str,
    expires_at_utc: datetime,
    sync_jsonl_path: str | Path,
    ledger_path: str | Path,
    audit_journal_path: str | Path,
    client: QCApiClient | None = None,
    now_utc: datetime | None = None,
    sync_max_age_seconds: int = SYNC_FRESHNESS_MAX_AGE_SECONDS,
    freshness_policy: SignalFreshnessPolicy | None = None,
) -> PaperSignalSubmissionResult:
    """Deliver a validated signal command through QCApiClient only."""

    _assert_paper_only()
    now = _aware_utc(now_utc or datetime.now(timezone.utc), "now_utc")
    journal = AppendOnlyJsonlAuditJournal(audit_journal_path)

    command = MarketPilotSignalCommand.from_order_intent(
        intent,
        correlation_id=correlation_id,
        signal_id=signal_id,
        expires_at_utc=expires_at_utc,
    )
    payload = command.to_payload()
    idempotency_key = str(payload["idempotency_key"])

    sync_decision = evaluate_latest_sync_gate(
        sync_jsonl_path=sync_jsonl_path,
        now_utc=now,
        max_age_seconds=sync_max_age_seconds,
    )
    if not sync_decision.accepted:
        _append_audit(
            journal,
            event_type="paper_signal_sync_blocked",
            timestamp=now,
            correlation_id=correlation_id,
            payload={
                "reason": sync_decision.reason,
                "signal_id": signal_id,
                "idempotency_key": idempotency_key,
                "deploy_id": deploy_id,
                "command_delivered": False,
                "order_executed": False,
                "paper_trading_only": True,
            },
        )
        return PaperSignalSubmissionResult(
            status="sync_gate_blocked",
            idempotency_key=idempotency_key,
            command_delivered=False,
            reason=sync_decision.reason,
            command_payload=payload,
        )

    policy = freshness_policy or SignalFreshnessPolicy(ttl_seconds=600)
    freshness = policy.evaluate(
        signal_time_utc=intent.signal_time,
        expires_at_utc=expires_at_utc,
        now_utc=now,
    )
    if not freshness.accepted:
        _append_audit(
            journal,
            event_type="paper_signal_skipped",
            timestamp=now,
            correlation_id=correlation_id,
            payload={
                "reason": freshness.reason,
                "signal_id": signal_id,
                "idempotency_key": idempotency_key,
                "age_seconds": freshness.age_seconds,
                "command_delivered": False,
                "order_executed": False,
                "paper_trading_only": True,
            },
        )
        return PaperSignalSubmissionResult(
            status="signal_skipped",
            idempotency_key=idempotency_key,
            command_delivered=False,
            reason=freshness.reason,
            command_payload=payload,
        )

    path = Path(ledger_path)
    if _ledger_contains(path, idempotency_key):
        _append_audit(
            journal,
            event_type="paper_signal_duplicate_rejected",
            timestamp=now,
            correlation_id=correlation_id,
            payload={
                "reason": "duplicate_signal_idempotency_key",
                "signal_id": signal_id,
                "idempotency_key": idempotency_key,
                "command_delivered": False,
                "order_executed": False,
                "paper_trading_only": True,
            },
        )
        return PaperSignalSubmissionResult(
            status="duplicate_signal_rejected",
            idempotency_key=idempotency_key,
            command_delivered=False,
            reason="duplicate_signal_idempotency_key",
            command_payload=payload,
        )

    api_client = client or QCApiClient()
    transport = os.environ.get("MARKETPILOT_QC_SIGNAL_TRANSPORT", "command").strip().lower()
    if transport == "object_store":
        organization_id = os.environ.get("QC_ORGANIZATION_ID", "").strip()
        object_store_key = os.environ.get("MARKETPILOT_QC_OBJECT_STORE_SIGNAL_KEY", "").strip()
        if not organization_id or not object_store_key:
            delivered = False
        else:
            response = api_client.upload_object_store_file(
                organization_id=organization_id,
                project_id=project_id,
                key=object_store_key,
                content=json.dumps(payload, sort_keys=True).encode("utf-8"),
            )
            delivered = bool(response.get("success", False))
    else:
        delivered = bool(api_client.create_live_command(project_id=project_id, command=payload))
    _append_ledger_record(
        path,
        {
            "record_type": "paper_signal_command",
            "idempotency_key": idempotency_key,
            "signal_id": signal_id,
            "correlation_id": correlation_id,
            "project_id": project_id,
            "deploy_id": deploy_id,
            "command_delivered": delivered,
            "order_executed": False,
            "paper_trading_only": True,
            "created_at_utc": _utc_iso(now),
        },
    )
    event_type = "paper_signal_command_delivered" if delivered else "paper_signal_command_failed"
    _append_audit(
        journal,
        event_type=event_type,
        timestamp=now,
        correlation_id=correlation_id,
        payload={
            "signal_id": signal_id,
            "idempotency_key": idempotency_key,
            "project_id": project_id,
            "deploy_id": deploy_id,
            "command_delivered": delivered,
            "order_executed": False,
            "order_filled": False,
            "source_authority": "quantconnect",
            "transport": transport,
            "local_authority": False,
            "paper_trading_only": True,
        },
    )
    return PaperSignalSubmissionResult(
        status="command_delivered" if delivered else "command_delivery_failed",
        idempotency_key=idempotency_key,
        command_delivered=delivered,
        order_executed=False,
        reason=None if delivered else "command_delivery_failed",
        command_payload=payload,
    )


def evaluate_latest_sync_gate(
    *,
    sync_jsonl_path: str | Path,
    now_utc: datetime,
    max_age_seconds: int = SYNC_FRESHNESS_MAX_AGE_SECONDS,
) -> SyncGateDecision:
    """Validate the latest Phase 14 sync JSONL record before command delivery."""

    now = _aware_utc(now_utc, "now_utc")
    try:
        record = read_last_sync_record(Path(sync_jsonl_path))
    except (OSError, JSONDecodeError, ValueError):
        return SyncGateDecision(False, "invalid_sync_record_json")
    if record is None:
        return SyncGateDecision(False, "missing_sync_record")

    raw_timestamp = record.get("source_timestamp")
    if raw_timestamp is None:
        return SyncGateDecision(False, "missing_sync_source_timestamp", record=record)
    try:
        source_timestamp = _parse_utc_datetime(raw_timestamp)
    except ValueError as exc:
        return SyncGateDecision(False, str(exc), record=record)

    age_seconds = int((now - source_timestamp).total_seconds())
    if age_seconds < 0:
        return SyncGateDecision(False, "future_sync_source_timestamp", age_seconds=age_seconds, record=record)
    if age_seconds > max_age_seconds:
        return SyncGateDecision(False, "stale_sync_record", age_seconds=age_seconds, record=record)
    sync_status = str(record.get("sync_status", "")).strip()
    if sync_status != "success":
        return SyncGateDecision(False, f"sync_status_{sync_status or 'missing'}", age_seconds=age_seconds, record=record)
    if record.get("reconciliation_clean") is not True:
        return SyncGateDecision(False, "reconciliation_not_clean", age_seconds=age_seconds, record=record)
    return SyncGateDecision(True, "sync_fresh_clean", age_seconds=age_seconds, record=record)


def _ledger_contains(path: Path, idempotency_key: str) -> bool:
    if not path.exists():
        return False
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                record = json.loads(line)
                if record.get("idempotency_key") == idempotency_key:
                    return True
    except (OSError, JSONDecodeError) as exc:
        raise RuntimeError(f"idempotency ledger is unreadable: {path}") from exc
    return False


def _append_ledger_record(path: Path, record: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(dict(record), sort_keys=True) + "\n")


def _append_audit(
    journal: AppendOnlyJsonlAuditJournal,
    *,
    event_type: str,
    timestamp: datetime,
    correlation_id: str,
    payload: Mapping[str, object],
) -> None:
    journal.append(
        AuditJournalRecord(
            event_type=event_type,
            timestamp=timestamp,
            correlation_id=correlation_id,
            payload=payload,
        )
    )


def _build_order_observation(
    *,
    quantconnect_order_id: str,
    symbol: str,
    raw_status: str,
    quantity: int | None,
    filled_quantity: int | None,
    remaining_quantity: int | None,
    average_fill_price: str | None,
    submitted_at: datetime | None,
    last_fill_at: datetime | None,
    rejection_reason: str | None,
    tag: str | None,
    signal_id: str | None,
    idempotency_key: str | None,
    raw_payload: Mapping[str, object],
    warnings: list[str],
) -> QuantConnectOrderObservation:
    lifecycle_state = _map_qc_status(raw_status)
    if lifecycle_state is None:
        warnings.append("unknown_order_status")
    if lifecycle_state in {OrderLifecycleState.FILLED, OrderLifecycleState.PARTIALLY_FILLED}:
        if filled_quantity is None:
            warnings.append("missing_filled_quantity")
        if average_fill_price is None:
            warnings.append("missing_average_fill_price")
    if tag and not parse_order_tag(tag):
        warnings.append("unrecognized_marketpilot_order_tag")
    if not tag:
        warnings.append("missing_order_tag")
    return QuantConnectOrderObservation(
        quantconnect_order_id=str(quantconnect_order_id),
        symbol=symbol.strip().upper() if symbol else "UNKNOWN",
        lifecycle_state=lifecycle_state,
        raw_status=str(raw_status),
        quantity=quantity,
        filled_quantity=filled_quantity,
        remaining_quantity=remaining_quantity,
        average_fill_price=average_fill_price,
        submitted_at=submitted_at,
        last_fill_at=last_fill_at,
        rejection_reason=rejection_reason,
        tag=tag,
        signal_id=signal_id,
        idempotency_key=idempotency_key,
        raw_payload=dict(raw_payload),
        parse_warnings=tuple(dict.fromkeys(warnings)),
    )


def _audit_event_type_for_observation(observation: QuantConnectOrderObservation) -> str:
    if observation.lifecycle_state is OrderLifecycleState.REJECTED:
        return "paper_order_rejected"
    if (
        observation.lifecycle_state in {OrderLifecycleState.PARTIALLY_FILLED, OrderLifecycleState.FILLED}
        and observation.filled_quantity is not None
    ):
        return "paper_fill_observed"
    return "paper_order_observed"


def _audit_payload_for_observation(
    observation: QuantConnectOrderObservation,
    *,
    project_id: int,
    deploy_id: str,
    correlation_id: str,
    observed_at: datetime,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "source_authority": "quantconnect",
        "local_authority": False,
        "paper_trading_only": True,
        "correlation_id": correlation_id,
        "project_id": project_id,
        "deploy_id": deploy_id,
        "quantconnect_order_id": observation.quantconnect_order_id,
        "signal_id": observation.signal_id,
        "idempotency_key": observation.idempotency_key,
        "symbol": observation.symbol,
        "status": observation.lifecycle_state.value if observation.lifecycle_state else "unknown",
        "raw_status": observation.raw_status,
        "quantity": observation.quantity,
        "filled_quantity": observation.filled_quantity,
        "remaining_quantity": observation.remaining_quantity,
        "average_fill_price": observation.average_fill_price,
        "submitted_at_utc": _optional_utc_iso(observation.submitted_at),
        "last_fill_at_utc": _optional_utc_iso(observation.last_fill_at),
        "observed_at_utc": _utc_iso(observed_at),
        "rejection_reason": observation.rejection_reason,
        "tag": observation.tag,
        "parse_warnings": list(observation.parse_warnings),
        "raw_payload": dict(observation.raw_payload),
    }
    return payload


def _map_qc_status(raw_status: str) -> OrderLifecycleState | None:
    normalized = raw_status.strip().lower().replace("_", "").replace(" ", "")
    if normalized in {"0", "new", "1", "submitted", "submitpending", "updatesubmitted"}:
        return OrderLifecycleState.SUBMITTED
    if normalized in {"2", "partiallyfilled", "partialfill"}:
        return OrderLifecycleState.PARTIALLY_FILLED
    if normalized in {"3", "filled"}:
        return OrderLifecycleState.FILLED
    if normalized in {"5", "canceled", "cancelled", "cancelpending"}:
        return OrderLifecycleState.CANCELED
    if normalized in {"6", "invalid", "rejected", "reject", "brokeragerejected", "error"}:
        return OrderLifecycleState.REJECTED
    return None


def _filter_expected_observations(
    observations: tuple[QuantConnectOrderObservation, ...],
    *,
    expected_signal_id: str | None,
    expected_idempotency_key: str | None,
) -> tuple[QuantConnectOrderObservation, ...]:
    signal = (expected_signal_id or "").strip()
    key = (expected_idempotency_key or "").strip()
    if not signal and not key:
        return observations
    return tuple(
        observation
        for observation in observations
        if (signal and observation.signal_id == signal) or (key and observation.idempotency_key == key)
    )


def _order_string_field(payload: Mapping[str, object], *keys: str) -> str | None:
    for key in keys:
        value = payload.get(key)
        if value is not None and value != "":
            return str(value)
    return None


def _order_int_field(
    payload: Mapping[str, object],
    *keys: str,
    fallback: int | None = None,
) -> int | None:
    found = False
    value: object = None
    for key in keys:
        if key in payload:
            found = True
            value = payload[key]
            break
    if not found:
        return fallback
    if value is None or value == "":
        return None
    try:
        return int(Decimal(str(value)))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"invalid integer order field: {value!r}") from exc


def _order_datetime_field(payload: Mapping[str, object], *keys: str) -> datetime | None:
    value = _order_string_field(payload, *keys)
    if value is None:
        return None
    return _parse_utc_datetime(value)


def _order_symbol(payload: Mapping[str, object]) -> str:
    value = payload.get("symbol", payload.get("Symbol"))
    if isinstance(value, Mapping):
        return str(value.get("value", value.get("Value", "UNKNOWN")))
    if value is None:
        return "UNKNOWN"
    return str(value)


def _parse_utc_datetime(value: object) -> datetime:
    if not isinstance(value, str):
        raise ValueError("invalid_sync_source_timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid_sync_source_timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError("naive_sync_source_timestamp")
    return parsed.astimezone(timezone.utc)


def _aware_utc(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware.")
    return value.astimezone(timezone.utc)


def _utc_iso(value: datetime) -> str:
    return _aware_utc(value, "timestamp").isoformat()


def _optional_utc_iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return _utc_iso(value)


def _safe_deploy_id_preview(deploy_id: str) -> str:
    value = str(deploy_id or "").strip()
    if len(value) <= 12:
        return value
    return f"{value[:6]}...{value[-6:]}"


def _safe_deploy_id_hash(deploy_id: str) -> str:
    value = str(deploy_id or "").strip()
    if not value:
        return ""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def _assert_paper_only() -> None:
    if PAPER_TRADING_ONLY is not True:
        raise RuntimeError("PAPER_TRADING_ONLY must be True for paper order flow.")


__all__ = [
    "PaperDeploymentResult",
    "PaperSignalSubmissionResult",
    "QuantConnectOrderObservation",
    "QuantConnectOrderPollResult",
    "SyncGateDecision",
    "deploy_paper_algorithm",
    "evaluate_latest_sync_gate",
    "parse_quantconnect_live_order",
    "parse_quantconnect_live_orders",
    "poll_quantconnect_order_updates",
    "read_signal_order_fill_trace",
    "submit_signal_command",
]
