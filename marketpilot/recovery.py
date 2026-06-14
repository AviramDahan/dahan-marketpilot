"""Restart recovery and corporate-action placeholder contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Mapping

from marketpilot.quantconnect_paper import QuantConnectPaperSnapshot, QuantConnectPaperStatusCode


class RecoveryMismatch(str, Enum):
    ORDER_STATE = "order_state"
    FILLS = "fills"
    HOLDINGS = "holdings"
    CASH = "cash"
    OPEN_POSITIONS = "open_positions"


class CorporateActionType(str, Enum):
    SPLIT = "split"
    DELISTING = "delisting"
    UNSUPPORTED = "unsupported_corporate_action"


class QuantConnectRecoveryStatus(str, Enum):
    RECOVERED = "recovered"
    NOT_CONFIGURED = "not_configured"
    NOT_RUN = "not_run"
    RECOVERY_REQUIRED = "recovery_required"


@dataclass(frozen=True)
class RecoveryDecision:
    quantconnect_wins: bool
    mismatches: tuple[RecoveryMismatch, ...]
    local_state_marked_mismatched: bool
    event_type: str = "recovery_mismatch"
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    payload: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class CorporateActionPlaceholder:
    symbol: str
    action_type: CorporateActionType
    safe_state: str = "recovery_required"
    full_execution_deferred: bool = True


@dataclass(frozen=True)
class QuantConnectRestartRecoveryDecision:
    status: QuantConnectRecoveryStatus
    authoritative_source: str
    block_new_entries: bool
    requires_explicit_recovery: bool
    preserve_exits: bool
    reconstructed_positions: Mapping[str, int]
    reconstructed_order_ids: tuple[str, ...]
    reconstructed_fill_count: int
    attached_local_audit_count: int
    local_audit_context_only: bool
    correlation_id: str
    recovery_required_reasons: tuple[str, ...] = field(default_factory=tuple)


def reconcile_restart_state(
    *,
    local_state: Mapping[str, object],
    quantconnect_snapshot: Mapping[str, object],
) -> RecoveryDecision:
    checks = {
        RecoveryMismatch.ORDER_STATE: "order_state",
        RecoveryMismatch.FILLS: "fills",
        RecoveryMismatch.HOLDINGS: "holdings",
        RecoveryMismatch.CASH: "cash",
        RecoveryMismatch.OPEN_POSITIONS: "open_positions",
    }
    mismatches = tuple(reason for reason, key in checks.items() if local_state.get(key) != quantconnect_snapshot.get(key))
    return RecoveryDecision(
        quantconnect_wins=True,
        mismatches=mismatches,
        local_state_marked_mismatched=bool(mismatches),
        payload={
            "authoritative_source": "quantconnect",
            "mismatch_count": len(mismatches),
        },
    )


def corporate_action_placeholder(symbol: str, action_type: CorporateActionType | str) -> CorporateActionPlaceholder:
    return CorporateActionPlaceholder(
        symbol=symbol.strip().upper(),
        action_type=action_type if isinstance(action_type, CorporateActionType) else CorporateActionType(str(action_type)),
    )


def recover_from_quantconnect_snapshot(
    *,
    snapshot: QuantConnectPaperSnapshot | None,
    local_audit_records: tuple[Mapping[str, object], ...],
    correlation_id: str,
    unavailable_status: QuantConnectPaperStatusCode | None = None,
) -> QuantConnectRestartRecoveryDecision:
    if not correlation_id.strip():
        raise ValueError("correlation_id is required for restart recovery.")

    audit_count = len(local_audit_records)
    if snapshot is None:
        status = _status_from_unavailable(unavailable_status)
        return QuantConnectRestartRecoveryDecision(
            status=status,
            authoritative_source="quantconnect_unavailable",
            block_new_entries=True,
            requires_explicit_recovery=True,
            preserve_exits=True,
            reconstructed_positions={},
            reconstructed_order_ids=(),
            reconstructed_fill_count=0,
            attached_local_audit_count=audit_count,
            local_audit_context_only=True,
            correlation_id=correlation_id.strip(),
            recovery_required_reasons=(
                "quantconnect_snapshot_unavailable",
                "local_audit_cannot_become_authoritative",
            ),
        )

    positions = {holding.symbol: holding.quantity for holding in snapshot.holdings if holding.quantity != 0}
    order_ids = tuple(order.quantconnect_order_id for order in snapshot.orders)
    return QuantConnectRestartRecoveryDecision(
        status=QuantConnectRecoveryStatus.RECOVERED,
        authoritative_source="quantconnect",
        block_new_entries=False,
        requires_explicit_recovery=False,
        preserve_exits=True,
        reconstructed_positions=positions,
        reconstructed_order_ids=order_ids,
        reconstructed_fill_count=len(snapshot.fills),
        attached_local_audit_count=audit_count,
        local_audit_context_only=True,
        correlation_id=correlation_id.strip(),
    )


def _status_from_unavailable(status: QuantConnectPaperStatusCode | None) -> QuantConnectRecoveryStatus:
    if status is QuantConnectPaperStatusCode.NOT_CONFIGURED:
        return QuantConnectRecoveryStatus.NOT_CONFIGURED
    if status is QuantConnectPaperStatusCode.NOT_RUN:
        return QuantConnectRecoveryStatus.NOT_RUN
    return QuantConnectRecoveryStatus.RECOVERY_REQUIRED
