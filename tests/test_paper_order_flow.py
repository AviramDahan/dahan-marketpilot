"""Offline tests for paper deployment and signal command flow."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from marketpilot.order_lifecycle import OrderIntent
from marketpilot.paper_command_models import (
    MarketPilotSignalCommand,
    SignalFreshnessPolicy,
    build_deployment_idempotency_key,
    build_order_tag,
    parse_order_tag,
)


UTC = timezone.utc


def _order_intent(*, signal_time: datetime | None = None) -> OrderIntent:
    return OrderIntent(
        idempotency_key="order-intent-abc123",
        symbol="msft",
        primary_setup="trend_pullback",
        strategy_mode="daily_only",
        signal_time=signal_time or datetime(2026, 6, 16, 13, 30, tzinfo=UTC),
        portfolio_epoch="sync-gen-7",
        quantity=10,
        entry_price=Decimal("420.00"),
        stop_price=Decimal("400.00"),
        target_price=Decimal("460.00"),
        audit_metadata={"risk_decision_id": "risk-1"},
    )


def test_deployment_idempotency_key_is_deterministic_and_sorts_providers():
    first = build_deployment_idempotency_key(
        project_id=123,
        compile_id="C-1",
        node_id="N-1",
        version_id="-1",
        data_providers={
            "Zulu": {"id": "Zulu"},
            "QuantConnectBrokerage": {"id": "QuantConnectBrokerage"},
        },
        strategy_version="strategy-v1",
        config_version="config-v1",
    )
    second = build_deployment_idempotency_key(
        project_id=123,
        compile_id="C-1",
        node_id="N-1",
        version_id="-1",
        data_providers={
            "QuantConnectBrokerage": {"id": "QuantConnectBrokerage"},
            "Zulu": {"id": "Zulu"},
        },
        strategy_version="strategy-v1",
        config_version="config-v1",
    )
    changed = build_deployment_idempotency_key(
        project_id=123,
        compile_id="C-1",
        node_id="N-1",
        version_id="-2",
        data_providers={"QuantConnectBrokerage": {"id": "QuantConnectBrokerage"}},
        strategy_version="strategy-v1",
        config_version="config-v1",
    )

    assert first == second
    assert first.startswith("paper-deploy-")
    assert first != changed


def test_signal_command_serializes_marketpilot_payload_with_trace_fields():
    intent = _order_intent()
    command = MarketPilotSignalCommand.from_order_intent(
        intent,
        correlation_id="corr-001",
        signal_id="sig-001",
        expires_at_utc=datetime(2026, 6, 16, 13, 40, tzinfo=UTC),
    )

    payload = command.to_payload()

    assert payload == {
        "command_type": "marketpilot_signal",
        "correlation_id": "corr-001",
        "signal_id": "sig-001",
        "idempotency_key": "order-intent-abc123",
        "symbol": "MSFT",
        "quantity": 10,
        "signal_time_utc": "2026-06-16T13:30:00+00:00",
        "expires_at_utc": "2026-06-16T13:40:00+00:00",
        "strategy_mode": "daily_only",
        "primary_setup": "trend_pullback",
        "paper_trading_only": True,
        "command_delivery_is_order_execution": False,
    }
    assert "token" not in str(payload).lower()
    assert "password" not in str(payload).lower()


def test_signal_freshness_policy_accepts_utc_signal_within_ttl():
    policy = SignalFreshnessPolicy(ttl_seconds=600)
    decision = policy.evaluate(
        signal_time_utc=datetime(2026, 6, 16, 13, 30, tzinfo=UTC),
        expires_at_utc=datetime(2026, 6, 16, 13, 40, tzinfo=UTC),
        now_utc=datetime(2026, 6, 16, 13, 35, tzinfo=UTC),
    )

    assert decision.accepted is True
    assert decision.reason == "fresh"
    assert decision.age_seconds == 300


@pytest.mark.parametrize(
    ("signal_time", "expires_at", "expected_reason"),
    [
        (None, datetime(2026, 6, 16, 13, 40, tzinfo=UTC), "missing_signal_time_utc"),
        (datetime(2026, 6, 16, 13, 30), datetime(2026, 6, 16, 13, 40, tzinfo=UTC), "naive_signal_time_utc"),
        (datetime(2026, 6, 16, 13, 20, tzinfo=UTC), datetime(2026, 6, 16, 13, 40, tzinfo=UTC), "stale_signal"),
        (datetime(2026, 6, 16, 13, 30, tzinfo=UTC), datetime(2026, 6, 16, 13, 34, tzinfo=UTC), "expired_signal"),
        (datetime(2026, 6, 16, 13, 30, tzinfo=UTC), datetime(2026, 6, 16, 13, 29, tzinfo=UTC), "expires_before_signal_time"),
    ],
)
def test_signal_freshness_policy_rejects_unsafe_timestamps(signal_time, expires_at, expected_reason):
    policy = SignalFreshnessPolicy(ttl_seconds=600)
    decision = policy.evaluate(
        signal_time_utc=signal_time,
        expires_at_utc=expires_at,
        now_utc=datetime(2026, 6, 16, 13, 35, tzinfo=UTC),
    )

    assert decision.accepted is False
    assert decision.reason == expected_reason


def test_order_tag_round_trip_recovers_signal_and_idempotency_without_secrets():
    tag = build_order_tag(signal_id="sig-001", idempotency_key="order-intent-abc123")

    assert tag == "mp:sig-001:order-intent-abc123"
    assert len(tag) < 128
    assert parse_order_tag(tag) == {
        "signal_id": "sig-001",
        "idempotency_key": "order-intent-abc123",
    }
    assert "token" not in tag.lower()
    assert "secret" not in tag.lower()
