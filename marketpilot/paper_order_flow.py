"""Local simulated paper deployment and signal submission gates."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from json import JSONDecodeError
from pathlib import Path
from typing import Mapping

from marketpilot.audit_journal import AppendOnlyJsonlAuditJournal, AuditJournalRecord
from marketpilot.constants import PAPER_TRADING_ONLY
from marketpilot.order_lifecycle import OrderIntent
from marketpilot.paper_command_models import (
    MarketPilotSignalCommand,
    SignalFreshnessPolicy,
    build_deployment_idempotency_key,
)
from marketpilot.qc_api import QCApiClient
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


def _assert_paper_only() -> None:
    if PAPER_TRADING_ONLY is not True:
        raise RuntimeError("PAPER_TRADING_ONLY must be True for paper order flow.")


__all__ = [
    "PaperDeploymentResult",
    "PaperSignalSubmissionResult",
    "SyncGateDecision",
    "deploy_paper_algorithm",
    "evaluate_latest_sync_gate",
    "submit_signal_command",
]
