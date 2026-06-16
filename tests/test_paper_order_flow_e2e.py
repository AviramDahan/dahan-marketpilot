"""Offline E2E tests for the simulated paper order flow.

These tests intentionally use fake QuantConnect clients, fake sync records, and
fake LEAN runtime objects. They prove local behavior only; they are not evidence
of real QuantConnect paper execution.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

from marketpilot.order_lifecycle import OrderIntent
from marketpilot.paper_order_flow import (
    poll_quantconnect_order_updates,
    read_signal_order_fill_trace,
    submit_signal_command,
)


ROOT = Path(__file__).resolve().parents[1]
LEAN_MAIN = ROOT / "lean" / "main.py"
UTC = timezone.utc
NOW = datetime(2026, 6, 16, 14, 30, tzinfo=UTC)


class FakePaperFlowClient:
    def __init__(self, *, live_orders=None) -> None:
        self.command_calls: list[dict[str, object]] = []
        self.live_order_calls: list[dict[str, object]] = []
        self.live_orders = live_orders or []

    def create_live_command(self, **kwargs):
        self.command_calls.append(kwargs)
        return True

    def read_live_orders(self, **kwargs):
        self.live_order_calls.append(kwargs)
        return self.live_orders


def test_signal_to_command_to_fill_trace(tmp_path, monkeypatch):
    sync_path = tmp_path / "portfolio_sync.jsonl"
    ledger_path = tmp_path / "signal_ledger.jsonl"
    audit_path = tmp_path / "paper_audit.jsonl"
    _write_sync_record(sync_path, source_timestamp=(NOW - timedelta(seconds=60)).isoformat())
    client = FakePaperFlowClient(live_orders=[_qc_order(status="Filled", quantityFilled=10, remainingQuantity=0)])

    submission = submit_signal_command(
        project_id=123,
        deploy_id="L-paper-001",
        intent=_order_intent(signal_time=NOW - timedelta(seconds=120)),
        correlation_id="corr-e2e-happy",
        signal_id="sig-001",
        expires_at_utc=NOW + timedelta(seconds=300),
        sync_jsonl_path=sync_path,
        ledger_path=ledger_path,
        audit_journal_path=audit_path,
        client=client,
        now_utc=NOW,
    )

    assert submission.status == "command_delivered"
    assert submission.command_delivered is True
    assert submission.order_executed is False
    assert len(client.command_calls) == 1
    command_payload = client.command_calls[0]["command"]
    assert command_payload["command_delivery_is_order_execution"] is False

    algorithm = _algorithm(monkeypatch)
    assert algorithm.on_command(command_payload) is True
    assert algorithm.market_orders == [
        {"symbol": "MSFT", "quantity": 10, "tag": "mp:sig-001:order-intent-abc123"}
    ]

    poll = poll_quantconnect_order_updates(
        project_id=123,
        deploy_id="L-paper-001",
        audit_journal_path=audit_path,
        correlation_id="corr-e2e-happy",
        client=client,
        observed_at_utc=NOW + timedelta(minutes=5),
    )
    assert client.live_order_calls == [{"project_id": 123, "deploy_id": "L-paper-001"}]
    assert poll.observed_count == 1
    assert poll.audit_record_count == 1
    assert poll.observations[0].signal_id == "sig-001"

    trace = read_signal_order_fill_trace(audit_journal_path=audit_path, signal_id="sig-001")
    assert [record["event_type"] for record in trace] == [
        "paper_signal_command_delivered",
        "paper_fill_observed",
    ]
    assert trace[0]["payload"]["order_executed"] is False
    assert trace[1]["payload"]["source_authority"] == "quantconnect"
    assert trace[1]["payload"]["local_authority"] is False
    assert trace[1]["payload"]["filled_quantity"] == 10


def test_duplicate_signal_is_rejected_before_api_and_before_lean_order(tmp_path, monkeypatch):
    sync_path = tmp_path / "portfolio_sync.jsonl"
    ledger_path = tmp_path / "signal_ledger.jsonl"
    audit_path = tmp_path / "paper_audit.jsonl"
    _write_sync_record(sync_path, source_timestamp=(NOW - timedelta(seconds=60)).isoformat())
    client = FakePaperFlowClient()
    kwargs = {
        "project_id": 123,
        "deploy_id": "L-paper-001",
        "intent": _order_intent(signal_time=NOW - timedelta(seconds=120)),
        "correlation_id": "corr-e2e-duplicate",
        "signal_id": "sig-001",
        "expires_at_utc": NOW + timedelta(seconds=300),
        "sync_jsonl_path": sync_path,
        "ledger_path": ledger_path,
        "audit_journal_path": audit_path,
        "client": client,
        "now_utc": NOW,
    }

    first = submit_signal_command(**kwargs)
    second = submit_signal_command(**kwargs)

    assert first.status == "command_delivered"
    assert second.status == "duplicate_signal_rejected"
    assert second.command_delivered is False
    assert second.order_executed is False
    assert len(client.command_calls) == 1

    algorithm = _algorithm(monkeypatch)
    assert algorithm.on_command(first.command_payload) is True
    assert algorithm.on_command(first.command_payload) is False
    assert algorithm.market_orders == [
        {"symbol": "MSFT", "quantity": 10, "tag": "mp:sig-001:order-intent-abc123"}
    ]

    records = _audit_records(audit_path)
    assert records[-1]["event_type"] == "paper_signal_duplicate_rejected"
    assert records[-1]["payload"]["command_delivered"] is False
    assert records[-1]["payload"]["order_executed"] is False


def test_stale_signal_skips_locally_and_direct_lean_injection_is_rejected(tmp_path, monkeypatch):
    sync_path = tmp_path / "portfolio_sync.jsonl"
    ledger_path = tmp_path / "signal_ledger.jsonl"
    audit_path = tmp_path / "paper_audit.jsonl"
    _write_sync_record(sync_path, source_timestamp=(NOW - timedelta(seconds=60)).isoformat())
    client = FakePaperFlowClient()

    result = submit_signal_command(
        project_id=123,
        deploy_id="L-paper-001",
        intent=_order_intent(signal_time=NOW - timedelta(seconds=1200)),
        correlation_id="corr-e2e-stale",
        signal_id="sig-001",
        expires_at_utc=NOW - timedelta(seconds=60),
        sync_jsonl_path=sync_path,
        ledger_path=ledger_path,
        audit_journal_path=audit_path,
        client=client,
        now_utc=NOW,
    )

    assert result.status == "signal_skipped"
    assert result.reason == "stale_signal"
    assert client.command_calls == []

    algorithm = _algorithm(monkeypatch)
    assert algorithm.on_command(result.command_payload) is False
    assert getattr(algorithm, "market_orders", []) == []
    assert algorithm.latest_command_rejection_evidence["reason"] == "expired_signal"

    records = _audit_records(audit_path)
    assert records[-1]["event_type"] == "paper_signal_skipped"
    assert records[-1]["payload"]["reason"] == "stale_signal"
    assert records[-1]["payload"]["command_delivered"] is False
    assert records[-1]["payload"]["order_executed"] is False


def test_partial_fill_and_rejection_evidence_are_traceable_from_qc_poll(tmp_path):
    audit_path = tmp_path / "paper_audit.jsonl"
    client = FakePaperFlowClient(
        live_orders=[
            _qc_order(id=701, status="PartiallyFilled", quantityFilled=4, remainingQuantity=6),
            _qc_order(id=702, status="Invalid", quantityFilled=0, remainingQuantity=10, message="insufficient buying power"),
        ]
    )

    poll = poll_quantconnect_order_updates(
        project_id=123,
        deploy_id="L-paper-001",
        audit_journal_path=audit_path,
        correlation_id="corr-e2e-poll",
        client=client,
        observed_at_utc=NOW,
    )

    assert poll.observed_count == 2
    assert [observation.raw_status for observation in poll.observations] == ["PartiallyFilled", "Invalid"]
    assert poll.observations[0].filled_quantity == 4
    assert poll.observations[1].rejection_reason == "insufficient buying power"

    trace = read_signal_order_fill_trace(audit_journal_path=audit_path, idempotency_key="order-intent-abc123")
    assert [record["event_type"] for record in trace] == [
        "paper_fill_observed",
        "paper_order_rejected",
    ]
    assert trace[0]["payload"]["status"] == "partially_filled"
    assert trace[0]["payload"]["filled_quantity"] == 4
    assert trace[1]["payload"]["status"] == "rejected"
    assert trace[1]["payload"]["rejection_reason"] == "insufficient buying power"


def _order_intent(*, signal_time: datetime) -> OrderIntent:
    return OrderIntent(
        idempotency_key="order-intent-abc123",
        symbol="MSFT",
        primary_setup="trend_pullback",
        strategy_mode="daily_only",
        signal_time=signal_time,
        portfolio_epoch="sync-gen-7",
        quantity=10,
        entry_price=Decimal("420.00"),
        stop_price=Decimal("400.00"),
        target_price=Decimal("460.00"),
        audit_metadata={"risk_decision_id": "risk-1"},
    )


def _qc_order(**overrides):
    payload = {
        "id": 701,
        "symbol": {"value": "MSFT"},
        "status": "Submitted",
        "quantity": 10,
        "quantityFilled": 0,
        "remainingQuantity": 10,
        "averageFillPrice": "421.25",
        "createdTime": "2026-06-16T14:31:00Z",
        "lastFillTime": "2026-06-16T14:32:00Z",
        "tag": "mp:sig-001:order-intent-abc123",
    }
    payload.update(overrides)
    return payload


def _write_sync_record(path: Path, *, source_timestamp: str) -> None:
    path.write_text(
        json.dumps(
            {
                "generation": 1,
                "source_timestamp": source_timestamp,
                "captured_at": source_timestamp,
                "sync_status": "success",
                "reconciliation_clean": True,
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


def _audit_records(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _algorithm(monkeypatch):
    module = _load_lean_main(monkeypatch)
    algorithm = module.DahanMarketPilotRuntime()
    algorithm.time = NOW
    algorithm.initialize()
    return algorithm


def _load_lean_main(monkeypatch):
    class FakeQCAlgorithm:
        def set_start_date(self, *args):
            self.start_date = args

        def set_end_date(self, *args):
            self.end_date = args

        def set_cash(self, cash):
            self.cash = cash

        def add_equity(self, symbol, resolution):
            self.equities = getattr(self, "equities", [])
            self.equities.append((symbol, resolution))
            return SimpleNamespace(Symbol=symbol)

        def add_universe(self, selector):
            self.universe_selector = selector

        def debug(self, message):
            self.debug_messages = getattr(self, "debug_messages", [])
            self.debug_messages.append(message)

        def market_order(self, symbol, quantity, tag=None):
            self.market_orders = getattr(self, "market_orders", [])
            self.market_orders.append({"symbol": symbol, "quantity": quantity, "tag": tag})
            return SimpleNamespace(order_id=len(self.market_orders), symbol=symbol, quantity=quantity, tag=tag)

    fake_algorithm_imports = SimpleNamespace(
        QCAlgorithm=FakeQCAlgorithm,
        Resolution=SimpleNamespace(DAILY="Daily"),
    )
    monkeypatch.setitem(sys.modules, "AlgorithmImports", fake_algorithm_imports)
    module_name = "lean_main_e2e_test_module"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, LEAN_MAIN)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module
