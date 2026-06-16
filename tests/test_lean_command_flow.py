from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from marketpilot.lean_command_receiver import (
    normalize_marketpilot_command,
    validate_marketpilot_command,
)


NOW = datetime(2026, 6, 16, 14, 30, tzinfo=timezone.utc)


def _payload(**overrides):
    payload = {
        "command_type": "marketpilot_signal",
        "correlation_id": "corr-001",
        "signal_id": "sig-001",
        "idempotency_key": "order-intent-001",
        "symbol": "MSFT",
        "quantity": 12,
        "signal_time_utc": "2026-06-16T14:20:00+00:00",
        "expires_at_utc": "2026-06-16T14:40:00+00:00",
        "strategy_mode": "daily_only",
        "primary_setup": "relative_strength_leader",
        "paper_trading_only": True,
        "command_delivery_is_order_execution": False,
    }
    payload.update(overrides)
    return payload


def test_normalize_marketpilot_command_accepts_dict_payload():
    command = normalize_marketpilot_command(_payload())

    assert command.accepted is True
    assert command.command is not None
    assert command.command.symbol == "MSFT"
    assert command.command.quantity == 12
    assert command.command.expires_at_utc == datetime(2026, 6, 16, 14, 40, tzinfo=timezone.utc)


def test_normalize_marketpilot_command_accepts_attribute_payload():
    command = normalize_marketpilot_command(SimpleNamespace(**_payload(symbol="AAPL")))

    assert command.accepted is True
    assert command.command is not None
    assert command.command.symbol == "AAPL"


@pytest.mark.parametrize(
    "field,value,reason",
    [
        ("command_type", "external_order", "unsupported_command_type"),
        ("signal_id", "", "missing_signal_id"),
        ("expires_at_utc", "not-a-time", "malformed_expires_at_utc"),
        ("signal_time_utc", "2026-06-16T14:20:00", "naive_signal_time_utc"),
        ("quantity", 0, "non_positive_quantity"),
        ("quantity", 1.5, "non_integer_quantity"),
        ("symbol", "BTC/USD", "unsupported_symbol"),
        ("paper_trading_only", False, "non_paper_command"),
    ],
)
def test_normalize_marketpilot_command_rejects_malformed_or_unsupported_payloads(field, value, reason):
    result = normalize_marketpilot_command(_payload(**{field: value}))

    assert result.accepted is False
    assert result.reason == reason
    assert result.command is None


def test_validate_marketpilot_command_accepts_fresh_non_duplicate_command():
    normalized = normalize_marketpilot_command(_payload())
    seen_keys: set[str] = set()

    decision = validate_marketpilot_command(normalized.command, seen_idempotency_keys=seen_keys, now_utc=NOW)

    assert decision.accepted is True
    assert decision.reason == "accepted"
    assert decision.symbol == "MSFT"
    assert decision.quantity == 12
    assert decision.tag == "mp:sig-001:order-intent-001"
    assert seen_keys == {"order-intent-001"}


def test_validate_marketpilot_command_rejects_stale_command_before_seen_key_mutates():
    normalized = normalize_marketpilot_command(
        _payload(expires_at_utc="2026-06-16T14:29:59+00:00")
    )
    seen_keys: set[str] = set()

    decision = validate_marketpilot_command(normalized.command, seen_idempotency_keys=seen_keys, now_utc=NOW)

    assert decision.accepted is False
    assert decision.reason == "expired_signal"
    assert decision.tag is None
    assert seen_keys == set()


def test_validate_marketpilot_command_rejects_duplicate_before_order_placement():
    normalized = normalize_marketpilot_command(_payload())
    seen_keys = {"order-intent-001"}

    decision = validate_marketpilot_command(normalized.command, seen_idempotency_keys=seen_keys, now_utc=NOW)

    assert decision.accepted is False
    assert decision.reason == "duplicate_idempotency_key"
    assert decision.symbol == "MSFT"
    assert decision.quantity == 12
    assert decision.tag is None
