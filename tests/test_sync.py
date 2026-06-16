from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest

from marketpilot.qc_api import QCApiClient, QCApiError
from marketpilot.quantconnect_paper import (
    QuantConnectAlgorithmStatus,
    QuantConnectDeploymentStatus,
    QuantConnectHolding,
    QuantConnectPaperPerformance,
    QuantConnectPaperSnapshot,
)
from marketpilot.reconciliation import ReconciliationDecision, ReconciliationMismatch, ReconciliationMismatchType
from marketpilot.sync import (
    SyncRecord,
    _exceeds_threshold,
    _next_generation,
    atomic_jsonl_append,
    read_last_sync_record,
    sync_portfolio,
)


def _test_snapshot() -> QuantConnectPaperSnapshot:
    return QuantConnectPaperSnapshot(
        fixture_label="deterministic-test-fixture",
        captured_at=datetime(2026, 6, 16, 14, 30, tzinfo=timezone.utc),
        cash=Decimal("100000"),
        portfolio_equity=Decimal("105000"),
        holdings=(
            QuantConnectHolding(
                symbol="AAPL",
                quantity=50,
                average_price=Decimal("175"),
                market_price=Decimal("182"),
            ),
        ),
        orders=(),
        fills=(),
        deployment_status=QuantConnectDeploymentStatus.RUNNING,
        algorithm_status=QuantConnectAlgorithmStatus.RUNNING,
        performance=QuantConnectPaperPerformance(
            total_orders=0,
            total_fills=0,
            unrealized_profit=Decimal("350"),
        ),
    )


def _clean_decision(correlation_id: str) -> ReconciliationDecision:
    return ReconciliationDecision(
        authoritative_source="quantconnect",
        block_new_entries=False,
        preserve_exits=True,
        requires_explicit_recovery=False,
        mismatches=(),
        correlation_id=correlation_id,
    )


def _mismatch_decision(
    correlation_id: str,
    mismatch_type: ReconciliationMismatchType,
    *,
    local_value: object | None = None,
    quantconnect_value: object | None = None,
) -> ReconciliationDecision:
    mismatch = ReconciliationMismatch(
        mismatch_type=mismatch_type,
        reason=f"{mismatch_type.value}_differs_from_quantconnect",
        local_value=local_value,
        quantconnect_value=quantconnect_value,
    )
    return ReconciliationDecision(
        authoritative_source="quantconnect",
        block_new_entries=True,
        preserve_exits=True,
        requires_explicit_recovery=True,
        mismatches=(mismatch,),
        correlation_id=correlation_id,
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


def test_atomic_jsonl_append_creates_file(tmp_path):
    path = tmp_path / "portfolio_sync.jsonl"

    atomic_jsonl_append(path, {"generation": 1, "value": "first"})

    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0]) == {"generation": 1, "value": "first"}


def test_atomic_jsonl_append_appends_lines(tmp_path):
    path = tmp_path / "portfolio_sync.jsonl"

    for generation in range(1, 4):
        atomic_jsonl_append(path, {"generation": generation})

    lines = path.read_text(encoding="utf-8").splitlines()
    assert [json.loads(line)["generation"] for line in lines] == [1, 2, 3]


def test_atomic_jsonl_append_no_partial_on_existing(tmp_path):
    path = tmp_path / "portfolio_sync.jsonl"
    path.write_text('{"generation": 1, "value": "existing"}\n', encoding="utf-8")

    atomic_jsonl_append(path, {"generation": 2, "value": "new"})

    lines = path.read_text(encoding="utf-8").splitlines()
    assert [json.loads(line)["generation"] for line in lines] == [1, 2]
    assert json.loads(lines[0])["value"] == "existing"
    assert json.loads(lines[1])["value"] == "new"


def test_read_last_sync_record_missing_file(tmp_path):
    assert read_last_sync_record(tmp_path / "missing.jsonl") is None


