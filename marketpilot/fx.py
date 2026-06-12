"""FX seed calculations for the launch configuration."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation


@dataclass(frozen=True)
class FxSeed:
    starting_budget_nis: Decimal
    initial_usd_ils_rate: Decimal
    starting_cash_usd: Decimal
    trading_currency: str
    display_currency: str
    fx_rate_timestamp: str
    fx_rate_source: str


def calculate_starting_cash_usd(starting_budget_nis: object, initial_usd_ils_rate: object) -> Decimal:
    """Calculate USD starting cash from the configured NIS budget and launch FX rate."""

    budget = _positive_decimal(starting_budget_nis, "starting_budget_nis")
    rate = _positive_decimal(initial_usd_ils_rate, "initial_usd_ils_rate")
    return budget / rate


def build_fx_seed(config: dict[str, object]) -> FxSeed:
    """Build and validate an FX seed from environment configuration."""

    calculated_cash = calculate_starting_cash_usd(
        config.get("starting_budget_nis"),
        config.get("initial_usd_ils_rate"),
    )
    configured_cash = _positive_decimal(config.get("starting_cash_usd"), "starting_cash_usd")

    if abs(configured_cash - calculated_cash) > Decimal("0.01"):
        raise ValueError("starting_cash_usd must match starting_budget_nis / initial_usd_ils_rate.")

    trading_currency = str(config.get("trading_currency", "")).upper()
    display_currency = str(config.get("display_currency", "")).upper()
    if trading_currency != "USD":
        raise ValueError("trading_currency must be USD.")
    if display_currency != "NIS":
        raise ValueError("display_currency must be NIS.")

    timestamp = str(config.get("fx_rate_timestamp", "")).strip()
    source = str(config.get("fx_rate_source", "")).strip()
    if not timestamp:
        raise ValueError("fx_rate_timestamp is required.")
    if not source:
        raise ValueError("fx_rate_source is required.")

    return FxSeed(
        starting_budget_nis=_positive_decimal(config.get("starting_budget_nis"), "starting_budget_nis"),
        initial_usd_ils_rate=_positive_decimal(config.get("initial_usd_ils_rate"), "initial_usd_ils_rate"),
        starting_cash_usd=configured_cash,
        trading_currency=trading_currency,
        display_currency=display_currency,
        fx_rate_timestamp=timestamp,
        fx_rate_source=source,
    )


def _positive_decimal(value: object, name: str) -> Decimal:
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{name} must be a positive number.") from exc
    if amount <= 0:
        raise ValueError(f"{name} must be a positive number.")
    return amount
