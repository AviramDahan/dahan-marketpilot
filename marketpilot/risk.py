"""Paper-only portfolio risk and position sizing decisions."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation, ROUND_FLOOR
from enum import Enum
from pathlib import Path
from typing import Mapping

import yaml


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "risk.yaml"


class RiskRejectionReason(str, Enum):
    INVALID_STOP_DISTANCE = "invalid_stop_distance"
    ZERO_QUANTITY = "zero_quantity"
    INSUFFICIENT_CASH = "insufficient_cash"
    MINIMUM_REWARD_RISK_NOT_MET = "minimum_reward_risk_not_met"
    MAX_OPEN_POSITIONS = "max_open_positions"
    MAX_SECTOR_EXPOSURE = "max_sector_exposure"
    MAX_DAILY_ENTRIES = "max_daily_entries"
    INVALID_CANDIDATE = "invalid_candidate"


@dataclass(frozen=True)
class RiskConfig:
    per_trade_risk_pct: Decimal
    max_open_positions: int
    max_sector_exposure_pct: Decimal
    max_new_entries_per_day: int
    max_position_allocation_pct: Decimal
    minimum_reward_risk: Decimal
    minimum_quantity: int


@dataclass(frozen=True)
class PortfolioSnapshot:
    simulated_equity: Decimal
    available_cash: Decimal
    open_positions: int = 0
    sector_exposure: Mapping[str, Decimal] = field(default_factory=dict)
    new_entries_today: int = 0
    portfolio_epoch: str = "epoch-0"


@dataclass(frozen=True)
class PositionSizingDecision:
    accepted: bool
    quantity: int
    risk_amount: Decimal
    allocation_amount: Decimal
    stop_distance: Decimal
    rejection_reasons: tuple[RiskRejectionReason, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class RiskDecision:
    accepted: bool
    symbol: str
    primary_setup: str
    quantity: int
    risk_amount: Decimal
    allocation_amount: Decimal
    rejection_reasons: tuple[RiskRejectionReason, ...]
    evidence: Mapping[str, object]


def load_risk_config(path: str | Path = DEFAULT_CONFIG_PATH) -> RiskConfig:
    with Path(path).open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    config = loaded.get("risk", loaded)
    if not isinstance(config, dict):
        raise ValueError("risk config must be a mapping.")
    if config.get("paper_trading_only") is not True:
        raise ValueError("risk config requires paper_trading_only: true.")
    disabled = config.get("disabled_behaviors", {})
    for key in (
        "submit_orders",
        "broker_adapters",
        "telegram_delivery",
        "live_deployment",
        "fake_portfolio_authority",
        "leverage",
        "margin",
        "short_selling",
        "real_money_paths",
    ):
        if disabled.get(key) is not False:
            raise ValueError(f"risk config requires disabled {key}.")
    risk_config = RiskConfig(
        per_trade_risk_pct=_positive_decimal(config.get("per_trade_risk_pct"), "per_trade_risk_pct"),
        max_open_positions=_positive_int(config.get("max_open_positions"), "max_open_positions"),
        max_sector_exposure_pct=_positive_decimal(config.get("max_sector_exposure_pct"), "max_sector_exposure_pct"),
        max_new_entries_per_day=_positive_int(config.get("max_new_entries_per_day"), "max_new_entries_per_day"),
        max_position_allocation_pct=_positive_decimal(
            config.get("max_position_allocation_pct"), "max_position_allocation_pct"
        ),
        minimum_reward_risk=_positive_decimal(config.get("minimum_reward_risk"), "minimum_reward_risk"),
        minimum_quantity=_positive_int(config.get("minimum_quantity"), "minimum_quantity"),
    )
    for pct_name in ("per_trade_risk_pct", "max_sector_exposure_pct", "max_position_allocation_pct"):
        if getattr(risk_config, pct_name) > Decimal("100"):
            raise ValueError(f"{pct_name} must be at most 100.")
    return risk_config


def calculate_position_size(
    *,
    simulated_equity: object,
    available_cash: object,
    entry_price: object,
    stop_distance: object,
    reward_risk: object,
    config: RiskConfig | None = None,
) -> PositionSizingDecision:
    active_config = config or load_risk_config()
    equity = _positive_decimal(simulated_equity, "simulated_equity")
    cash = _non_negative_decimal(available_cash, "available_cash")
    entry = _positive_decimal(entry_price, "entry_price")
    rr = _positive_decimal(reward_risk, "reward_risk")
    try:
        distance = _positive_decimal(stop_distance, "stop_distance")
    except ValueError:
        return _sizing_rejection(RiskRejectionReason.INVALID_STOP_DISTANCE)

    if rr < active_config.minimum_reward_risk:
        return _sizing_rejection(RiskRejectionReason.MINIMUM_REWARD_RISK_NOT_MET, stop_distance=distance)

    risk_amount = equity * active_config.per_trade_risk_pct / Decimal("100")
    quantity_by_risk = (risk_amount / distance).to_integral_value(rounding=ROUND_FLOOR)
    allocation_cap = equity * active_config.max_position_allocation_pct / Decimal("100")
    quantity_by_allocation = (allocation_cap / entry).to_integral_value(rounding=ROUND_FLOOR)
    quantity_by_cash = (cash / entry).to_integral_value(rounding=ROUND_FLOOR)
    quantity = int(min(quantity_by_risk, quantity_by_allocation, quantity_by_cash))
    allocation = entry * Decimal(quantity)

    reasons: list[RiskRejectionReason] = []
    if quantity < active_config.minimum_quantity:
        reasons.append(RiskRejectionReason.ZERO_QUANTITY)
    if quantity_by_cash < min(quantity_by_risk, quantity_by_allocation) and quantity < active_config.minimum_quantity:
        reasons.append(RiskRejectionReason.INSUFFICIENT_CASH)
    return PositionSizingDecision(
        accepted=not reasons,
        quantity=quantity,
        risk_amount=risk_amount,
        allocation_amount=allocation,
        stop_distance=distance,
        rejection_reasons=tuple(reasons),
    )


def evaluate_portfolio_risk(
    *,
    candidate: object,
    portfolio: PortfolioSnapshot,
    entry_price: object,
    stop_distance: object,
    reward_risk: object,
    sector: str = "unknown",
    config: RiskConfig | None = None,
) -> RiskDecision:
    active_config = config or load_risk_config()
    symbol = str(getattr(candidate, "symbol", "")).strip().upper()
    primary_setup = str(getattr(candidate, "primary_setup", "")).strip()
    reasons: list[RiskRejectionReason] = []
    if not symbol or not primary_setup:
        reasons.append(RiskRejectionReason.INVALID_CANDIDATE)
    if portfolio.open_positions >= active_config.max_open_positions:
        reasons.append(RiskRejectionReason.MAX_OPEN_POSITIONS)
    if portfolio.new_entries_today >= active_config.max_new_entries_per_day:
        reasons.append(RiskRejectionReason.MAX_DAILY_ENTRIES)

    sizing = calculate_position_size(
        simulated_equity=portfolio.simulated_equity,
        available_cash=portfolio.available_cash,
        entry_price=entry_price,
        stop_distance=stop_distance,
        reward_risk=reward_risk,
        config=active_config,
    )
    reasons.extend(sizing.rejection_reasons)

    exposure = portfolio.sector_exposure.get(sector, Decimal("0"))
    projected_exposure = exposure + sizing.allocation_amount
    sector_cap = portfolio.simulated_equity * active_config.max_sector_exposure_pct / Decimal("100")
    if projected_exposure > sector_cap:
        reasons.append(RiskRejectionReason.MAX_SECTOR_EXPOSURE)

    return RiskDecision(
        accepted=not reasons,
        symbol=symbol,
        primary_setup=primary_setup,
        quantity=sizing.quantity if not reasons else 0,
        risk_amount=sizing.risk_amount,
        allocation_amount=sizing.allocation_amount,
        rejection_reasons=tuple(dict.fromkeys(reasons)),
        evidence={
            "classification_is_instruction": False,
            "portfolio_epoch": portfolio.portfolio_epoch,
            "sector": sector,
            "projected_sector_exposure": str(projected_exposure),
            "sector_cap": str(sector_cap),
            "open_positions": portfolio.open_positions,
            "new_entries_today": portfolio.new_entries_today,
        },
    )


def _sizing_rejection(
    reason: RiskRejectionReason,
    *,
    stop_distance: Decimal = Decimal("0"),
) -> PositionSizingDecision:
    return PositionSizingDecision(
        accepted=False,
        quantity=0,
        risk_amount=Decimal("0"),
        allocation_amount=Decimal("0"),
        stop_distance=stop_distance,
        rejection_reasons=(reason,),
    )


def _positive_decimal(value: object, field_name: str) -> Decimal:
    decimal_value = _decimal(value, field_name)
    if decimal_value <= 0 or not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be a positive finite number.")
    return decimal_value


def _non_negative_decimal(value: object, field_name: str) -> Decimal:
    decimal_value = _decimal(value, field_name)
    if decimal_value < 0 or not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be a non-negative finite number.")
    return decimal_value


def _decimal(value: object, field_name: str) -> Decimal:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} must be numeric.") from exc


def _positive_int(value: object, field_name: str) -> int:
    try:
        int_value = int(str(value))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a positive integer.") from exc
    if int_value <= 0:
        raise ValueError(f"{field_name} must be a positive integer.")
    return int_value
