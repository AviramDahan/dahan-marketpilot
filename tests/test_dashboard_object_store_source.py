"""Tests for dashboard Object Store/API-style export producer and read-only source loader."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from dashboard.config import DashboardConfig
from dashboard.data import (
    OBJECT_STORE_EXPORT_KEYS,
    DashboardDataClient,
    EndpointAccessError,
    assert_read_only_endpoint,
    load_dashboard_snapshot,
)
from dashboard.models import (
    DashboardAuthority,
    DashboardFreshnessStatus,
    DashboardSectionStatus,
)
from marketpilot.dashboard_export import (
    APPROVED_OBJECT_STORE_PRODUCER_KEYS,
    DashboardExportPayload,
    FakeObjectStoreWriter,
    ObjectStoreSourceLoader,
    build_dashboard_export_payload,
)


ROOT = Path(__file__).resolve().parents[1]
NOW = datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc)


def _runtime_evidence() -> dict[str, object]:
    return {
        "runtime_status": "paper_intent_ready",
        "ranked_candidates": 3,
        "risk_decisions": 2,
        "order_intents": 1,
        "notification_events": 2,
        "paper_order_eligible": True,
    }


def _portfolio_snapshot() -> dict[str, object]:
    return {
        "cash": "100000.00",
        "equity": "101500.00",
        "currency": "USD",
        "holdings": [
            {
                "symbol": "AAPL",
                "quantity": 50,
                "average_price": "175.00",
                "market_price": "180.00",
            }
        ],
    }


# --- Export payload builder tests ---


class TestBuildDashboardExportPayload:
    def test_valid_payload_has_required_authority_fields(self):
        payload = build_dashboard_export_payload(
            portfolio=_portfolio_snapshot(),
            runtime_evidence=_runtime_evidence(),
            source_timestamp=NOW,
        )

        assert payload.source == "quantconnect"
        assert payload.authority == "authoritative"
        assert payload.paper_trading_only is True
        assert payload.read_only_dashboard is True
        assert payload.source_timestamp == NOW

    def test_payload_serializes_to_approved_json_shape(self):
        payload = build_dashboard_export_payload(
            portfolio=_portfolio_snapshot(),
            runtime_evidence=_runtime_evidence(),
            source_timestamp=NOW,
        )
        serialized = payload.to_json()
        loaded = json.loads(serialized)

        assert loaded["source"] == "quantconnect"
        assert loaded["authority"] == "authoritative"
        assert loaded["paper_trading_only"] is True
        assert loaded["read_only_dashboard"] is True
        assert loaded["portfolio"]["cash"] == "100000.00"
        assert loaded["portfolio"]["holdings"][0]["symbol"] == "AAPL"
        assert "fixture_label" in loaded

    def test_payload_fixture_label_is_explicit(self):
        payload = build_dashboard_export_payload(
            portfolio=_portfolio_snapshot(),
            runtime_evidence=_runtime_evidence(),
            source_timestamp=NOW,
            fixture_label="test-export-fixture",
        )

        assert payload.fixture_label == "test-export-fixture"

    def test_empty_portfolio_produces_safe_payload(self):
        payload = build_dashboard_export_payload(
            portfolio={},
            runtime_evidence={},
            source_timestamp=NOW,
        )

        assert payload.source == "quantconnect"
        assert payload.paper_trading_only is True


# --- Fake Object Store writer tests ---


class TestFakeObjectStoreWriter:
    def test_writer_accepts_only_approved_keys(self):
        writer = FakeObjectStoreWriter()
        writer.write("dashboard/portfolio.json", '{"test": true}')

        assert "dashboard/portfolio.json" in writer.store

    def test_writer_rejects_unapproved_keys(self):
        writer = FakeObjectStoreWriter()

        with pytest.raises(ValueError, match="not an approved"):
            writer.write("secrets/api_key.json", '{"token": "bad"}')

    def test_writer_rejects_mutation_keys(self):
        writer = FakeObjectStoreWriter()

        with pytest.raises(ValueError, match="not an approved"):
            writer.write("live/orders/create", '{"order": "bad"}')

    def test_writer_stores_payload_string(self):
        writer = FakeObjectStoreWriter()
        content = json.dumps({"portfolio": {"cash": "1000"}})
        writer.write("dashboard/portfolio.json", content)

        assert writer.store["dashboard/portfolio.json"] == content

    def test_approved_producer_keys_match_dashboard_export_keys(self):
        assert APPROVED_OBJECT_STORE_PRODUCER_KEYS == OBJECT_STORE_EXPORT_KEYS


# --- Object Store source loader tests ---


class TestObjectStoreSourceLoader:
    def test_valid_payload_loads_into_dashboard_snapshot(self):
        payload = build_dashboard_export_payload(
            portfolio=_portfolio_snapshot(),
            runtime_evidence=_runtime_evidence(),
            source_timestamp=NOW,
            fixture_label="object-store-test",
        )
        writer = FakeObjectStoreWriter()
        writer.write("dashboard/portfolio.json", payload.to_json())
        loader = ObjectStoreSourceLoader(writer)

        snapshot = loader.load_snapshot(
            key="dashboard/portfolio.json",
            cache_timestamp=NOW,
        )

        assert snapshot.source_metadata.authority is DashboardAuthority.AUTHORITATIVE
        assert snapshot.source_metadata.source == "quantconnect"
        assert snapshot.portfolio.status is DashboardSectionStatus.AVAILABLE
        assert snapshot.portfolio.holdings[0].symbol == "AAPL"

    def test_missing_key_returns_not_available(self):
        writer = FakeObjectStoreWriter()
        loader = ObjectStoreSourceLoader(writer)

        snapshot = loader.load_snapshot(
            key="dashboard/portfolio.json",
            cache_timestamp=NOW,
        )

        assert snapshot.portfolio.status is DashboardSectionStatus.NOT_AVAILABLE
        assert "missing_object_store_export" in snapshot.source_metadata.reasons[0]

    def test_malformed_payload_returns_safe_degraded_state(self):
        writer = FakeObjectStoreWriter()
        writer.write("dashboard/portfolio.json", "{not valid json")
        loader = ObjectStoreSourceLoader(writer)

        snapshot = loader.load_snapshot(
            key="dashboard/portfolio.json",
            cache_timestamp=NOW,
        )

        assert snapshot.portfolio.status is DashboardSectionStatus.ERROR
        assert snapshot.portfolio.errors[0].code == "object_store_parse_error"

    def test_stale_payload_is_labeled_stale(self):
        old_time = datetime(2026, 6, 14, 0, 0, tzinfo=timezone.utc)
        payload = build_dashboard_export_payload(
            portfolio=_portfolio_snapshot(),
            runtime_evidence=_runtime_evidence(),
            source_timestamp=old_time,
            fixture_label="stale-fixture",
        )
        writer = FakeObjectStoreWriter()
        writer.write("dashboard/portfolio.json", payload.to_json())
        loader = ObjectStoreSourceLoader(writer, stale_threshold_seconds=3600)

        snapshot = loader.load_snapshot(
            key="dashboard/portfolio.json",
            cache_timestamp=NOW,
        )

        assert snapshot.source_metadata.freshness_status is DashboardFreshnessStatus.STALE

    def test_loader_rejects_secret_like_keys(self):
        writer = FakeObjectStoreWriter()
        loader = ObjectStoreSourceLoader(writer)

        with pytest.raises(ValueError, match="not an approved"):
            loader.load_snapshot(
                key="secrets/api_token.json",
                cache_timestamp=NOW,
            )

    def test_loader_rejects_mutation_endpoints(self):
        writer = FakeObjectStoreWriter()
        loader = ObjectStoreSourceLoader(writer)

        with pytest.raises(ValueError, match="not an approved"):
            loader.load_snapshot(
                key="/live/create",
                cache_timestamp=NOW,
            )


# --- Integration with dashboard config source kind ---


class TestObjectStoreConfigSourceKind:
    def test_object_store_source_kind_is_accepted_by_config(self):
        config = DashboardConfig(
            data_source_kind="object_store",
            data_source_path="dashboard/portfolio.json",
        )

        assert config.data_source_kind == "object_store"

    def test_object_store_source_returns_not_configured_without_writer(self):
        config = DashboardConfig(
            data_source_kind="object_store",
            data_source_path="dashboard/portfolio.json",
        )

        snapshot = load_dashboard_snapshot(config, now=NOW)

        assert snapshot.portfolio.status is DashboardSectionStatus.NOT_AVAILABLE
        assert "object_store_not_configured" in snapshot.source_metadata.reasons[0]

    def test_read_only_constraint_preserved_for_object_store_source(self):
        config = DashboardConfig(
            data_source_kind="object_store",
            data_source_path="dashboard/portfolio.json",
        )

        assert config.read_only is True
        assert config.manual_order_controls_enabled is False
        assert config.paper_trading_only is True
