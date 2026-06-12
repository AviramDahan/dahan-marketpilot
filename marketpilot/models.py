"""Phase 1-safe foundational domain models."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import Enum


class TradingMode(str, Enum):
    PAPER = "paper"


class EnvironmentName(str, Enum):
    BACKTEST = "backtest"
    SHADOW = "shadow"
    PAPER = "paper"


class CurrencyCode(str, Enum):
    USD = "USD"
    NIS = "NIS"


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: CurrencyCode

    @classmethod
    def from_value(cls, amount: object, currency: str | CurrencyCode) -> "Money":
        currency_code = parse_currency(currency)
        decimal_amount = positive_decimal(amount, "amount")
        return cls(amount=decimal_amount, currency=currency_code)

    def format_public(self) -> str:
        return f"{self.amount:.2f} {self.currency.value}"


@dataclass(frozen=True)
class FxSeed:
    starting_budget: Money
    initial_usd_ils_rate: Decimal
    starting_cash: Money
    fx_rate_timestamp: str
    fx_rate_source: str

    @classmethod
    def create(
        cls,
        starting_budget_nis: object,
        initial_usd_ils_rate: object,
        fx_rate_timestamp: str,
        fx_rate_source: str,
    ) -> "FxSeed":
        budget = Money.from_value(starting_budget_nis, CurrencyCode.NIS)
        rate = positive_decimal(initial_usd_ils_rate, "initial_usd_ils_rate")
        cash = Money(amount=budget.amount / rate, currency=CurrencyCode.USD)
        if not fx_rate_timestamp.strip():
            raise ValueError("fx_rate_timestamp is required.")
        if not fx_rate_source.strip():
            raise ValueError("fx_rate_source is required.")
        return cls(
            starting_budget=budget,
            initial_usd_ils_rate=rate,
            starting_cash=cash,
            fx_rate_timestamp=fx_rate_timestamp,
            fx_rate_source=fx_rate_source,
        )


@dataclass(frozen=True)
class SafetyStatus:
    paper_trading_only: bool
    mode: TradingMode

    def validate(self) -> None:
        if self.paper_trading_only is not True or self.mode is not TradingMode.PAPER:
            raise ValueError("SafetyStatus requires paper-only mode.")


@dataclass(frozen=True)
class ReadOnlyStatus:
    read_only: bool
    no_live_data_connected: bool

    def validate(self) -> None:
        if self.read_only is not True:
            raise ValueError("ReadOnlyStatus requires read-only mode.")
        if self.no_live_data_connected is not True:
            raise ValueError("ReadOnlyStatus requires no live data connection in Phase 1.")


@dataclass(frozen=True)
class ValidationIssue:
    path: str
    code: str
    message: str

    def public_message(self) -> str:
        sanitized_path = _sanitize(self.path)
        sanitized_message = _sanitize(self.message)
        return f"{self.code}: {sanitized_path}: {sanitized_message}"


def parse_currency(currency: str | CurrencyCode) -> CurrencyCode:
    if isinstance(currency, CurrencyCode):
        return currency
    normalized = str(currency).upper()
    try:
        return CurrencyCode(normalized)
    except ValueError as exc:
        raise ValueError("currency must be USD or NIS.") from exc


def positive_decimal(value: object, field_name: str) -> Decimal:
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} must be a positive number.") from exc
    if decimal_value <= 0:
        raise ValueError(f"{field_name} must be a positive number.")
    return decimal_value


def _sanitize(text: str) -> str:
    sanitized = text
    for marker in ("secret", "token", "password", "credential", "api_key"):
        sanitized = sanitized.replace(marker, "[redacted]")
        sanitized = sanitized.replace(marker.upper(), "[redacted]")
    return sanitized