def test_read_last_sync_record_empty_file(tmp_path):
    path = tmp_path / "portfolio_sync.jsonl"
    path.write_text("", encoding="utf-8")

    assert read_last_sync_record(path) is None


def test_read_last_sync_record_returns_last_line(tmp_path):
    path = tmp_path / "portfolio_sync.jsonl"
    for generation in range(1, 4):
        atomic_jsonl_append(path, {"generation": generation})

    assert read_last_sync_record(path) == {"generation": 3}


def test_next_generation_starts_at_one(tmp_path):
    assert _next_generation(tmp_path / "portfolio_sync.jsonl") == 1


def test_next_generation_increments(tmp_path):
    path = tmp_path / "portfolio_sync.jsonl"
    atomic_jsonl_append(path, {"generation": 5})

    assert _next_generation(path) == 6


def test_sync_portfolio_rejects_paper_trading_false(tmp_path):
    client = Mock(spec=QCApiClient)

    with patch("marketpilot.sync.PAPER_TRADING_ONLY", False):
        with pytest.raises(RuntimeError, match="PAPER_TRADING_ONLY must be True"):
            sync_portfolio(project_id=123, deploy_id="L-paper", jsonl_path=tmp_path / "portfolio_sync.jsonl", client=client)

    client.read_live_algorithm.assert_not_called()


def test_sync_portfolio_success_happy_path(tmp_path):
    path = tmp_path / "portfolio_sync.jsonl"
    snapshot = _test_snapshot()
    client = Mock(spec=QCApiClient)
    client.read_live_algorithm.return_value = snapshot

    with patch("marketpilot.sync.reconcile_quantconnect_state", return_value=_clean_decision("sync-gen-1")) as reconcile:
        result = sync_portfolio(project_id=123, deploy_id="L-paper", jsonl_path=path, client=client)

    record = read_last_sync_record(path)
    assert result.status == "success"
    assert result.generation == 1
    assert result.alert_emitted is False
    client.read_live_algorithm.assert_called_once_with(project_id=123, deploy_id="L-paper")
    reconcile.assert_called_once()
    assert record is not None
    assert record["sync_status"] == "success"
    assert record["reconciliation_clean"] is True
    assert record["generation"] == 1
    assert record["portfolio"]["cash"] == "100000"
    assert record["portfolio"]["holdings"][0]["symbol"] == "AAPL"


def test_sync_portfolio_api_error_persists_error_record(tmp_path):
    path = tmp_path / "portfolio_sync.jsonl"
    client = Mock(spec=QCApiClient)
    client.read_live_algorithm.side_effect = QCApiError("network unavailable")

    result = sync_portfolio(project_id=123, deploy_id="L-paper", jsonl_path=path, client=client)

    record = read_last_sync_record(path)
    assert result.status == "api_error"
    assert result.generation == 1
    assert result.error == "network unavailable"
    assert record is not None
    assert record["sync_status"] == "api_error"
    assert record["portfolio"] == {}
    assert record["error_detail"] == "network unavailable"


def test_sync_portfolio_emits_alert_on_order_mismatch(tmp_path):
    path = tmp_path / "portfolio_sync.jsonl"
    snapshot = _test_snapshot()
    client = Mock(spec=QCApiClient)
    client.read_live_algorithm.return_value = snapshot
    decision = _mismatch_decision("sync-gen-1", ReconciliationMismatchType.ORDER_ID)

    with patch("marketpilot.sync.reconcile_quantconnect_state", return_value=decision):
        with patch("marketpilot.sync.event_for_system_incident", return_value=Mock()) as event_factory:
            result = sync_portfolio(project_id=123, deploy_id="L-paper", jsonl_path=path, client=client)

    assert result.alert_emitted is True
    event_factory.assert_called_once()
    record = read_last_sync_record(path)
    assert record is not None
    assert record["sync_status"] == "reconciliation_mismatch"


