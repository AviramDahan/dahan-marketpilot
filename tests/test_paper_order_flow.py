"""Offline tests for paper deployment and signal command flow."""

from __future__ import annotations

import json
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
from marketpilot.paper_order_flow import deploy_paper_algorithm, submit_signal_command


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


class FakeQCApiClient:
    def __init__(self) -> None:
        self.deploy_calls: list[dict[str, object]] = []
        self.command_calls: list[dict[str, object]] = []

    def create_live_algorithm(self, **kwargs):
        self.deploy_calls.append(kwargs)
        return {"success": True, "deployId": "L-paper-001"}

    def create_live_command(self, **kwargs):
        self.command_calls.append(kwargs)
        return True


def _write_sync_record(path, *, source_timestamp, sync_status="success", reconciliation_clean=True):
    path.write_text(
        json.dumps(
            {
                "generation": 1,
                "source_timestamp": source_timestamp,
                "captured_at": source_timestamp,
                "sync_status": sync_status,
                "reconciliation_clean": reconciliation_clean,
                "portfolio": {"cash": "100000"},
                "orders_count": 0,
                "fills_count": 0,
                "deployment_status": "running",
                "algorithm_status": "running",
                "error_detail": None,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _append_sync_record(path, *, source_timestamp, sync_status="success", reconciliation_clean=True):
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(
            json.dumps(
                {
                    "generation": 2,
                    "source_timestamp": source_timestamp,
                    "captured_at": source_timestamp,
                    "sync_status": sync_status,
                    "reconciliation_clean": reconciliation_clean,
                    "portfolio": {"cash": "100000"},
                    "orders_count": 0,
                    "fills_count": 0,
                    "deployment_status": "running",
                    "algorithm_status": "running",
                    "error_detail": None,
                },
                sort_keys=True,
            )
            + "\n"
        )


def test_duplicate_deployment_key_is_rejected_before_api_call(tmp_path):
    client = FakeQCApiClient()
    ledger_path = tmp_path / "paper_deployments.jsonl"
    kwargs = {
        "project_id": 123,
        "compile_id": "C-1",
        "node_id": "N-1",
        "version_id": "-1",
        "data_providers": {"QuantConnectBrokerage": {"id": "QuantConnectBrokerage"}},
        "strategy_version": "strategy-v1",
        "config_version": "config-v1",
        "ledger_path": ledger_path,
        "client": client,
    }

    first = deploy_paper_algorithm(**kwargs)
    second = deploy_paper_algorithm(**kwargs)

    assert first.status == "deployed"
    assert first.api_called is True
    assert second.status == "duplicate_deployment_rejected"
    assert second.api_called is False
    assert len(client.deploy_calls) == 1


def test_submit_signal_command_delivers_after_fresh_clean_sync(tmp_path):
    client = FakeQCApiClient()
    now = datetime(2026, 6, 16, 13, 35, tzinfo=UTC)
    sync_path = tmp_path / "portfolio_sync.jsonl"
    audit_path = tmp_path / "paper_audit.jsonl"
    ledger_path = tmp_path / "paper_signal_ledger.jsonl"
    _write_sync_record(sync_path, source_timestamp=(now - timedelta(seconds=300)).isoformat())

    result = submit_signal_command(
        project_id=123,
        deploy_id="L-paper-001",
        intent=_order_intent(signal_time=now - timedelta(seconds=120)),
        correlation_id="corr-001",
        signal_id="sig-001",
        expires_at_utc=now + timedelta(seconds=480),
        sync_jsonl_path=sync_path,
        ledger_path=ledger_path,
        audit_journal_path=audit_path,
        client=client,
        now_utc=now,
    )

    assert result.status == "command_delivered"
    assert result.command_delivered is True
    assert result.order_executed is False
    assert len(client.command_calls) == 1
    assert client.command_calls[0]["project_id"] == 123
    command = client.command_calls[0]["command"]
    assert command["command_type"] == "marketpilot_signal"
    assert command["signal_id"] == "sig-001"
    assert command["idempotency_key"] == "order-intent-abc123"
    records = [json.loads(line) for line in audit_path.read_text(encoding="utf-8").splitlines()]
    assert records[-1]["event_type"] == "paper_signal_command_delivered"
    assert records[-1]["payload"]["command_delivered"] is True
    assert records[-1]["payload"]["order_executed"] is False


def test_submit_signal_command_uses_latest_sync_record_only(tmp_path):
    client = FakeQCApiClient()
    now = datetime(2026, 6, 16, 13, 35, tzinfo=UTC)
    sync_path = tmp_path / "portfolio_sync.jsonl"
    audit_path = tmp_path / "paper_audit.jsonl"
    ledger_path = tmp_path / "paper_signal_ledger.jsonl"
    _write_sync_record(sync_path, source_timestamp=(now - timedelta(seconds=3600)).isoformat())
    _append_sync_record(sync_path, source_timestamp=(now - timedelta(seconds=60)).isoformat())

    result = submit_signal_command(
        project_id=123,
        deploy_id="L-paper-001",
        intent=_order_intent(signal_time=now - timedelta(seconds=120)),
        correlation_id="corr-001",
        signal_id="sig-001",
        expires_at_utc=now + timedelta(seconds=480),
        sync_jsonl_path=sync_path,
        ledger_path=ledger_path,
        audit_journal_path=audit_path,
        client=client,
        now_utc=now,
    )

    assert result.status == "command_delivered"
    assert len(client.command_calls) == 1


@pytest.mark.parametrize(
    ("record", "expected_status", "expected_reason"),
    [
        (None, "sync_gate_blocked", "missing_sync_record"),
        ({"source_timestamp": "2026-06-16T13:20:00+00:00", "sync_status": "success", "reconciliation_clean": True}, "sync_gate_blocked", "stale_sync_record"),
        ({"source_timestamp": "2026-06-16T13:34:00", "sync_status": "success", "reconciliation_clean": True}, "sync_gate_blocked", "naive_sync_source_timestamp"),
        ({"source_timestamp": "not-a-time", "sync_status": "success", "reconciliation_clean": True}, "sync_gate_blocked", "invalid_sync_source_timestamp"),
        ({"source_timestamp": "2026-06-16T13:34:00+00:00", "sync_status": "api_error", "reconciliation_clean": True}, "sync_gate_blocked", "sync_status_api_error"),
        ({"source_timestamp": "2026-06-16T13:34:00+00:00", "sync_status": "success", "reconciliation_clean": False}, "sync_gate_blocked", "reconciliation_not_clean"),
    ],
)
def test_sync_gate_blocks_without_api_call_and_writes_audit(tmp_path, record, expected_status, expected_reason):
    client = FakeQCApiClient()
    now = datetime(2026, 6, 16, 13, 35, tzinfo=UTC)
    sync_path = tmp_path / "portfolio_sync.jsonl"
    audit_path = tmp_path / "paper_audit.jsonl"
    ledger_path = tmp_path / "paper_signal_ledger.jsonl"
    if record is not None:
        sync_path.write_text(json.dumps(record) + "\n", encoding="utf-8")

    result = submit_signal_command(
        project_id=123,
        deploy_id="L-paper-001",
        intent=_order_intent(signal_time=now - timedelta(seconds=120)),
        correlation_id="corr-001",
        signal_id="sig-001",
        expires_at_utc=now + timedelta(seconds=480),
        sync_jsonl_path=sync_path,
        ledger_path=ledger_path,
        audit_journal_path=audit_path,
        client=client,
        now_utc=now,
    )

    assert result.status == expected_status
    assert result.reason == expected_reason
    assert result.command_delivered is False
    assert result.order_executed is False
    assert client.command_calls == []
    records = [json.loads(line) for line in audit_path.read_text(encoding="utf-8").splitlines()]
    assert records[-1]["event_type"] == "paper_signal_sync_blocked"
    assert records[-1]["payload"]["reason"] == expected_reason


def test_stale_signal_skips_without_api_call(tmp_path):
    client = FakeQCApiClient()
    now = datetime(2026, 6, 16, 13, 35, tzinfo=UTC)
    sync_path = tmp_path / "portfolio_sync.jsonl"
    audit_path = tmp_path / "paper_audit.jsonl"
    ledger_path = tmp_path / "paper_signal_ledger.jsonl"
    _write_sync_record(sync_path, source_timestamp=(now - timedelta(seconds=60)).isoformat())

    result = submit_signal_command(
        project_id=123,
        deploy_id="L-paper-001",
        intent=_order_intent(signal_time=now - timedelta(seconds=1200)),
        correlation_id="corr-001",
        signal_id="sig-001",
        expires_at_utc=now + timedelta(seconds=60),
        sync_jsonl_path=sync_path,
        ledger_path=ledger_path,
        audit_journal_path=audit_path,
        client=client,
        now_utc=now,
    )

    assert result.status == "signal_skipped"
    assert result.reason == "stale_signal"
    assert client.command_calls == []
    records = [json.loads(line) for line in audit_path.read_text(encoding="utf-8").splitlines()]
    assert records[-1]["event_type"] == "paper_signal_skipped"
    assert records[-1]["payload"]["reason"] == "stale_signal"


def test_duplicate_signal_is_rejected_before_api_call_and_writes_audit(tmp_path):
    client = FakeQCApiClient()
    now = datetime(2026, 6, 16, 13, 35, tzinfo=UTC)
    sync_path = tmp_path / "portfolio_sync.jsonl"
    audit_path = tmp_path / "paper_audit.jsonl"
    ledger_path = tmp_path / "paper_signal_ledger.jsonl"
    _write_sync_record(sync_path, source_timestamp=(now - timedelta(seconds=60)).isoformat())
    kwargs = {
        "project_id": 123,
        "deploy_id": "L-paper-001",
        "intent": _order_intent(signal_time=now - timedelta(seconds=120)),
        "correlation_id": "corr-001",
        "signal_id": "sig-001",
        "expires_at_utc": now + timedelta(seconds=480),
        "sync_jsonl_path": sync_path,
        "ledger_path": ledger_path,
        "audit_journal_path": audit_path,
        "client": client,
        "now_utc": now,
    }

    first = submit_signal_command(**kwargs)
    second = submit_signal_command(**kwargs)

    assert first.status == "command_delivered"
    assert second.status == "duplicate_signal_rejected"
    assert second.reason == "duplicate_signal_idempotency_key"
    assert len(client.command_calls) == 1
    records = [json.loads(line) for line in audit_path.read_text(encoding="utf-8").splitlines()]
    assert records[-1]["event_type"] == "paper_signal_duplicate_rejected"
