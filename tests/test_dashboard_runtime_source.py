from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from dashboard.config import DashboardConfig, load_dashboard_config
from dashboard.data import load_dashboard_snapshot
from dashboard.models import DashboardAuthority, DashboardFreshnessStatus, DashboardSectionStatus


ROOT = Path(__file__).resolve().parents[1]
NOW = datetime(2026, 6, 15, 10, 45, tzinfo=timezone.utc)


def _portfolio_payload() -> dict[str, object]:
    return {
        "fixture_label": "runtime-export-fixture",
        "source_timestamp": "2026-06-15T10:40:00+00:00",
        "portfolio": {
            "cash": "100000.00",
            "equity": "101250.50",
            "currency": "USD",
            "holdings": [
                {
                    "symbol": "MSFT",
                    "quantity": 10,
                    "average_price": "400.00",
                    "market_price": "412.50",
                }
            ],
        },
    }


def _sync_record(source_timestamp: datetime) -> dict[str, object]:
    return {
        "generation": 7,
        "source_timestamp": source_timestamp.isoformat(),
        "captured_at": "2026-06-15T10:40:01+00:00",
        "sync_status": "success",
        "reconciliation_clean": True,
        "portfolio": {
            "cash": "100000.00",
            "equity": "101250.50",
            "currency": "USD",
            "holdings": [
                {
                    "symbol": "msft",
                    "quantity": 10,
                    "average_price": "400.00",
                    "market_price": "412.50",
                }
            ],
        },
    }


def test_default_runtime_source_is_shared_state_and_degrades_before_worker_writes():
    config = load_dashboard_config(ROOT / "config" / "dashboard.yaml", env={})

    snapshot = load_dashboard_snapshot(config, now=NOW)

    assert config.data_source_kind == "shared_state"
    assert config.data_source_path is None
    assert snapshot.portfolio.status is DashboardSectionStatus.NOT_AVAILABLE
    assert snapshot.source_metadata.reasons == ("shared_state_no_data",)


def test_configured_local_json_source_loads_typed_dashboard_snapshot(tmp_path):
    source = tmp_path / "dashboard-export.json"
    source.write_text(json.dumps(_portfolio_payload()), encoding="utf-8")
    config = DashboardConfig(data_source_kind="local_json", data_source_path=str(source))

    snapshot = load_dashboard_snapshot(config, now=NOW)

    assert snapshot.source_metadata.source == "quantconnect"
    assert snapshot.source_metadata.authority is DashboardAuthority.AUTHORITATIVE
    assert snapshot.source_metadata.fixture_label == "runtime-export-fixture"
    assert snapshot.source_metadata.cache_timestamp == NOW
    assert snapshot.portfolio.status is DashboardSectionStatus.AVAILABLE
    assert snapshot.portfolio.holdings[0].symbol == "MSFT"


def test_missing_configured_source_degrades_without_crashing(tmp_path):
    config = DashboardConfig(data_source_kind="local_json", data_source_path=str(tmp_path / "missing.json"))

    snapshot = load_dashboard_snapshot(config, now=NOW)

    assert snapshot.portfolio.status is DashboardSectionStatus.NOT_AVAILABLE
    assert snapshot.source_metadata.source == "dashboard_runtime_source"
    assert snapshot.source_metadata.reasons == ("missing_dashboard_data_source",)
    assert snapshot.portfolio.errors[0].code == "dashboard_source_missing"


def test_malformed_source_degrades_with_redacted_safe_error(tmp_path):
    source = tmp_path / "bad-value.json"
    source.write_text("{bad json", encoding="utf-8")
    config = DashboardConfig(data_source_kind="local_json", data_source_path=str(source))

    snapshot = load_dashboard_snapshot(config, now=NOW)
    safe_error = snapshot.portfolio.errors[0].to_safe_dict()

    assert snapshot.portfolio.status is DashboardSectionStatus.ERROR
    assert snapshot.source_metadata.reasons == ("dashboard_source_error",)
    assert safe_error["code"] == "dashboard_source_error"
    assert "token" not in safe_error["message"].lower()


def test_sync_jsonl_source_kind_is_accepted_by_config(tmp_path):
    source = tmp_path / "portfolio_sync.jsonl"
    config = DashboardConfig(data_source_kind="sync_jsonl", data_source_path=str(source))

    assert config.data_source_kind == "sync_jsonl"
    assert config.data_source_path == str(source)


@pytest.mark.parametrize("contents", [None, ""])
def test_sync_jsonl_missing_or_empty_source_degrades_without_fabricating(tmp_path, contents):
    source = tmp_path / "portfolio_sync.jsonl"
    if contents is not None:
        source.write_text(contents, encoding="utf-8")
    config = DashboardConfig(data_source_kind="sync_jsonl", data_source_path=str(source))

    snapshot = load_dashboard_snapshot(config, now=NOW)

    assert snapshot.source_metadata.source == "quantconnect_sync_jsonl"
    assert snapshot.source_metadata.freshness_status is DashboardFreshnessStatus.UNKNOWN
    assert snapshot.portfolio.status is DashboardSectionStatus.NOT_AVAILABLE
    assert snapshot.portfolio.holdings == ()
    assert snapshot.portfolio.cash is None
    assert snapshot.portfolio.errors[0].code == "sync_no_data"


