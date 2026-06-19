from datetime import datetime, timezone
from decimal import Decimal

from dashboard.data import DashboardDataClient
from dashboard.models import DashboardSectionStatus
from dashboard.pages.positions import build_positions
from dashboard.pages.signals import build_signals
from dashboard.pages.trades import build_trades
from marketpilot.dashboard_export import build_simulation_dashboard_payload


NOW = datetime(2026, 6, 19, 14, 30, tzinfo=timezone.utc)


def test_simulation_dashboard_payload_loads_read_only_sections():
    payload = build_simulation_dashboard_payload(
        portfolio={"cash": "10000", "equity": "10125", "currency": "USD"},
        candidates=({"symbol": "MSFT", "classification": "buy_candidate"},),
        open_trades=({"symbol": "MSFT", "state": "open", "quantity": 10},),
        closed_trades=({"record_type": "simulated_trade", "symbol": "AAPL", "quantity": 5},),
        system=({"name": "scheduler", "state": "ok"},),
        source_timestamp=NOW,
    )

    snapshot = DashboardDataClient.from_simulation_payload(payload, cache_timestamp=NOW)

    assert snapshot.source_metadata.source == "internal_simulation"
    assert snapshot.portfolio.cash == Decimal("10000")
    assert snapshot.signals.status is DashboardSectionStatus.AVAILABLE
    assert snapshot.positions.items[0]["symbol"] == "MSFT"
    assert snapshot.trades.items[0]["record_type"] == "simulated_trade"


def test_simulation_dashboard_views_label_internal_simulation():
    payload = build_simulation_dashboard_payload(
        portfolio={"cash": "10000", "equity": "10000", "currency": "USD"},
        candidates=({"symbol": "MSFT", "classification": "buy_candidate"},),
        system=({"name": "scheduler", "state": "ok"},),
        source_timestamp=NOW,
    )
    snapshot = DashboardDataClient.from_simulation_payload(payload, cache_timestamp=NOW)

    assert build_signals(snapshot).lines[0] == "Product mode: simulation_only."
    assert "Internal simulation records only" in build_trades(snapshot).lines[0]
    assert build_positions(snapshot).lines[0] == "Authority: simulation_only"
