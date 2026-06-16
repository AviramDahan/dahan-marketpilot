"""Pure LEAN command receiver helpers for MarketPilot signal commands."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Mapping, MutableSet

from marketpilot.paper_command_models import (
    COMMAND_TYPE_MARKETPILOT_SIGNAL,
    build_order_tag,
)


_SUPPORTED_SYMBOL_RE = re.compile(r"^[A-Z][A-Z0-9.]{0,11}$")
_UNSAFE_ORDER_FIELDS = frozenset(
    {
        "action",
        "order_action",
        "order_type",
        "brokerage",
        "brokerage_model",
        "asset_class",
        "security_type",
        "leverage",
        "margin",
        "short",
    }
)


@dataclass(frozen=True)
class LeanMarketPilotCommand:
    command_type: str
    correlation_id: str
    signal_id: str
    idempotency_key: str
    symbol: str
    quantity: int
    signal_time_utc: datetime
    expires_at_utc: datetime
    strategy_mode: str
    primary_setup: str
    paper_trading_only: bool


@dataclass(frozen=True)
class CommandNormalizationResult:
    accepted: bool
    reason: str
    command: LeanMarketPilotCommand | None = None


@dataclass(frozen=True)
class CommandValidationResult:
    accepted: bool
    reason: str
    symbol: str | None = None
    quantity: int | None = None
    tag: str | None = None


def normalize_marketpilot_command(payload: object) -> CommandNormalizationResult:
    """Normalize dict-like or attribute-style command payloads into a strict model."""

    if payload is None:
        return CommandNormalizationResult(False, "missing_command_payload")

    field_names = _payload_field_names(payload)
    unsafe_field = next((field for field in sorted(_UNSAFE_ORDER_FIELDS) if field in field_names), None)
    if unsafe_field is not None:
        return CommandNormalizationResult(False, f"unsupported_field_{unsafe_field}")

    command_type = _optional_text(payload, "command_type")
    if command_type != COMMAND_TYPE_MARKETPILOT_SIGNAL:
        return CommandNormalizationResult(False, "unsupported_command_type")

    paper_trading_only = _field_value(payload, "paper_trading_only")
    if paper_trading_only is not True:
        return CommandNormalizationResult(False, "non_paper_command")

    required_text_fields = {
        "correlation_id": _optional_text(payload, "correlation_id"),
        "signal_id": _optional_text(payload, "signal_id"),
        "idempotency_key": _optional_text(payload, "idempotency_key"),
        "strategy_mode": _optional_text(payload, "strategy_mode"),
        "primary_setup": _optional_text(payload, "primary_setup"),
    }
    for field_name, value in required_text_fields.items():
        if not value:
            return CommandNormalizationResult(False, f"missing_{field_name}")

    symbol = _optional_text(payload, "symbol")
    if not symbol:
        return CommandNormalizationResult(False, "missing_symbol")
    symbol = symbol.upper()
    if _SUPPORTED_SYMBOL_RE.fullmatch(symbol) is None:
        return CommandNormalizationResult(False, "unsupported_symbol")

    quantity_value = _field_value(payload, "quantity")
    if isinstance(quantity_value, bool) or not isinstance(quantity_value, int):
        return CommandNormalizationResult(False, "non_integer_quantity")
    if quantity_value <= 0:
        return CommandNormalizationResult(False, "non_positive_quantity")

    signal_time = _parse_required_aware_utc(payload, "signal_time_utc")
    if not isinstance(signal_time, datetime):
        return CommandNormalizationResult(False, signal_time)

    expires_at = _parse_required_aware_utc(payload, "expires_at_utc")
    if not isinstance(expires_at, datetime):
        return CommandNormalizationResult(False, expires_at)
    if expires_at < signal_time:
        return CommandNormalizationResult(False, "expires_before_signal_time")

    return CommandNormalizationResult(
        True,
        "normalized",
        LeanMarketPilotCommand(
            command_type=command_type,
            correlation_id=required_text_fields["correlation_id"],
            signal_id=required_text_fields["signal_id"],
            idempotency_key=required_text_fields["idempotency_key"],
            symbol=symbol,
            quantity=quantity_value,
            signal_time_utc=signal_time,
            expires_at_utc=expires_at,
            strategy_mode=required_text_fields["strategy_mode"],
            primary_setup=required_text_fields["primary_setup"],
            paper_trading_only=True,
        ),
    )


def validate_marketpilot_command(
    command: LeanMarketPilotCommand | None,
    *,
    seen_idempotency_keys: MutableSet[str],
    now_utc: datetime | None = None,
) -> CommandValidationResult:
    """Validate freshness and idempotency before a LEAN order is submitted."""

    if command is None:
        return CommandValidationResult(False, "missing_normalized_command")
    if command.paper_trading_only is not True:
        return CommandValidationResult(False, "non_paper_command", command.symbol, command.quantity)

    now = now_utc or datetime.now(timezone.utc)
    if now.tzinfo is None:
        return CommandValidationResult(False, "naive_now_utc", command.symbol, command.quantity)
    now = now.astimezone(timezone.utc)

    if now > command.expires_at_utc.astimezone(timezone.utc):
        return CommandValidationResult(False, "expired_signal", command.symbol, command.quantity)

    if command.idempotency_key in seen_idempotency_keys:
        return CommandValidationResult(False, "duplicate_idempotency_key", command.symbol, command.quantity)

    try:
        tag = build_order_tag(signal_id=command.signal_id, idempotency_key=command.idempotency_key)
    except ValueError:
        return CommandValidationResult(False, "invalid_order_tag", command.symbol, command.quantity)

    seen_idempotency_keys.add(command.idempotency_key)
    return CommandValidationResult(True, "accepted", command.symbol, command.quantity, tag)


def _payload_field_names(payload: object) -> frozenset[str]:
    if isinstance(payload, Mapping):
        return frozenset(str(key).lower() for key in payload)
    return frozenset(name.lower() for name in dir(payload) if not name.startswith("_"))


def _field_value(payload: object, field_name: str) -> object:
    candidates = _field_candidates(field_name)
    if isinstance(payload, Mapping):
        for candidate in candidates:
            if candidate in payload:
                return payload[candidate]
        return None

    for candidate in candidates:
        if hasattr(payload, candidate):
            return getattr(payload, candidate)
    return None


def _optional_text(payload: object, field_name: str) -> str:
    value = _field_value(payload, field_name)
    if value is None:
        return ""
    return str(value).strip()


def _parse_required_aware_utc(payload: object, field_name: str) -> datetime | str:
    value = _field_value(payload, field_name)
    if value is None or str(value).strip() == "":
        return f"missing_{field_name}"

    if isinstance(value, datetime):
        parsed = value
    else:
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return f"malformed_{field_name}"

    if parsed.tzinfo is None:
        return f"naive_{field_name}"
    return parsed.astimezone(timezone.utc)


def _field_candidates(field_name: str) -> tuple[str, ...]:
    pascal = "".join(part.capitalize() for part in field_name.split("_"))
    mixed = field_name[0].upper() + field_name[1:] if field_name else field_name
    return (field_name, mixed, pascal)


__all__ = [
    "CommandNormalizationResult",
    "CommandValidationResult",
    "LeanMarketPilotCommand",
    "normalize_marketpilot_command",
    "validate_marketpilot_command",
]