def test_sync_jsonl_malformed_last_line_degrades_without_crashing(tmp_path):
    source = tmp_path / "portfolio_sync.jsonl"
    source.write_text(json.dumps(_sync_record(NOW)) + "\n{bad json", encoding="utf-8")
    config = DashboardConfig(data_source_kind="sync_jsonl", data_source_path=str(source))

    snapshot = load_dashboard_snapshot(config, now=NOW)

    assert snapshot.source_metadata.source == "quantconnect_sync_jsonl"
    assert snapshot.portfolio.status is DashboardSectionStatus.ERROR
    assert snapshot.portfolio.errors[0].code == "sync_parse_error"


def test_sync_jsonl_unparseable_source_timestamp_is_unknown_not_fabricated(tmp_path):
    source = tmp_path / "portfolio_sync.jsonl"
    record = _sync_record(NOW)
    record["source_timestamp"] = "not-a-timestamp"
    source.write_text(json.dumps(record) + "\n", encoding="utf-8")
    config = DashboardConfig(data_source_kind="sync_jsonl", data_source_path=str(source))

    snapshot = load_dashboard_snapshot(config, now=NOW)

    assert snapshot.source_metadata.source_timestamp is None
    assert snapshot.source_metadata.freshness_status is DashboardFreshnessStatus.UNKNOWN
    assert snapshot.portfolio.status is DashboardSectionStatus.AVAILABLE
    assert "unknown_source_timestamp" in snapshot.source_metadata.reasons


def test_sync_jsonl_reads_last_line_and_loads_authoritative_portfolio(tmp_path):
    source = tmp_path / "portfolio_sync.jsonl"
    stale_record = _sync_record(datetime(2026, 6, 15, 10, 0, tzinfo=timezone.utc))
    fresh_record = _sync_record(datetime(2026, 6, 15, 10, 40, tzinfo=timezone.utc))
    fresh_record["portfolio"] = {
        **fresh_record["portfolio"],
        "holdings": [
            {
                "symbol": "aapl",
                "quantity": 5,
                "average_price": "175.00",
                "market_price": "180.00",
            }
        ],
    }
    source.write_text(
        json.dumps(stale_record) + "\n" + json.dumps(fresh_record) + "\n",
        encoding="utf-8",
    )
    config = DashboardConfig(data_source_kind="sync_jsonl", data_source_path=str(source))

    snapshot = load_dashboard_snapshot(config, now=NOW)

    assert snapshot.source_metadata.source == "quantconnect_sync_jsonl"
    assert snapshot.source_metadata.authority is DashboardAuthority.AUTHORITATIVE
    assert snapshot.source_metadata.cache_timestamp == NOW
    assert snapshot.source_metadata.freshness_status is DashboardFreshnessStatus.FRESH
    assert snapshot.portfolio.status is DashboardSectionStatus.AVAILABLE
    assert snapshot.portfolio.holdings[0].symbol == "AAPL"


def test_shared_state_source_loads_latest_dashboard_payload(monkeypatch):
    class FakeSharedSnapshot:
        def __init__(self, payload):
            self.payload = payload

    def fake_loader():
        return FakeSharedSnapshot(_portfolio_payload())

    monkeypatch.setattr("marketpilot.shared_state.load_dashboard_payload_from_env", fake_loader)
    config = DashboardConfig(data_source_kind="shared_state")

    snapshot = load_dashboard_snapshot(config, now=NOW)

    assert snapshot.source_metadata.source == "quantconnect"
    assert snapshot.source_metadata.authority is DashboardAuthority.AUTHORITATIVE
    assert snapshot.source_metadata.fixture_label == "runtime-export-fixture"
    assert snapshot.portfolio.status is DashboardSectionStatus.AVAILABLE


@pytest.mark.parametrize(
    "age_seconds,freshness,portfolio_status",
    [
        (600, DashboardFreshnessStatus.FRESH, DashboardSectionStatus.AVAILABLE),
        (601, DashboardFreshnessStatus.STALE, DashboardSectionStatus.STALE),
        (1800, DashboardFreshnessStatus.STALE, DashboardSectionStatus.STALE),
        (1801, DashboardFreshnessStatus.ERROR, DashboardSectionStatus.ERROR),
    ],
)
def test_sync_jsonl_freshness_thresholds(tmp_path, age_seconds, freshness, portfolio_status):
    source = tmp_path / "portfolio_sync.jsonl"
    source.write_text(
        json.dumps(_sync_record(NOW.replace(tzinfo=timezone.utc) - timedelta(seconds=age_seconds))) + "\n",
        encoding="utf-8",
    )
    config = DashboardConfig(data_source_kind="sync_jsonl", data_source_path=str(source))

    snapshot = load_dashboard_snapshot(config, now=NOW)

    assert snapshot.source_metadata.freshness_status is freshness
    assert snapshot.portfolio.status is portfolio_status


def test_app_uses_runtime_loader_instead_of_hard_coded_not_configured():
    app_source = (ROOT / "dashboard" / "app.py").read_text(encoding="utf-8")

    assert "load_dashboard_snapshot(config" in app_source
    assert 'DashboardDataClient.not_configured(missing=("dashboard_data_source",))' not in app_source


@pytest.mark.parametrize(
    "source_kind,source_path",
    [
        ("http", "https://example.com/dashboard.json"),
        ("local_json", "https://example.com/dashboard.json"),
        ("local_json", "../secret.json"),
        ("local_json", "token=secret-value"),
        ("sync_jsonl", "https://example.com/portfolio_sync.jsonl"),
        ("sync_jsonl", "../portfolio_sync.jsonl"),
        ("sync_jsonl", "token=secret-value"),
        ("object_store_write", "dashboard/portfolio.json"),
    ],
)
def test_runtime_source_config_rejects_unsafe_sources(source_kind, source_path):
    with pytest.raises(ValueError):
        DashboardConfig(data_source_kind=source_kind, data_source_path=source_path)
