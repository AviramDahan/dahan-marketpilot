"""Paper-only exit obligation models."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable, Mapping

import yaml

from marketpilot.notification_events import (
    FakeNotificationCollector,
    NotificationDomainEvent,
    event_for_protective_recovery,
)
from marketpilot.quantconnect_paper import QuantConnectPaperSnapshot
from marketpilot.setups.base import NumericEvidence


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "exits.yaml"


@dataclass(frozen=True)
class StopModel:
    price: Decimal
    source: str
    atr_sanity_cap_applied: bool = False


@dataclass(frozen=True)
class TargetModel:
    price: Decimal
    r_multiple: Decimal


@dataclass(frozen=True)
class PartialExitRule:
    name: str
    r_multiple: Decimal
    close_fraction: Decimal
    execute_orders: bool = False


@dataclass(frozen=True)
class TrailingStopPolicy:
    enabled: bool = False


@dataclass(frozen=True)
class HoldingPeriodPolicy:
    maximum_days: int


@dataclass(frozen=True)
class ExitPlan:
    symbol: str
    entry_price: Decimal
    stop: StopModel
    target: TargetModel
    partial_exit_rules: tuple[PartialExitRule, ...]
    trailing_stop: TrailingStopPolicy
    holding_period: HoldingPeriodPolicy
    obligations_active: bool = True
    evidence: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class ProtectiveRecoveryDecision:
    block_new_entries: bool
    preserve_exits: bool
    protective_recovery_required: bool
    missing_protection_symbols: tuple[str, ...]
    correlation_id: str
    notification_event: NotificationDomainEvent | None = None
    notification_delivery_attempted: bool = False
    notification_delivery_succeeded: bool | None = None


def load_exit_config(path: str | Path = DEFAULT_CONFIG_PATH) -> dict:
    with Path(path).open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    config = loaded.get("exits", loaded)
    if not isinstance(config, dict):
        raise ValueError("exits config must be a mapping.")
    if config.get("paper_trading_only") is not True:
        raise ValueError("exits config requires paper_trading_only: true.")
    disabled = config.get("disabled_behaviors", {})
    for key in ("submit_orders", "cancel_orders", "telegram_delivery", "live_deployment", "fake_portfolio_authority"):
        if disabled.get(key) is not False:
            raise ValueError(f"exits config requires disabled {key}.")
    if config.get("trailing_stop", {}).get("enabled") is not False:
        raise ValueError("trailing stop must be disabled by default.")
    return config


def build_exit_plan(
    *,
    symbol: str,
    entry_price: object,
    evidence: Iterable[NumericEvidence],
    atr: object | None = None,
    current_regime: str = "risk_on",
    config: dict | None = None,
) -> ExitPlan:
    active_config = config or load_exit_config()
    entry = _positive_decimal(entry_price, "entry_price")
    stop_price, source = _stop_from_evidence(tuple(evidence))
    if stop_price >= entry:
        raise ValueError("stop price must be below entry for long-only exits.")
    risk_per_share = entry - stop_price
    if atr is not None:
        atr_value = _positive_decimal(atr, "atr")
        cap = atr_value * _positive_decimal(active_config["atr_sanity_cap_multiple"], "atr_sanity_cap_multiple")
        if risk_per_share > cap:
            raise ValueError("stop distance exceeds ATR sanity cap.")
    target_r = _positive_decimal(active_config["minimum_target_r_multiple"], "minimum_target_r_multiple")
    target_price = entry + risk_per_share * target_r
    partial_rules = tuple(
        PartialExitRule(
            name=str(rule["name"]),
            r_multiple=_positive_decimal(rule["r_multiple"], "partial r_multiple"),
            close_fraction=_positive_decimal(rule["close_fraction"], "partial close_fraction"),
            execute_orders=False,
        )
        for rule in active_config.get("partial_exits", {}).get("rules", ())
    )
    return ExitPlan(
        symbol=symbol.strip().upper(),
        entry_price=entry,
        stop=StopModel(price=stop_price, source=source, atr_sanity_cap_applied=atr is not None),
        target=TargetModel(price=target_price, r_multiple=target_r),
        partial_exit_rules=partial_rules,
        trailing_stop=TrailingStopPolicy(enabled=False),
        holding_period=HoldingPeriodPolicy(maximum_days=int(active_config["maximum_holding_period_days"])),
        obligations_active=True,
        evidence={
            "current_regime": current_regime,
            "risk_off_blocks_new_entries_only": current_regime == "risk_off",
        },
    )


def exit_obligations_after_regime_change(exit_plan: ExitPlan, new_regime: str) -> ExitPlan:
    return ExitPlan(
        symbol=exit_plan.symbol,
        entry_price=exit_plan.entry_price,
        stop=exit_plan.stop,
        target=exit_plan.target,
        partial_exit_rules=exit_plan.partial_exit_rules,
        trailing_stop=exit_plan.trailing_stop,
        holding_period=exit_plan.holding_period,
        obligations_active=True,
        evidence={**exit_plan.evidence, "new_regime": new_regime, "exits_remain_authoritative": True},
    )


def evaluate_protective_recovery(
    *,
    snapshot: QuantConnectPaperSnapshot,
    exit_plans: tuple[ExitPlan, ...],
    correlation_id: str,
    notification_collector: FakeNotificationCollector | None = None,
) -> ProtectiveRecoveryDecision:
    if snapshot.authoritative_source != "quantconnect":
        raise ValueError("protective recovery requires a QuantConnect-authoritative snapshot.")
    if not correlation_id.strip():
        raise ValueError("correlation_id is required for protective recovery.")

    active_exit_plans = {plan.symbol: plan for plan in exit_plans if plan.obligations_active}
    missing_symbols = tuple(
        holding.symbol
        for holding in snapshot.holdings
        if holding.quantity > 0 and _missing_protective_state(holding.symbol, active_exit_plans, snapshot)
    )
    if not missing_symbols:
        return ProtectiveRecoveryDecision(
            block_new_entries=False,
            preserve_exits=True,
            protective_recovery_required=False,
            missing_protection_symbols=(),
            correlation_id=correlation_id.strip(),
        )

    event = event_for_protective_recovery(
        correlation_id,
        {
            "authoritative_source": "quantconnect",
            "missing_protection_symbols": missing_symbols,
            "block_new_entries": True,
            "preserve_exits": True,
            "telegram_delivery_controls_recovery": False,
        },
    )
    attempted = notification_collector is not None
    delivered = notification_collector.emit(event) if notification_collector is not None else None
    return ProtectiveRecoveryDecision(
        block_new_entries=True,
        preserve_exits=True,
        protective_recovery_required=True,
        missing_protection_symbols=missing_symbols,
        correlation_id=correlation_id.strip(),
        notification_event=event,
        notification_delivery_attempted=attempted,
        notification_delivery_succeeded=delivered,
    )


def _missing_protective_state(
    symbol: str,
    active_exit_plans: Mapping[str, ExitPlan],
    snapshot: QuantConnectPaperSnapshot,
) -> bool:
    if symbol not in active_exit_plans:
        return True
    active_roles = {
        order.order_role
        for order in snapshot.orders
        if order.symbol == symbol and order.status not in {"filled", "canceled", "cancelled", "rejected"}
    }
    has_stop = "stop" in active_roles or "protective_stop" in active_roles
    has_target = "target" in active_roles or "profit_target" in active_roles
    return not (has_stop and has_target)


def _stop_from_evidence(evidence: tuple[NumericEvidence, ...]) -> tuple[Decimal, str]:
    for name in ("structural_invalidation", "swing_low", "breakout_level", "stop_price"):
        for item in evidence:
            if item.name == name and item.value is not None:
                return _positive_decimal(item.value, name), name
    raise ValueError("setup evidence must include a structural stop source.")


def _positive_decimal(value: object, field_name: str) -> Decimal:
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} must be numeric.") from exc
    if decimal_value <= 0 or not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be a positive finite number.")
    return decimal_value
