from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from dashboard.config import DashboardConfig, load_dashboard_config
from dashboard.data import load_dashboard_snapshot
from dashboard.models import DashboardAuthority, DashboardSectionStatus


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


def test_default_runtime_source_is_explicit_not_configured():
    config = load_dashboard_config(ROOT / "config" / "dashboard.yaml", env={})

    snapshot = load_dashboard_snapshot(config, now=NOW)

    assert config.data_source_kind == "none"
    assert config.data_source_path is None
    assert snapshot.portfolio.status is DashboardSectionStatus.NOT_CONFIGURED
    assert snapshot.source_metadata.reasons == ("dashboard_data_source",)


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
        ("object_store_write", "dashboard/portfolio.json"),
    ],
)
def test_runtime_source_config_rejects_unsafe_sources(source_kind, source_path):
    with pytest.raises(ValueError):
        DashboardConfig(data_source_kind=source_kind, data_source_path=source_path)
