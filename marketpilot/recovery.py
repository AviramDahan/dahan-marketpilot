"""Restart recovery and corporate-action placeholder contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Mapping


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