def test_sync_portfolio_no_alert_on_small_cash_mismatch(tmp_path):
    path = tmp_path / "portfolio_sync.jsonl"
    snapshot = _test_snapshot()
    client = Mock(spec=QCApiClient)
    client.read_live_algorithm.return_value = snapshot
    decision = _mismatch_decision(
        "sync-gen-1",
        ReconciliationMismatchType.CASH,
        local_value=Decimal("100000"),
        quantconnect_value=Decimal("99500"),
    )

    with patch("marketpilot.sync.reconcile_quantconnect_state", return_value=decision):
        with patch("marketpilot.sync.event_for_system_incident", return_value=Mock()) as event_factory:
            result = sync_portfolio(project_id=123, deploy_id="L-paper", jsonl_path=path, client=client)

    assert result.alert_emitted is False
    event_factory.assert_not_called()


def test_sync_portfolio_alerts_on_large_cash_mismatch(tmp_path):
    path = tmp_path / "portfolio_sync.jsonl"
    snapshot = _test_snapshot()
    client = Mock(spec=QCApiClient)
    client.read_live_algorithm.return_value = snapshot
    decision = _mismatch_decision(
        "sync-gen-1",
        ReconciliationMismatchType.CASH,
        local_value=Decimal("100000"),
        quantconnect_value=Decimal("98000"),
    )

    with patch("marketpilot.sync.reconcile_quantconnect_state", return_value=decision):
        with patch("marketpilot.sync.event_for_system_incident", return_value=Mock()) as event_factory:
            result = sync_portfolio(project_id=123, deploy_id="L-paper", jsonl_path=path, client=client)

    assert result.alert_emitted is True
    event_factory.assert_called_once()


def test_sync_portfolio_never_auto_corrects(tmp_path):
    path = tmp_path / "portfolio_sync.jsonl"
    snapshot = _test_snapshot()
    client = Mock(spec=QCApiClient)
    client.read_live_algorithm.return_value = snapshot
    decision = _mismatch_decision("sync-gen-1", ReconciliationMismatchType.ORDER_STATE)

    with patch("marketpilot.sync.reconcile_quantconnect_state", return_value=decision):
        result = sync_portfolio(project_id=123, deploy_id="L-paper", jsonl_path=path, client=client)

    assert result.status == "success"
    assert snapshot == _test_snapshot()
    client.read_live_algorithm.assert_called_once_with(project_id=123, deploy_id="L-paper")
    assert set(client.method_calls[0][2]) == {"project_id", "deploy_id"}


def test_sync_record_timestamps_are_utc(tmp_path):
    path = tmp_path / "portfolio_sync.jsonl"
    snapshot = _test_snapshot()
    client = Mock(spec=QCApiClient)
    client.read_live_algorithm.return_value = snapshot

    with patch("marketpilot.sync.reconcile_quantconnect_state", return_value=_clean_decision("sync-gen-1")):
        sync_portfolio(project_id=123, deploy_id="L-paper", jsonl_path=path, client=client)

    record = read_last_sync_record(path)
    assert record is not None
    assert record["source_timestamp"].endswith("+00:00")
    assert record["captured_at"].endswith("+00:00")


def test_threshold_flags_order_and_large_cash_mismatches():
    snapshot = _test_snapshot()
    order_decision = _mismatch_decision("corr", ReconciliationMismatchType.ORDER_STATE)
    small_cash_decision = _mismatch_decision(
        "corr",
        ReconciliationMismatchType.CASH,
        local_value=Decimal("100000"),
        quantconnect_value=Decimal("99500"),
    )
    large_cash_decision = _mismatch_decision(
        "corr",
        ReconciliationMismatchType.CASH,
        local_value=Decimal("100000"),
        quantconnect_value=Decimal("98000"),
    )

    assert _exceeds_threshold(order_decision, snapshot) is True
    assert _exceeds_threshold(small_cash_decision, snapshot) is False
    assert _exceeds_threshold(large_cash_decision, snapshot) is True
