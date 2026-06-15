from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal

from marketpilot.qc_api import QCNetworkError
from marketpilot.quantconnect_paper import (
    QuantConnectAlgorithmStatus,
    QuantConnectDeploymentStatus,
    QuantConnectHolding,
    QuantConnectPaperFill,
    QuantConnectPaperOrder,
    QuantConnectPaperPerformance,
    QuantConnectPaperSnapshot,
)
from marketpilot.reconciliation import ReconciliationDecision, ReconciliationMismatch, ReconciliationMismatchType
from marketpilot.sync import (
    SyncRecord,
    _exceeds_threshold,
    atomic_jsonl_append,
    read_last_sync_record,
    sync_portfolio,
)


class FakeClient:
    def __init__(self, snapshot: QuantConnectPaperSnapshot):
        self.snapshot = snapshot
        self.calls: list[dict[str, object]] = []

    def read_live_algorithm(self, *, project_id: int, deploy_id: str) -> QuantConnectPaperSnapshot:
        self.calls.append({"project_id": project_id, "deploy_id": deploy_id})
        return self.snapshot


class ErrorClient:
    def read_live_algorithm(self, *, project_id: int, deploy_id: str) -> QuantConnectPaperSnapshot:
        raise QCNetworkError("network unavailable")


def _snapshot(*, fill_references_order: bool = True) -> QuantConnectPaperSnapshot:
    order_id = "qc-order-1"
    fill_order_id = order_id if fill_references_order else "qc-missing-order"
    return QuantConnectPaperSnapshot(
        fixture_label="deterministic-test-fixture",
        captured_at=datetime(2026, 6, 16, 13, 0, tzinfo=timezone.utc),
        cash=Decimal("98500"),
        portfolio_equity=Decimal("101250"),
        holdings=(
            QuantConnectHolding(symbol="MSFT", quantity=10, average_price=Decimal("420"), market_price=Decimal("425")),
        ),
        orders=(
            QuantConnectPaperOrder(
                quantconnect_order_id=order_id,
                symbol="MSFT",
                status="filled",
                quantity=10,
                submitted_at=datetime(2026, 6, 16, 13, 1, tzinfo=timezone.utc),
                idempotency_key="intent-msft",
            ),
        ),
        fills=(
            QuantConnectPaperFill(
                quantconnect_order_id=fill_order_id,
                symbol="MSFT",
                quantity=10,
                fill_price=Decimal("421.50"),
                filled_at=datetime(2026, 6, 16, 13, 2, tzinfo=timezone.utc),
            ),
        ),
        deployment_status=QuantConnectDeploymentStatus.RUNNING,
        algorithm_status=QuantConnectAlgorithmStatus.RUNNING,
        performance=QuantConnectPaperPerformance(total_orders=1, total_fills=1, unrealized_profit=Decimal("35")),
    )


def test_sync_record_serializes_utc_timestamps():
    record = SyncRecord(
        generation=1,
        source_timestamp=datetime(2026, 6, 16, 13, 0, tzinfo=timezone.utc),
        captured_at=datetime(2026, 6, 16, 13, 1, tzinfo=timezone.utc),
        sync_status="success",
        reconciliation_clean=True,
        portfolio={"cash": "100"},
        orders_count=0,
        fills_count=0,
        deployment_status="running",
        algorithm_status="running",
    )

    data = record.to_json_dict()

    assert data["source_timestamp"].endswith("+00:00")
    assert data["captured_at"].endswith("+00:00")


def test_atomic_jsonl_append_replaces_file_and_reads_last_record(tmp_path):
    path = tmp_path / "portfolio_sync.jsonl"

    atomic_jsonl_append(path, {"generation": 1, "value": "first"})
    atomic_jsonl_append(path, {"generation": 2, "value": "second"})

    assert read_last_sync_record(path) == {"generation": 2, "value": "second"}
    lines = path.read_text(encoding="utf-8").splitlines()
    assert [json.loads(line)["generation"] for line in lines] == [1, 2]


def test_read_last_sync_record_returns_none_for_missing_or_empty_file(tmp_path):
    missing = tmp_path / "missing.jsonl"
    empty = tmp_path / "empty.jsonl"
    empty.write_text("", encoding="utf-8")

    assert read_last_sync_record(missing) is None
    assert read_last_sync_record(empty) is None


def test_threshold_flags_order_and_large_cash_mismatches():
    snapshot = _snapshot()
    order_decision = _decision(
        ReconciliationMismatch(
            mismatch_type=ReconciliationMismatchType.ORDER_STATE,
            reason="state differs",
            local_value="submitted",
            quantconnect_value="filled",
        )
    )
    small_cash_decision = _decision(
        ReconciliationMismatch(
            mismatch_type=ReconciliationMismatchType.CASH,
            reason="cash differs",
            local_value=Decimal("100000"),
            quantconnect_value=Decimal("99500"),
        )
    )
    large_cash_decision = _decision(
        ReconciliationMismatch(
            mismatch_type=ReconciliationMismatchType.CASH,
            reason="cash differs",
            local_value=Decimal("100000"),
            quantconnect_value=Decimal("98000"),
        )
    )

    assert _exceeds_threshold(order_decision, snapshot) is True
    assert _exceeds_threshold(small_cash_decision, snapshot) is False
    assert _exceeds_threshold(large_cash_decision, snapshot) is True


def test_sync_portfolio_polls_reconciles_persists_and_emits_discrepancy_alert(tmp_path):
    client = FakeClient(_snapshot(fill_references_order=False))
    path = tmp_path / "portfolio_sync.jsonl"

    result = sync_portfolio(project_id=123, deploy_id="L-paper", jsonl_path=path, client=client)  # type: ignore[arg-type]
    record = read_last_sync_record(path)

    assert result.status == "success"
    assert result.generation == 1
    assert result.alert_emitted is True
    assert client.calls == [{"project_id": 123, "deploy_id": "L-paper"}]
    assert record is not None
    assert record["generation"] == 1
    assert record["sync_status"] == "reconciliation_mismatch"
    assert record["reconciliation_clean"] is False
    assert record["portfolio"]["cash"] == "98500"
    assert record["source_timestamp"].endswith("+00:00")


def test_sync_portfolio_persists_api_error_record(tmp_path):
    path = tmp_path / "portfolio_sync.jsonl"

    result = sync_portfolio(project_id=123, deploy_id="L-paper", jsonl_path=path, client=ErrorClient())  # type: ignore[arg-type]
    record = read_last_sync_record(path)

    assert result.status == "api_error"
    assert result.generation == 1
    assert result.error == "network unavailable"
    assert record is not None
    assert record["sync_status"] == "api_error"
    assert record["portfolio"] == {}
    assert record["error_detail"] == "network unavailable"


def _decision(*mismatches: ReconciliationMismatch) -> ReconciliationDecision:
    return ReconciliationDecision(
        authoritative_source="quantconnect",
        block_new_entries=bool(mismatches),
        preserve_exits=True,
        requires_explicit_recovery=bool(mismatches),
        mismatches=tuple(mismatches),
        correlation_id="test-correlation",
    )
