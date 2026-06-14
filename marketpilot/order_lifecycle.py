"""Paper-only order intent and lifecycle audit models."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Mapping


class OrderLifecycleState(str, Enum):
    PLANNED = "planned"
    SUBMITTED = "submitted"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    REJECTED = "rejected"
    CANCELED = "canceled"
    PROTECTIVE_ORDERS_PENDING = "protective_orders_pending"
    OPEN = "open"
    PARTIALLY_CLOSED = "partially_closed"
    CLOSED = "closed"


TERMINAL_STATES = {
    OrderLifecycleState.REJECTED,
    OrderLifecycleState.CANCELED,
    OrderLifecycleState.CLOSED,
}


ALLOWED_TRANSITIONS: Mapping[OrderLifecycleState, set[OrderLifecycleState]] = {
    OrderLifecycleState.PLANNED: {
        OrderLifecycleState.SUBMITTED,
        OrderLifecycleState.REJECTED,
        OrderLifecycleState.CANCELED,
    },
    OrderLifecycleState.SUBMITTED: {
        OrderLifecycleState.PARTIALLY_FILLED,
        OrderLifecycleState.FILLED,
        OrderLifecycleState.REJECTED,
        OrderLifecycleState.CANCELED,
    },
    OrderLifecycleState.PARTIALLY_FILLED: {
        OrderLifecycleState.FILLED,
        OrderLifecycleState.CANCELED,
    },
    OrderLifecycleState.FILLED: {OrderLifecycleState.PROTECTIVE_ORDERS_PENDING},
    OrderLifecycleState.PROTECTIVE_ORDERS_PENDING: {OrderLifecycleState.OPEN, OrderLifecycleState.CLOSED},
    OrderLifecycleState.OPEN: {OrderLifecycleState.PARTIALLY_CLOSED, OrderLifecycleState.CLOSED},
    OrderLifecycleState.PARTIALLY_CLOSED: {OrderLifecycleState.CLOSED},
    OrderLifecycleState.REJECTED: set(),
    OrderLifecycleState.CANCELED: set(),
    OrderLifecycleState.CLOSED: set(),
}


@dataclass(frozen=True)
class OrderIntent:
    idempotency_key: str
    symbol: str
    primary_setup: str
    strategy_mode: str
    signal_time: datetime
    portfolio_epoch: str
    quantity: int
    entry_price: Decimal
    risk_decision_id: str | None = None
    stop_price: Decimal | None = None
    target_price: Decimal | None = None
    audit_metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class OrderLifecycleEvent:
    idempotency_key: str
    previous_state: OrderLifecycleState
    next_state: OrderLifecycleState
    timestamp: datetime
    reason: str
    source: str = "local_audit_mirror"
    payload: Mapping[str, object] = field(default_factory=dict)


def make_order_idempotency_key(
    *,
    symbol: str,
    strategy_mode: str,
    primary_setup: str,
    signal_time: datetime,
    portfolio_epoch: str,
) -> str:
    normalized = "|".join(
        (
            symbol.strip().upper(),
            strategy_mode.strip().lower(),
            primary_setup.strip().lower(),
            signal_time.astimezone(timezone.utc).isoformat(),
            portfolio_epoch.strip().lower(),
        )
    )
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:24]
    return f"order-intent-{digest}"


def transition_order_state(
    *,
    idempotency_key: str,
    previous_state: OrderLifecycleState | str,
    next_state: OrderLifecycleState | str,
    reason: str,
    timestamp: datetime | None = None,
    source: str = "local_audit_mirror",
    payload: Mapping[str, object] | None = None,
) -> OrderLifecycleEvent:
    previous = _state(previous_state)
    next_ = _state(next_state)
    if next_ not in ALLOWED_TRANSITIONS[previous]:
        raise ValueError(f"cannot transition order lifecycle from {previous.value} to {next_.value}.")
    if not idempotency_key.strip():
        raise ValueError("idempotency_key is required.")
    return OrderLifecycleEvent(
        idempotency_key=idempotency_key.strip(),
        previous_state=previous,
        next_state=next_,
        timestamp=timestamp or datetime.now(timezone.utc),
        reason=reason.strip() or "unspecified",
        source=source.strip() or "local_audit_mirror",
        payload=_sanitize_payload(payload or {}),
    )


def _state(value: OrderLifecycleState | str) -> OrderLifecycleState:
    return value if isinstance(value, OrderLifecycleState) else OrderLifecycleState(str(value))


def _sanitize_payload(payload: Mapping[str, object]) -> dict[str, object]:
    sanitized: dict[str, object] = {}
    for key, value in payload.items():
        lowered = key.lower()
        if any(marker in lowered for marker in ("secret", "token", "password", "credential", "api_key")):
            sanitized[key] = "[redacted]"
        else:
            sanitized[key] = value
    return sanitized
