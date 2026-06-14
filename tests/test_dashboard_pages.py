from datetime import datetime, timezone
from decimal import Decimal

from dashboard.data import DashboardDataClient
from dashboard.models import (
    DashboardAuthority,
    DashboardCollectionSection,
    DashboardFreshnessStatus,
    DashboardHolding,
    DashboardPortfolioSection,
    DashboardSectionError,
    DashboardSectionStatus,
    DashboardSnapshot,
    DashboardSourceMetadata,
)
from dashboard.pages import PAGE_REGISTRY, PageKind, render_page
from dashboard.pages.overview import build_overview


EXPECTED_PAGE_ORDER = (
    "Overview",
    "Positions",
    "Trades",
    "Signals",
    "Backtests",
    "Strategies",
    "Risk",
    "Notifications",
    "Activity",
    "System Status",
)


def _available_snapshot() -> DashboardSnapshot:
    metadata = DashboardSourceMetadata(
        source="quantconnect",
        source_timestamp=datetime(2026, 6, 14, 18, 0, tzinfo=timezone.utc),
        cache_timestamp=datetime(2026, 6, 14, 18, 1, tzinfo=timezone.utc),
        freshness_status=DashboardFreshnessStatus.FRESH,
        authority=DashboardAuthority.AUTHORITATIVE,
    )
    return DashboardSnapshot(
        source_metadata=metadata,
        portfolio=DashboardPortfolioSection(
            status=DashboardSectionStatus.AVAILABLE,
            cash=Decimal("100000"),
            equity=Decimal("101250.50"),
            holdings=(
                DashboardHolding(
                    symbol="MSFT",
                    quantity=10,
                    average_price=Decimal("400"),
                    market_price=Decimal("412.50"),
                ),
            ),
        ),
        positions=DashboardCollectionSection(
            status=DashboardSectionStatus.AVAILABLE,
            items=({"symbol": "MSFT", "state": "open", "quantity": 10},),
        ),
        signals=DashboardCollectionSection(
            status=DashboardSectionStatus.AVAILABLE,
            items=({"symbol": "AAPL", "classification": "watch"}, {"symbol": "NVDA"}),
        ),
        trades=DashboardCollectionSection(
            status=DashboardSectionStatus.AVAILABLE,
            items=(
                {"symbol": "MSFT", "record_type": "submitted", "quantity": 10},
                {"symbol": "MSFT", "record_type": "fill", "quantity": 10},
            ),
        ),
        backtests=DashboardCollectionSection(
            status=DashboardSectionStatus.NOT_AVAILABLE,
            reasons=("not_run",),
        ),
        strategies=DashboardCollectionSection(
            status=DashboardSectionStatus.AVAILABLE,
            items=({"name": "daily_only", "paper_mode": "limited_paper", "readiness": "ready"},),
        ),
        activity=DashboardCollectionSection(
            status=DashboardSectionStatus.AVAILABLE,
            items=({"event": "paper_snapshot_loaded"},),
        ),
        system=DashboardCollectionSection(
            status=DashboardSectionStatus.AVAILABLE,
            reasons=("all_clear",),
        ),
    )


def test_page_registry_order_and_read_only_metadata():
    assert tuple(page.title for page in PAGE_REGISTRY) == EXPECTED_PAGE_ORDER
    assert all(page.kind is PageKind.OBSERVATIONAL for page in PAGE_REGISTRY)
    assert all(page.allowed_actions == ("view", "refresh") for page in PAGE_REGISTRY)
    assert PAGE_REGISTRY[0].slug == "overview"


def test_overview_renders_operational_state_from_typed_snapshot():
    overview = build_overview(_available_snapshot())
    text = "\n".join(overview.lines)

    assert "SIMULATED PAPER TRADING ONLY - NOT FINANCIAL ADVICE" in text
    assert "QuantConnect source: quantconnect" in text
    assert "Paper mode: paper-only" in text
    assert "Portfolio status: available" in text
    assert "Freshness: fresh" in text
    assert "Open positions: 1" in text
    assert "Recent signals: 2" in text
    assert "Recent activity: 1" in text
    assert "System warnings: all_clear" in text


