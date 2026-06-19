from __future__ import annotations

"""Internal paper simulator for simulation-only product mode."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Mapping

from marketpilot.product_modes import assert_simulation_only_safety
from marketpilot.risk import RiskDecision


class SimulatedPositionStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"


class SimulatedExitReason(str, Enum):
    STOP_HIT = "stop_hit"
    TARGET_HIT = "target_hit"
    SYSTEM_CLOSE = "system_close"


@dataclass(frozen=True)
class SimulatedPosition:
    idempotency_key: str
    symbol: str
    strategy: str
    quantity: int
    entry_price: Decimal
    stop_price: Decimal
    target_price: Decimal
    opened_at: datetime
    correlation_id: str
    score: Decimal = Decimal("0")
    rank: int | None = None
    last_price: Decimal | None = None
    status: SimulatedPositionStatus = SimulatedPositionStatus.OPEN
    evidence: Mapping[str, object] = field(default_factory=dict)

    @property
    def market_price(self) -> Decimal:
        return self.last_price if self.last_price is not None else self.entry_price

    @property
    def unrealized_pnl(self) -> Decimal:
        return (self.market_price - self.entry_price) * Decimal(self.quantity)


@dataclass(frozen=True)
class SimulatedClosedTrade:
    idempotency_key: str
    symbol: str
    strategy: str
    quantity: int
    entry_price: Decimal
    exit_price: Decimal
    opened_at: datetime
    closed_at: datetime
    exit_reason: SimulatedExitReason
    realized_pnl: Decimal
    correlation_id: str
    evidence: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class SimulatedPortfolio:
    starting_cash: Decimal
    available_cash: Decimal
    equity: Decimal
    open_positions: tuple[SimulatedPosition, ...] = ()
    closed_trades: tuple[SimulatedClosedTrade, ...] = ()
    realized_pnl: Decimal = Decimal("0")
    unrealized_pnl: Decimal = Decimal("0")
    product_mode: str = "simulation_only"
    paper_trading_only: bool = True


def initial_simulated_portfolio(starting_cash: object) -> SimulatedPortfolio:
    cash = _positive_decimal(starting_cash, "starting_cash")
    return SimulatedPortfolio(starting_cash=cash, available_cash=cash, equity=cash)


def open_simulated_position(
    portfolio: SimulatedPortfolio,
    *,
    risk_decision: RiskDecision,
    idempotency_key: str,
    entry_price: object,
    stop_price: object,
    target_price: object,
    opened_at: datetime,
    correlation_id: str,
    score: object = Decimal("0"),
    rank: int | None = None,
    evidence: Mapping[str, object] | None = None,
) -> SimulatedPortfolio:
    assert_simulation_only_safety()
    if not risk_decision.accepted:
        raise ValueError("accepted risk decision is required.")
    if any(position.idempotency_key == idempotency_key for position in portfolio.open_positions):
        raise ValueError("duplicate simulated position idempotency key.")
    entry = _positive_decimal(entry_price, "entry_price")
    stop = _positive_decimal(stop_price, "stop_price")
    target = _positive_decimal(target_price, "target_price")
    quantity = int(risk_decision.quantity)
    if quantity <= 0:
        raise ValueError("simulated quantity must be positive.")
    allocation = entry * Decimal(quantity)
    if allocation > portfolio.available_cash:
        raise ValueError("insufficient simulated cash.")
    position = SimulatedPosition(
        idempotency_key=idempotency_key.strip(),
        symbol=risk_decision.symbol.strip().upper(),
        strategy=risk_decision.primary_setup,
        quantity=quantity,
        entry_price=entry,
        stop_price=stop,
        target_price=target,
        opened_at=_aware_utc(opened_at),
        correlation_id=correlation_id.strip(),
        score=_decimal(score, "score"),
        rank=rank,
        evidence={
            "product_mode": "simulation_only",
            "paper_trading_only": True,
            "real_order": False,
            "quantconnect_order": False,
            **dict(evidence or {}),
        },
    )
    open_positions = tuple(portfolio.open_positions) + (position,)
    return _recalculate(portfolio, open_positions=open_positions, closed_trades=portfolio.closed_trades, available_cash=portfolio.available_cash - allocation)


def mark_to_market(
    portfolio: SimulatedPortfolio,
    prices: Mapping[str, object],
) -> SimulatedPortfolio:
    updated = []
    for position in portfolio.open_positions:
        value = prices.get(position.symbol)
        if value is None:
            updated.append(position)
        else:
            updated.append(_replace_position(position, last_price=_positive_decimal(value, "market_price")))
    return _recalculate(portfolio, open_positions=tuple(updated), closed_trades=portfolio.closed_trades, available_cash=portfolio.available_cash)


def close_positions_by_stop_target(
    portfolio: SimulatedPortfolio,
    prices: Mapping[str, object],
    *,
    closed_at: datetime,
) -> SimulatedPortfolio:
    open_positions: list[SimulatedPosition] = []
    closed_trades = list(portfolio.closed_trades)
    cash = portfolio.available_cash
    for position in portfolio.open_positions:
        price_value = prices.get(position.symbol)
        if price_value is None:
            open_positions.append(position)
            continue
        price = _positive_decimal(price_value, "market_price")
        reason = None
        exit_price = price
        if price <= position.stop_price:
            reason = SimulatedExitReason.STOP_HIT
            exit_price = position.stop_price
        elif price >= position.target_price:
            reason = SimulatedExitReason.TARGET_HIT
            exit_price = position.target_price
        if reason is None:
            open_positions.append(_replace_position(position, last_price=price))
            continue
        closed = _closed_trade(position, exit_price=exit_price, closed_at=closed_at, reason=reason)
        closed_trades.append(closed)
        cash += exit_price * Decimal(position.quantity)
    return _recalculate(portfolio, open_positions=tuple(open_positions), closed_trades=tuple(closed_trades), available_cash=cash)


def close_simulated_position(
    portfolio: SimulatedPortfolio,
    *,
    idempotency_key: str,
    exit_price: object,
    closed_at: datetime,
    reason: SimulatedExitReason = SimulatedExitReason.SYSTEM_CLOSE,
) -> SimulatedPortfolio:
    target = idempotency_key.strip()
    open_positions = []
    closed_trades = list(portfolio.closed_trades)
    cash = portfolio.available_cash
    found = False
    parsed_exit = _positive_decimal(exit_price, "exit_price")
    for position in portfolio.open_positions:
        if position.idempotency_key != target:
            open_positions.append(position)
            continue
        found = True
        closed = _closed_trade(position, exit_price=parsed_exit, closed_at=closed_at, reason=reason)
        closed_trades.append(closed)
        cash += parsed_exit * Decimal(position.quantity)
    if not found:
        raise ValueError("simulated position not found.")
    return _recalculate(portfolio, open_positions=tuple(open_positions), closed_trades=tuple(closed_trades), available_cash=cash)


def performance_summary(portfolio: SimulatedPortfolio) -> dict[str, object]:
    wins = [trade for trade in portfolio.closed_trades if trade.realized_pnl > 0]
    losses = [trade for trade in portfolio.closed_trades if trade.realized_pnl <= 0]
    return {
        "product_mode": "simulation_only",
        "open_trade_count": len(portfolio.open_positions),
        "closed_trade_count": len(portfolio.closed_trades),
        "realized_pnl": str(portfolio.realized_pnl),
        "unrealized_pnl": str(portfolio.unrealized_pnl),
        "equity": str(portfolio.equity),
        "win_rate": 0 if not portfolio.closed_trades else round(100 * len(wins) / len(portfolio.closed_trades), 2),
        "average_gain": str(_average([trade.realized_pnl for trade in wins])),
        "average_loss": str(_average([trade.realized_pnl for trade in losses])),
        "real_orders": False,
        "quantconnect_required": False,
    }


def _closed_trade(
    position: SimulatedPosition,
    *,
    exit_price: Decimal,
    closed_at: datetime,
    reason: SimulatedExitReason,
) -> SimulatedClosedTrade:
    pnl = (exit_price - position.entry_price) * Decimal(position.quantity)
    return SimulatedClosedTrade(
        idempotency_key=position.idempotency_key,
        symbol=position.symbol,
        strategy=position.strategy,
        quantity=position.quantity,
        entry_price=position.entry_price,
        exit_price=exit_price,
        opened_at=position.opened_at,
        closed_at=_aware_utc(closed_at),
        exit_reason=reason,
        realized_pnl=pnl,
        correlation_id=position.correlation_id,
        evidence=position.evidence,
    )


def _recalculate(
    base: SimulatedPortfolio,
    *,
    open_positions: tuple[SimulatedPosition, ...],
    closed_trades: tuple[SimulatedClosedTrade, ...],
    available_cash: Decimal,
) -> SimulatedPortfolio:
    unrealized = sum((position.unrealized_pnl for position in open_positions), Decimal("0"))
    realized = sum((trade.realized_pnl for trade in closed_trades), Decimal("0"))
    open_value = sum((position.market_price * Decimal(position.quantity) for position in open_positions), Decimal("0"))
    return SimulatedPortfolio(
        starting_cash=base.starting_cash,
        available_cash=available_cash,
        equity=available_cash + open_value,
        open_positions=open_positions,
        closed_trades=closed_trades,
        realized_pnl=realized,
        unrealized_pnl=unrealized,
    )


def _replace_position(position: SimulatedPosition, **updates: object) -> SimulatedPosition:
    data = position.__dict__.copy()
    data.update(updates)
    return SimulatedPosition(**data)


def _average(values: list[Decimal]) -> Decimal:
    if not values:
        return Decimal("0")
    return sum(values, Decimal("0")) / Decimal(len(values))


def _positive_decimal(value: object, field_name: str) -> Decimal:
    parsed = _decimal(value, field_name)
    if parsed <= 0:
        raise ValueError(f"{field_name} must be positive.")
    return parsed


def _decimal(value: object, field_name: str) -> Decimal:
    try:
        return Decimal(str(value))
    except Exception as exc:
        raise ValueError(f"{field_name} must be numeric.") from exc


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware.")
    return value.astimezone(timezone.utc)


__all__ = [
    "SimulatedClosedTrade",
    "SimulatedExitReason",
    "SimulatedPortfolio",
    "SimulatedPosition",
    "SimulatedPositionStatus",
    "close_positions_by_stop_target",
    "close_simulated_position",
    "initial_simulated_portfolio",
    "mark_to_market",
    "open_simulated_position",
    "performance_summary",
]

