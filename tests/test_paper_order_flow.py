"""Offline tests for paper deployment and signal command flow."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from marketpilot.order_lifecycle import OrderIntent, OrderLifecycleState
from marketpilot.paper_command_models import (
    MarketPilotSignalCommand,
    SignalFreshnessPolicy,
    build_deployment_idempotency_key,
    build_order_tag,
    parse_order_tag,
)
from marketpilot.paper_order_flow import (
    deploy_paper_algorithm,
    parse_quantconnect_live_order,
    parse_quantconnect_live_orders,
    poll_quantconnect_order_updates,
    read_signal_order_fill_trace,
    submit_signal_command,
)


UTC = timezone.utc


def _qc_order_payload(**overrides):
    payload = {
        "id": 701,
        "symbol": {"value": "MSFT"},
        "status": "Submitted",
        "quantity": 10,
        "quantityFilled": 0,
        "remainingQuantity": 10,
        "averageFillPrice": None,
        "createdTime": "2026-06-16T13:36:00Z",
        "lastFillTime": None,
        "tag": "mp:sig-001:order-intent-abc123",
    }
    payload.update(overrides)
    return payload


def test_live_order_parser_maps_status_and_marketpilot_tag():
    parsed = parse_quantconnect_live_order(_qc_order_payload())

    assert parsed.quantconnect_order_id == "701"
    assert parsed.signal_id == "sig-001"
    assert parsed.idempotency_key == "order-intent-abc123"
    assert parsed.lifecycle_state is OrderLifecycleState.SUBMITTED
    assert parsed.raw_status == "Submitted"
    assert parsed.quantity == 10
    assert parsed.filled_quantity == 0
    assert parsed.remaining_quantity == 10
    assert parsed.submitted_at.isoformat() == "2026-06-16T13:36:00+00:00"
    assert parsed.parse_warnings == ()


def test_live_order_parser_maps_quantconnect_numeric_filled_status():
    parsed = parse_quantconnect_live_order(
        _qc_order_payload(status=3, quantityFilled=10, remainingQuantity=0, averageFillPrice="421.25")
    )

    assert parsed.lifecycle_state is OrderLifecycleState.FILLED
    assert parsed.raw_status == "3"
    assert parsed.filled_quantity == 10


@pytest.mark.parametrize(
    ("raw_status", "filled_quantity", "remaining_quantity", "expected_state"),
    [
        ("PartiallyFilled", 4, 6, OrderLifecycleState.PARTIALLY_FILLED),
        ("Filled", 10, 0, OrderLifecycleState.FILLED),
        ("Canceled", 0, 10, OrderLifecycleState.CANCELED),
    ],
)
def test_live_order_parser_preserves_partial_filled_and_canceled_quantities(
    raw_status, filled_quantity, remaining_quantity, expected_state
):
    parsed = parse_quantconnect_live_order(
        _qc_order_payload(
            status=raw_status,
            quantityFilled=filled_quantity,
            remainingQuantity=remaining_quantity,
            averageFillPrice="421.25" if filled_quantity else None,
            lastFillTime="2026-06-16T13:38:00Z" if filled_quantity else None,
        )
    )

    assert parsed.lifecycle_state is expected_state
    assert parsed.raw_status == raw_status
    assert parsed.filled_quantity == filled_quantity
    assert parsed.remaining_quantity == remaining_quantity
    if filled_quantity:
        assert parsed.average_fill_price == "421.25"
        assert parsed.last_fill_at.isoformat() == "2026-06-16T13:38:00+00:00"


def test_live_order_parser_preserves_rejection_reason():
    parsed = parse_quantconnect_live_order(
        _qc_order_payload(
            status="Invalid",
            quantityFilled=0,
            remainingQuantity=10,
            message="insufficient buying power",
        )
    )

    assert parsed.lifecycle_state is OrderLifecycleState.REJECTED
    assert parsed.rejection_reason == "insufficient buying power"
    assert parsed.raw_status == "Invalid"
    assert parsed.raw_payload["message"] == "insufficient buying power"


def test_live_order_parser_flags_unknown_status_and_preserves_raw_evidence():
    payload = _qc_order_payload(status="BrokeragePendingReview", unexpected={"raw": True})

    parsed = parse_quantconnect_live_order(payload)

    assert parsed.lifecycle_state is None
    assert parsed.raw_status == "BrokeragePendingReview"
    assert "unknown_order_status" in parsed.parse_warnings
    assert parsed.raw_payload == payload


def test_live_order_parser_does_not_infer_fill_without_quantconnect_fill_data():
    parsed = parse_quantconnect_live_order(
        _qc_order_payload(
            status="Filled",
            quantityFilled=None,
            filledQuantity=None,
            fillQuantity=None,
            remainingQuantity=None,
            averageFillPrice=None,
            lastFillTime=None,
        )
    )

    assert parsed.lifecycle_state is OrderLifecycleState.FILLED
    assert parsed.filled_quantity is None
    assert parsed.remaining_quantity is None
    assert parsed.average_fill_price is None
    assert parsed.last_fill_at is None
    assert "missing_filled_quantity" in parsed.parse_warnings


def test_live_orders_parser_accepts_raw_page_mapping():
    parsed = parse_quantconnect_live_orders(
        {
            "success": True,
            "orders": {
                "701": _qc_order_payload(id=701, status="Submitted"),
                "702": _qc_order_payload(id=702, status="Filled", quantityFilled=10, remainingQuantity=0),
            },
        }
    )

    assert [order.quantconnect_order_id for order in parsed] == ["701", "702"]
    assert [order.lifecycle_state for order in parsed] == [
        OrderLifecycleState.SUBMITTED,
        OrderLifecycleState.FILLED,
    ]


class FakeLiveOrdersClient:
    def __init__(self, orders) -> None:
        self.orders = orders
        self.calls: list[dict[str, object]] = []

    def read_live_orders(self, **kwargs):
        self.calls.append(kwargs)
        return self.orders


def _audit_records(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_fill_poll_appends_audit_record(tmp_path):
    audit_path = tmp_path / "paper_audit.jsonl"
    client = FakeLiveOrdersClient(
        [
            _qc_order_payload(status="Submitted", quantityFilled=0, remainingQuantity=10),
            _qc_order_payload(id=702, status="PartiallyFilled", quantityFilled=4, remainingQuantity=6, averageFillPrice="421.25"),
            _qc_order_payload(id=703, status="Filled", quantityFilled=10, remainingQuantity=0, averageFillPrice="422.00"),
            _qc_order_payload(id=704, status="Invalid", quantityFilled=0, remainingQuantity=10, message="insufficient buying power"),
            _qc_order_payload(id=705, status="BrokeragePendingReview"),
        ]
    )

    result = poll_quantconnect_order_updates(
        project_id=123,
        deploy_id="L-paper-001",
        audit_journal_path=audit_path,
        correlation_id="corr-fill-poll",
        client=client,
        observed_at_utc=datetime(2026, 6, 16, 13, 45, tzinfo=UTC),
    )

    assert client.calls == [{"project_id": 123, "deploy_id": "L-paper-001"}]
    assert result.observed_count == 5
    assert result.audit_record_count == 5
    assert result.warning_count == 1

    records = _audit_records(audit_path)
    assert [record["event_type"] for record in records] == [
        "paper_order_observed",
        "paper_fill_observed",
        "paper_fill_observed",
        "paper_order_rejected",
        "paper_order_observed",
    ]
    fill_payload = records[1]["payload"]
    assert fill_payload["source_authority"] == "quantconnect"
    assert fill_payload["local_authority"] is False
    assert fill_payload["paper_trading_only"] is True
    assert fill_payload["correlation_id"] == "corr-fill-poll"
    assert fill_payload["quantconnect_order_id"] == "702"
    assert fill_payload["signal_id"] == "sig-001"
    assert fill_payload["idempotency_key"] == "order-intent-abc123"
    assert fill_payload["status"] == "partially_filled"
    assert fill_payload["raw_status"] == "PartiallyFilled"
    assert fill_payload["filled_quantity"] == 4
    assert fill_payload["remaining_quantity"] == 6
    assert fill_payload["average_fill_price"] == "421.25"

    rejection_payload = records[3]["payload"]
    assert rejection_payload["rejection_reason"] == "insufficient buying power"
    assert rejection_payload["raw_status"] == "Invalid"

    unknown_payload = records[4]["payload"]
    assert unknown_payload["status"] == "unknown"
    assert unknown_payload["parse_warnings"] == ["unknown_order_status"]
    assert unknown_payload["raw_payload"]["status"] == "BrokeragePendingReview"


def test_fill_poll_filters_to_expected_signal_and_idempotency_key(tmp_path):
    audit_path = tmp_path / "paper_audit.jsonl"
    client = FakeLiveOrdersClient(
        [
            _qc_order_payload(id=701, tag="mp:old-sig:old-key", status="Filled", quantityFilled=10, remainingQuantity=0),
            _qc_order_payload(id=702, tag="mp:sig-expected:order-intent-expected", status=3, quantityFilled=10, remainingQuantity=0),
        ]
    )

    result = poll_quantconnect_order_updates(
        project_id=123,
        deploy_id="L-paper-001",
        audit_journal_path=audit_path,
        correlation_id="corr-filter",
        expected_signal_id="sig-expected",
        expected_idempotency_key="order-intent-expected",
        client=client,
        observed_at_utc=datetime(2026, 6, 16, 13, 45, tzinfo=UTC),
    )

    assert result.observed_count == 1
    assert result.audit_record_count == 1
    assert result.observations[0].quantconnect_order_id == "702"
    records = _audit_records(audit_path)
    assert records[0]["payload"]["signal_id"] == "sig-expected"
    assert records[0]["payload"]["idempotency_key"] == "order-intent-expected"


def test_fill_poll_with_expected_signal_does_not_audit_unrelated_orders(tmp_path):
    audit_path = tmp_path / "paper_audit.jsonl"
    client = FakeLiveOrdersClient(
        [_qc_order_payload(id=701, tag="mp:old-sig:old-key", status=3, quantityFilled=10, remainingQuantity=0)]
    )

    result = poll_quantconnect_order_updates(
        project_id=123,
        deploy_id="L-paper-001",
        audit_journal_path=audit_path,
        correlation_id="corr-filter-empty",
        expected_signal_id="sig-current",
        expected_idempotency_key="order-intent-current",
        client=client,
        observed_at_utc=datetime(2026, 6, 16, 13, 45, tzinfo=UTC),
    )

    assert result.observed_count == 0
    assert result.audit_record_count == 0
    assert not audit_path.exists()


def test_fill_poll_does_not_append_fill_without_quantconnect_fill_data(tmp_path):
    audit_path = tmp_path / "paper_audit.jsonl"
    client = FakeLiveOrdersClient(
        [
            _qc_order_payload(
                status="Filled",
                quantityFilled=None,
                remainingQuantity=None,
                averageFillPrice=None,
                lastFillTime=None,
            )
        ]
    )

    result = poll_quantconnect_order_updates(
        project_id=123,
        deploy_id="L-paper-001",
        audit_journal_path=audit_path,
        correlation_id="corr-no-infer",
        client=client,
        observed_at_utc=datetime(2026, 6, 16, 13, 45, tzinfo=UTC),
    )

    assert result.observed_count == 1
    assert result.audit_record_count == 1
    records = _audit_records(audit_path)
    assert records[0]["event_type"] == "paper_order_observed"
    assert records[0]["payload"]["status"] == "filled"
    assert records[0]["payload"]["filled_quantity"] is None
    assert "missing_filled_quantity" in records[0]["payload"]["parse_warnings"]


def test_trace_chain_returns_signal_order_fill_records(tmp_path):
    audit_path = tmp_path / "paper_audit.jsonl"
    sync_path = tmp_path / "sync.jsonl"
    _write_sync_record(sync_path, source_timestamp="2026-06-16T13:34:00+00:00")
    client = FakeLiveOrdersClient(
        [
            _qc_order_payload(id=701, status="Submitted", quantityFilled=0, remainingQuantity=10),
            _qc_order_payload(id=702, status="Filled", quantityFilled=10, remainingQuantity=0, averageFillPrice="422.00"),
        ]
    )
    submit_signal_command(
        project_id=123,
        deploy_id="L-paper-001",
        intent=_order_intent(signal_time=datetime(2026, 6, 16, 13, 30, tzinfo=UTC)),
        correlation_id="corr-trace",
        signal_id="sig-001",
        expires_at_utc=datetime(2026, 6, 16, 13, 50, tzinfo=UTC),
        sync_jsonl_path=sync_path,
        ledger_path=tmp_path / "signal_ledger.jsonl",
        audit_journal_path=audit_path,
        client=FakeQCApiClient(),
        now_utc=datetime(2026, 6, 16, 13, 35, tzinfo=UTC),
    )
    poll_quantconnect_order_updates(
        project_id=123,
        deploy_id="L-paper-001",
        audit_journal_path=audit_path,
        correlation_id="corr-trace",
        client=client,
        observed_at_utc=datetime(2026, 6, 16, 13, 45, tzinfo=UTC),
    )

    trace = read_signal_order_fill_trace(audit_journal_path=audit_path, signal_id="sig-001")

    assert [record["event_type"] for record in trace] == [
        "paper_signal_command_delivered",
        "paper_order_observed",
        "paper_fill_observed",
    ]
    assert [record["payload"].get("quantconnect_order_id") for record in trace] == [None, "701", "702"]

    by_key = read_signal_order_fill_trace(
        audit_journal_path=audit_path,
        idempotency_key="order-intent-abc123",
    )
    assert by_key == trace


def test_trace_query_requires_signal_or_idempotency_key(tmp_path):
    with pytest.raises(ValueError, match="signal_id or idempotency_key"):
        read_signal_order_fill_trace(audit_journal_path=tmp_path / "paper_audit.jsonl")


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
        self.object_store_uploads: list[dict[str, object]] = []

    def create_live_algorithm(self, **kwargs):
        self.deploy_calls.append(kwargs)
        return {"success": True, "deployId": "L-paper-001"}

    def create_live_command(self, **kwargs):
        self.command_calls.append(kwargs)
        return True

    def upload_object_store_file(self, **kwargs):
        self.object_store_uploads.append(kwargs)
        return {"success": True}


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


def test_submit_signal_command_can_deliver_via_quantconnect_object_store(tmp_path, monkeypatch):
    client = FakeQCApiClient()
    now = datetime(2026, 6, 16, 13, 35, tzinfo=UTC)
    sync_path = tmp_path / "portfolio_sync.jsonl"
    audit_path = tmp_path / "paper_audit.jsonl"
    ledger_path = tmp_path / "paper_signal_ledger.jsonl"
    _write_sync_record(sync_path, source_timestamp=(now - timedelta(seconds=300)).isoformat())
    monkeypatch.setenv("MARKETPILOT_QC_SIGNAL_TRANSPORT", "object_store")
    monkeypatch.setenv("QC_ORGANIZATION_ID", "org-safe")
    monkeypatch.setenv("MARKETPILOT_QC_OBJECT_STORE_SIGNAL_KEY", "123/marketpilot/signals/operator-probe.json")

    result = submit_signal_command(
        project_id=123,
        deploy_id="L-paper-001",
        intent=_order_intent(signal_time=now - timedelta(seconds=120)),
        correlation_id="corr-object-store",
        signal_id="sig-object-store",
        expires_at_utc=now + timedelta(seconds=480),
        sync_jsonl_path=sync_path,
        ledger_path=ledger_path,
        audit_journal_path=audit_path,
        client=client,
        now_utc=now,
    )

    assert result.status == "command_delivered"
    assert result.command_delivered is True
    assert client.command_calls == []
    assert len(client.object_store_uploads) == 1
    upload = client.object_store_uploads[0]
    assert upload["key"] == "123/marketpilot/signals/operator-probe.json"
    assert json.loads(upload["content"].decode("utf-8"))["correlation_id"] == "corr-object-store"
    records = _audit_records(audit_path)
    assert records[-1]["payload"]["transport"] == "object_store"


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
