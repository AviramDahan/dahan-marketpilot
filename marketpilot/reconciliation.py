"""QuantConnect-authoritative Paper Trading reconciliation contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping

from marketpilot.notification_events import NotificationDomainEvent, event_for_system_incident
from marketpilot.order_lifecycle import OrderIntent, OrderLifecycleEvent
from marketpilot.quantconnect_paper import QuantConnectPaperFill, QuantConnectPaperSnapshot


class ReconciliationMismatchType(str, Enum):
    ORDER_ID = "order_id"
    ORDER_STATE = "order_state"
    FILL_DATA = "fill_data"
    LOCAL_AUDIT = "local_audit"
    CASH = "cash"
    HOLDINGS = "holdings"


@dataclass(frozen=True)
class ReconciliationMismatch:
    mismatch_type: ReconciliationMismatchType
    reason: str
    local_value: object | None = None
    quantconnect_value: object | None = None


@dataclass(frozen=True)
class ReconciliationDecision:
    authoritative_source: str
    block_new_entries: bool
    preserve_exits: bool
    requires_explicit_recovery: bool
    mismatches: tuple[ReconciliationMismatch, ...]
    correlation_id: str
    system_event: NotificationDomainEvent | None = None
    authoritative_order_ids: Mapping[str, str] = field(default_factory=dict)
    authoritative_fills: Mapping[str, QuantConnectPaperFill] = field(default_factory=dict)
    local_idempotency_keys: tuple[str, ...] = field(default_factory=tuple)


def reconcile_quantconnect_state(
    *,
    snapshot: QuantConnectPaperSnapshot,
    correlation_id: str,
    local_order_intents: tuple[OrderIntent, ...] = (),
    local_lifecycle_events: tuple[OrderLifecycleEvent, ...] = (),
    local_audit_records: tuple[Mapping[str, object], ...] = (),
) -> ReconciliationDecision:
    """Compare QC Paper state to local audit mirrors without mutating either side."""

    if snapshot.authoritative_source != "quantconnect":
        raise ValueError("reconciliation requires a QuantConnect-authoritative snapshot.")
    if not correlation_id.strip():
        raise ValueError("correlation_id is required for reconciliation decisions.")

    order_by_idempotency = {
        order.idempotency_key: order for order in snapshot.orders if order.idempotency_key
    }
    order_id_by_symbol = {order.symbol: order.quantconnect_order_id for order in snapshot.orders}
    fills_by_order_id = {fill.quantconnect_order_id: fill for fill in snapshot.fills}
    mismatches = list(_lifecycle_mismatches(local_lifecycle_events, order_by_idempotency))
    mismatches.extend(_fill_mismatches(snapshot))
    mismatches.extend(_audit_mismatches(local_audit_records))

    block_new_entries = bool(mismatches)
    system_event = None
    if block_new_entries:
        system_event = event_for_system_incident(
            correlation_id,
            {
                "authoritative_source": "quantconnect",
                "mismatch_types": tuple(mismatch.mismatch_type.value for mismatch in mismatches),
                "block_new_entries": True,
                "preserve_exits": True,
                "requires_explicit_recovery": True,
            },
            severity="high",
        )

    return ReconciliationDecision(
        authoritative_source="quantconnect",
        block_new_entries=block_new_entries,
        preserve_exits=True,
        requires_explicit_recovery=block_new_entries,
        mismatches=tuple(mismatches),
        correlation_id=correlation_id.strip(),
        system_event=system_event,
        authoritative_order_ids=order_id_by_symbol,
        authoritative_fills=fills_by_order_id,
        local_idempotency_keys=tuple(intent.idempotency_key for intent in local_order_intents),
    )


def _lifecycle_mismatches(
    local_lifecycle_events: tuple[OrderLifecycleEvent, ...],
    quantconnect_orders_by_idempotency: Mapping[str, object],
) -> tuple[ReconciliationMismatch, ...]:
    mismatches: list[ReconciliationMismatch] = []
    for event in local_lifecycle_events:
        qc_order = quantconnect_orders_by_idempotency.get(event.idempotency_key)
        if qc_order is None:
            continue
        local_order_id = event.payload.get("quantconnect_order_id")
        qc_order_id = getattr(qc_order, "quantconnect_order_id")
        if local_order_id and local_order_id != qc_order_id:
            mismatches.append(
                ReconciliationMismatch(
                    mismatch_type=ReconciliationMismatchType.ORDER_ID,
                    reason="local_quantconnect_order_id_differs_from_authoritative_snapshot",
                    local_value=local_order_id,
                    quantconnect_value=qc_order_id,
                )
            )
        qc_status = str(getattr(qc_order, "status"))
        if event.next_state.value != qc_status:
            mismatches.append(
                ReconciliationMismatch(
                    mismatch_type=ReconciliationMismatchType.ORDER_STATE,
                    reason="local_lifecycle_state_differs_from_authoritative_quantconnect_order_status",
                    local_value=event.next_state.value,
                    quantconnect_value=qc_status,
                )
            )
    return tuple(mismatches)


def _fill_mismatches(snapshot: QuantConnectPaperSnapshot) -> tuple[ReconciliationMismatch, ...]:
    order_ids = {order.quantconnect_order_id for order in snapshot.orders}
    return tuple(
        ReconciliationMismatch(
            mismatch_type=ReconciliationMismatchType.FILL_DATA,
            reason="quantconnect_fill_references_unknown_quantconnect_order",
            local_value=None,
            quantconnect_value=fill.quantconnect_order_id,
        )
        for fill in snapshot.fills
        if fill.quantconnect_order_id not in order_ids
    )


def _audit_mismatches(local_audit_records: tuple[Mapping[str, object], ...]) -> tuple[ReconciliationMismatch, ...]:
    return tuple(
        ReconciliationMismatch(
            mismatch_type=ReconciliationMismatchType.LOCAL_AUDIT,
            reason="local_audit_record_missing_correlation_id",
            local_value=record.get("event_type"),
            quantconnect_value="context_only",
        )
        for record in local_audit_records
        if not str(record.get("correlation_id", "")).strip()
    )