def test_overview_keeps_degraded_states_visible():
    snapshot = DashboardDataClient.not_configured(missing=("QUANTCONNECT_API_TOKEN",))
    overview = build_overview(snapshot)
    text = "\n".join(overview.lines)

    assert "not_configured" in text
    assert "QUANTCONNECT_API_TOKEN" in text
    assert "Portfolio status: not_configured" in text

    stale_snapshot = DashboardSnapshot(
        source_metadata=DashboardSourceMetadata(
            source="quantconnect",
            source_timestamp=None,
            cache_timestamp=None,
            freshness_status=DashboardFreshnessStatus.STALE,
            authority=DashboardAuthority.AUTHORITATIVE,
            reasons=("cache_older_than_threshold",),
        ),
        portfolio=DashboardPortfolioSection(status=DashboardSectionStatus.STALE, reasons=("stale",)),
        system=DashboardCollectionSection(
            status=DashboardSectionStatus.ERROR,
            errors=(DashboardSectionError(code="source_error", message="QuantConnect unavailable"),),
        ),
    )
    stale_text = "\n".join(build_overview(stale_snapshot).lines)
    assert "stale" in stale_text
    assert "error" in stale_text
    assert "QuantConnect unavailable" in stale_text


def test_later_phase_pages_render_safe_not_available_until_implemented():
    snapshot = _available_snapshot()

    for slug in (
        "risk",
        "notifications",
        "activity",
        "system-status",
    ):
        view = render_page(slug, snapshot)
        assert view.status is DashboardSectionStatus.NOT_AVAILABLE
        assert "not_available" in "\n".join(view.lines)


def test_registry_and_overview_do_not_define_mutation_actions():
    forbidden = {"trade", "send", "approve", "export", "ack"}
    action_names = {action for page in PAGE_REGISTRY for action in page.allowed_actions}

    assert action_names == {"view", "refresh"}
    assert forbidden.isdisjoint(action_names)


def test_positions_and_trades_pages_render_authoritative_rows():
    snapshot = _available_snapshot()

    positions = render_page("positions", snapshot)
    positions_text = "\n".join(positions.lines)
    assert positions.status is DashboardSectionStatus.AVAILABLE
    assert "Authority: authoritative" in positions_text
    assert "Freshness: fresh" in positions_text
    assert "MSFT" in positions_text
    assert "Quantity: 10" in positions_text

    trades = render_page("trades", snapshot)
    trades_text = "\n".join(trades.lines)
    assert trades.status is DashboardSectionStatus.AVAILABLE
    assert "QuantConnect authority" in trades_text
    assert "submitted" in trades_text
    assert "fill" in trades_text


def test_positions_and_trades_pages_show_degraded_states():
    snapshot = DashboardDataClient.not_configured(missing=("QUANTCONNECT_API_TOKEN",))

    assert "not_configured" in "\n".join(render_page("positions", snapshot).lines)
    assert "QUANTCONNECT_API_TOKEN" in "\n".join(render_page("trades", snapshot).lines)


def test_signals_backtests_and_strategies_pages_render_safe_status():
    snapshot = _available_snapshot()

    signals = "\n".join(render_page("signals", snapshot).lines)
    assert "AAPL" in signals
    assert "watch" in signals
    assert "Evidence is observational" in signals

    backtests = "\n".join(render_page("backtests", snapshot).lines)
    assert "not_run" in backtests
    assert "No performance claim is made" in backtests
    assert "guaranteed" not in backtests.lower()

    strategies = "\n".join(render_page("strategies", snapshot).lines)
    assert "daily_only" in strategies
    assert "limited_paper" in strategies
    assert "Status display only" in strategies


def test_signal_backtest_strategy_degraded_states_are_visible():
    snapshot = DashboardDataClient.missing_object_store_export("dashboard/signals.json")

    assert "not_available" in "\n".join(render_page("signals", snapshot).lines)
    assert "not_available" in "\n".join(render_page("backtests", snapshot).lines)
    assert "not_available" in "\n".join(render_page("strategies", snapshot).lines)
