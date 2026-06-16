from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dashboard.config import DashboardConfig
from dashboard.data import load_dashboard_snapshot
from dashboard.models import (
    DashboardAuthority,
    DashboardFreshnessStatus,
    DashboardSectionStatus,
    DashboardSnapshot,
)


NOW = datetime(2026, 6, 16, 15, 0, tzinfo=timezone.utc)


def _write_sync_record(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, sort_keys=True) + "\n", encoding="utf-8")


def _sample_record(source_timestamp: datetime, generation: int = 1) -> dict:
    return {
        "generation": generation,
        "source_timestamp": source_timestamp.astimezone(timezone.utc).isoformat(),
        "captured_at": NOW.isoformat(),
        "sync_status": "success",
        "reconciliation_clean": True,
        "portfolio": {
            "cash": "100000",
            "equity": "105000",
            "currency": "USD",
            "holdings": [
                {
                    "symbol": "AAPL",
                    "quantity": 50,
                    "average_price": "175",
                    "market_price": "182",
                }
            ],
            "unrealized_profit": "350",
        },
        "orders_count": 0,
        "fills_count": 0,
        "deployment_status": "running",
        "algorithm_status": "running",
        "error_detail": None,
    }


def _sync_config(path: Path) -> DashboardConfig:
    return DashboardConfig(data_source_kind="sync_jsonl", data_source_path=str(path))


def test_sync_jsonl_dispatch(tmp_path):
    source = tmp_path / "portfolio_sync.jsonl"
    _write_sync_record(source, _sample_record(NOW - timedelta(minutes=5)))

    snapshot = load_dashboard_snapshot(_sync_config(source), now=NOW)

    assert isinstance(snapshot, DashboardSnapshot)
    assert snapshot.portfolio.status is DashboardSectionStatus.AVAILABLE
    assert snapshot.source_metadata.freshness_status is DashboardFreshnessStatus.FRESH


def test_sync_jsonl_missing_file(tmp_path):
    snapshot = load_dashboard_snapshot(_sync_config(tmp_path / "missing.jsonl"), now=NOW)

    assert snapshot.portfolio.status is DashboardSectionStatus.NOT_AVAILABLE
    assert snapshot.source_metadata.freshness_status is DashboardFreshnessStatus.UNKNOWN
    assert "no_sync_data" in snapshot.portfolio.reasons
    assert "no_sync_data" in snapshot.source_metadata.reasons


def test_sync_jsonl_empty_file(tmp_path):
    source = tmp_path / "portfolio_sync.jsonl"
    source.write_text("", encoding="utf-8")

    snapshot = load_dashboard_snapshot(_sync_config(source), now=NOW)

    assert snapshot.portfolio.status is DashboardSectionStatus.NOT_AVAILABLE
    assert snapshot.source_metadata.freshness_status is DashboardFreshnessStatus.UNKNOWN
    assert snapshot.portfolio.cash is None
    assert snapshot.portfolio.holdings == ()


def test_sync_jsonl_corrupt_json(tmp_path):
    source = tmp_path / "portfolio_sync.jsonl"
    source.write_text("{bad json", encoding="utf-8")

    snapshot = load_dashboard_snapshot(_sync_config(source), now=NOW)

    assert snapshot.portfolio.status is DashboardSectionStatus.ERROR
    assert snapshot.portfolio.errors[0].code == "sync_parse_error"
    assert snapshot.source_metadata.freshness_status is DashboardFreshnessStatus.UNKNOWN


def test_freshness_fresh(tmp_path):
    source = tmp_path / "portfolio_sync.jsonl"
    _write_sync_record(source, _sample_record(NOW - timedelta(minutes=5)))

    snapshot = load_dashboard_snapshot(_sync_config(source), now=NOW)

    assert snapshot.source_metadata.freshness_status is DashboardFreshnessStatus.FRESH
    assert snapshot.portfolio.status is DashboardSectionStatus.AVAILABLE


def test_freshness_stale(tmp_path):
    source = tmp_path / "portfolio_sync.jsonl"
    _write_sync_record(source, _sample_record(NOW - timedelta(minutes=15)))

    snapshot = load_dashboard_snapshot(_sync_config(source), now=NOW)

    assert snapshot.source_metadata.freshness_status is DashboardFreshnessStatus.STALE
    assert snapshot.portfolio.status is DashboardSectionStatus.STALE


def test_freshness_error(tmp_path):
    source = tmp_path / "portfolio_sync.jsonl"
    _write_sync_record(source, _sample_record(NOW - timedelta(minutes=45)))

    snapshot = load_dashboard_snapshot(_sync_config(source), now=NOW)

    assert snapshot.source_metadata.freshness_status is DashboardFreshnessStatus.ERROR
    assert snapshot.portfolio.status is DashboardSectionStatus.ERROR


def test_freshness_boundary_10min(tmp_path):
    source = tmp_path / "portfolio_sync.jsonl"
    _write_sync_record(source, _sample_record(NOW - timedelta(seconds=600)))

    snapshot = load_dashboard_snapshot(_sync_config(source), now=NOW)

    assert snapshot.source_metadata.freshness_status is DashboardFreshnessStatus.FRESH
    assert snapshot.portfolio.status is DashboardSectionStatus.AVAILABLE


def test_freshness_boundary_30min(tmp_path):
    source = tmp_path / "portfolio_sync.jsonl"
    _write_sync_record(source, _sample_record(NOW - timedelta(seconds=1800)))

    snapshot = load_dashboard_snapshot(_sync_config(source), now=NOW)

    assert snapshot.source_metadata.freshness_status is DashboardFreshnessStatus.STALE
    assert snapshot.portfolio.status is DashboardSectionStatus.STALE


def test_authority_is_authoritative(tmp_path):
    source = tmp_path / "portfolio_sync.jsonl"
    _write_sync_record(source, _sample_record(NOW - timedelta(minutes=5)))

    snapshot = load_dashboard_snapshot(_sync_config(source), now=NOW)

    assert snapshot.source_metadata.source == "quantconnect_sync_jsonl"
    assert snapshot.source_metadata.authority is DashboardAuthority.AUTHORITATIVE


def test_no_fabrication_on_missing_data(tmp_path):
    snapshot = load_dashboard_snapshot(_sync_config(tmp_path / "missing.jsonl"), now=NOW)

    assert snapshot.portfolio.cash is None
    assert snapshot.portfolio.equity is None
    assert snapshot.portfolio.holdings == ()
    assert snapshot.positions.items == ()
    assert snapshot.trades.items == ()


def test_source_timestamp_parsed_as_utc(tmp_path):
    source = tmp_path / "portfolio_sync.jsonl"
    timestamp = datetime(2026, 6, 16, 14, 55, tzinfo=timezone.utc)
    _write_sync_record(source, _sample_record(timestamp))

    snapshot = load_dashboard_snapshot(_sync_config(source), now=NOW)

    assert snapshot.source_metadata.source_timestamp == timestamp
    assert snapshot.source_metadata.source_timestamp is not None
    assert snapshot.source_metadata.source_timestamp.tzinfo is timezone.utc
