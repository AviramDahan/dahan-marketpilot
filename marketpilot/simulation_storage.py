from __future__ import annotations

"""Append-only JSONL storage for internal simulation state."""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Mapping

from marketpilot.internal_paper_simulator import (
    SimulatedClosedTrade,
    SimulatedExitReason,
    SimulatedPortfolio,
    SimulatedPosition,
    close_simulated_position,
    initial_simulated_portfolio,
    open_simulated_position,
)
from marketpilot.risk import RiskDecision


@dataclass(frozen=True)
class SimulationEvent:
    event_type: str
    idempotency_key: str
    timestamp: datetime
    payload: Mapping[str, object] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "event_type": self.event_type,
            "idempotency_key": self.idempotency_key,
            "timestamp": self.timestamp.astimezone(timezone.utc).isoformat(),
            "payload": _sanitize(self.payload),
        }


class SimulationJsonlStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def append(self, event: SimulationEvent) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event.to_json_dict(), sort_keys=True) + "\n")

    def read_events(self) -> tuple[SimulationEvent, ...]:
        if not self.path.exists():
            return ()
        events = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                payload = json.loads(line)
                events.append(_event_from_json(payload))
        return tuple(events)


def rebuild_portfolio_from_events(events: tuple[SimulationEvent, ...], *, starting_cash: object) -> SimulatedPortfolio:
    portfolio = initial_simulated_portfolio(starting_cash)
    seen_opens: set[str] = set()
    for event in events:
        if event.event_type == "simulated_entry_opened":
            if event.idempotency_key in seen_opens:
                continue
            seen_opens.add(event.idempotency_key)
            risk = RiskDecision(
                accepted=True,
                symbol=str(event.payload["symbol"]),
                primary_setup=str(event.payload["strategy"]),
                quantity=int(event.payload["quantity"]),
                risk_amount=Decimal(str(event.payload.get("risk_amount", "0"))),
                allocation_amount=Decimal(str(event.payload.get("allocation_amount", "0"))),
                rejection_reasons=(),
                evidence={"rebuilt_from": "simulation_jsonl"},
            )
            portfolio = open_simulated_position(
                portfolio,
                risk_decision=risk,
                idempotency_key=event.idempotency_key,
                entry_price=event.payload["entry_price"],
                stop_price=event.payload["stop_price"],
                target_price=event.payload["target_price"],
                opened_at=event.timestamp,
                correlation_id=str(event.payload.get("correlation_id") or event.idempotency_key),
            )
        elif event.event_type == "simulated_trade_closed":
            portfolio = close_simulated_position(
                portfolio,
                idempotency_key=event.idempotency_key,
                exit_price=event.payload["exit_price"],
                closed_at=event.timestamp,
                reason=SimulatedExitReason(str(event.payload.get("exit_reason") or "system_close")),
            )
    return portfolio


def event_for_open_position(position: SimulatedPosition) -> SimulationEvent:
    return SimulationEvent(
        event_type="simulated_entry_opened",
        idempotency_key=position.idempotency_key,
        timestamp=position.opened_at,
        payload={
            "symbol": position.symbol,
            "strategy": position.strategy,
            "quantity": position.quantity,
            "entry_price": str(position.entry_price),
            "stop_price": str(position.stop_price),
            "target_price": str(position.target_price),
            "correlation_id": position.correlation_id,
            "product_mode": "simulation_only",
            "real_order": False,
        },
    )


def event_for_closed_trade(trade: SimulatedClosedTrade) -> SimulationEvent:
    return SimulationEvent(
        event_type="simulated_trade_closed",
        idempotency_key=trade.idempotency_key,
        timestamp=trade.closed_at,
        payload={
            "symbol": trade.symbol,
            "strategy": trade.strategy,
            "quantity": trade.quantity,
            "exit_price": str(trade.exit_price),
            "exit_reason": trade.exit_reason.value,
            "realized_pnl": str(trade.realized_pnl),
            "correlation_id": trade.correlation_id,
            "product_mode": "simulation_only",
            "real_order": False,
        },
    )


def _event_from_json(payload: Mapping[str, object]) -> SimulationEvent:
    return SimulationEvent(
        event_type=str(payload["event_type"]),
        idempotency_key=str(payload["idempotency_key"]),
        timestamp=datetime.fromisoformat(str(payload["timestamp"])).astimezone(timezone.utc),
        payload=payload.get("payload") if isinstance(payload.get("payload"), Mapping) else {},
    )


def _sanitize(payload: Mapping[str, object]) -> dict[str, object]:
    sanitized = {}
    for key, value in payload.items():
        if any(marker in key.lower() for marker in ("secret", "token", "password", "credential", "api_key")):
            sanitized[key] = "[redacted]"
        else:
            sanitized[key] = value
    return sanitized


__all__ = [
    "SimulationEvent",
    "SimulationJsonlStore",
    "event_for_closed_trade",
    "event_for_open_position",
    "rebuild_portfolio_from_events",
]

