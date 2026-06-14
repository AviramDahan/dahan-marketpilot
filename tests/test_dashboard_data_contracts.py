from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from dashboard.data import (
    APPROVED_QUANTCONNECT_READ_ENDPOINTS,
    OBJECT_STORE_EXPORT_KEYS,
    DashboardDataClient,
    EndpointAccessError,
    assert_read_only_endpoint,
)
from dashboard.models import (
    DashboardAuthority,
    DashboardFreshnessStatus,
    DashboardSectionStatus,
)


ROOT = Path(__file__).resolve().parents[1]


def _portfolio_fixture() -> dict[str, object]:
    return {
        "fixture_label": "deterministic-test-fixture",
        "source_timestamp": "2026-06-14T18:00:00+00:00",
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


def test_quantconnect_portfolio_fixture_parses_with_source_metadata():
    snapshot = DashboardDataClient.from_quantconnect_portfolio_fixture(
        _portfolio_fixture(),
        cache_timestamp=datetime(2026, 6, 14, 18, 1, tzinfo=timezone.utc),
    )

    assert snapshot.source_metadata.source == "quantconnect"
    assert snapshot.source_metadata.authority is DashboardAuthority.AUTHORITATIVE
    assert snapshot.source_metadata.fixture_label == "deterministic-test-fixture"
    assert snapshot.source_metadata.is_fixture is True
    assert snapshot.source_metadata.freshness_status is DashboardFreshnessStatus.FRESH
    assert snapshot.source_metadata.source_timestamp == datetime(2026, 6, 14, 18, 0, tzinfo=timezone.utc)
    assert snapshot.source_metadata.cache_timestamp == datetime(2026, 6, 14, 18, 1, tzinfo=timezone.utc)
    assert snapshot.portfolio.status is DashboardSectionStatus.AVAILABLE
    assert snapshot.portfolio.cash == Decimal("100000.00")
    assert snapshot.portfolio.equity == Decimal("101250.50")
    assert snapshot.portfolio.holdings[0].symbol == "MSFT"
    assert snapshot.source_metadata.to_safe_dict()["authority"] == "authoritative"


def test_fixture_payload_cannot_be_labeled_as_live_state():
    with pytest.raises(ValueError, match="fixture payloads must keep an explicit fixture label"):
        DashboardDataClient.from_quantconnect_portfolio_fixture(
            {**_portfolio_fixture(), "fixture_label": ""},
            cache_timestamp=datetime(2026, 6, 14, 18, 1, tzinfo=timezone.utc),
        )


def test_missing_quantconnect_prerequisites_and_exports_are_degraded_states():
    snapshot = DashboardDataClient.not_configured(
        missing=("QUANTCONNECT_USER_ID", "QUANTCONNECT_API_TOKEN")
    )

    assert snapshot.portfolio.status is DashboardSectionStatus.NOT_CONFIGURED
    assert snapshot.positions.status is DashboardSectionStatus.NOT_CONFIGURED
    assert snapshot.backtests.status is DashboardSectionStatus.NOT_CONFIGURED
    assert snapshot.portfolio.holdings == ()
    assert snapshot.backtests.items == ()
    assert "QUANTCONNECT_API_TOKEN" in snapshot.portfolio.reasons

    missing_export = DashboardDataClient.missing_object_store_export("dashboard/portfolio.json")
    assert missing_export.portfolio.status is DashboardSectionStatus.NOT_AVAILABLE
    assert missing_export.portfolio.holdings == ()
    assert missing_export.portfolio.reasons == ("missing_object_store_export:dashboard/portfolio.json",)


def test_quantconnect_read_endpoint_allowlist_rejects_mutation_paths():
    assert "/live/portfolio/read" in APPROVED_QUANTCONNECT_READ_ENDPOINTS
    assert "/object/get" in APPROVED_QUANTCONNECT_READ_ENDPOINTS
    assert "dashboard/portfolio.json" in OBJECT_STORE_EXPORT_KEYS
    assert_read_only_endpoint("/live/orders/read")

    forbidden_paths = [
        "/live/create",
        "/live/update",
        "/live/stop",
        "/orders/create",
        "/object/set",
        "/object/delete",
        "/projects/update",
        "/backtests/create",
    ]
    for path in forbidden_paths:
        with pytest.raises(EndpointAccessError):
            assert_read_only_endpoint(path)


def test_dashboard_docs_keep_data_source_contract_visible():
    text = (ROOT / "docs" / "dashboard.md").read_text(encoding="utf-8")

    assert "QuantConnect is the dashboard authority" in text
    assert "/live/portfolio/read" in text
    assert "/object/get" in text
    assert "dashboard/portfolio.json" in text
    assert "not_configured" in text
    assert "not_available" in text
    assert "fixtures are test-only" in text
