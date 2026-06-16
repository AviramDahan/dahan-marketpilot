"""Pure Overview page helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo

from dashboard.models import DashboardFreshnessStatus, DashboardSectionStatus, DashboardSnapshot
from marketpilot.constants import DISCLAIMER


ET = ZoneInfo("America/New_York")


@dataclass(frozen=True)
class HoldingRow:
    symbol: str
    quantity: str
    avg_price: str
    market_price: str
    pnl_pct: str


@dataclass(frozen=True)
class SyncPortfolioView:
    freshness_label: str
    freshness_level: str
    cash: str | None
    equity: str | None
    unrealized_pnl: str | None
    holdings: tuple[HoldingRow, ...] | None
    sync_status_label: str
    authority_label: str


@dataclass(frozen=True)
class OverviewView:
    lines: tuple[str, ...]
    sync_portfolio: SyncPortfolioView | None = None


def build_overview(snapshot: DashboardSnapshot) -> OverviewView:
    metadata = snapshot.source_metadata
    warnings = _system_warnings(snapshot)
    sync_portfolio = _safe_sync_portfolio_view(snapshot)
    lines = (
        *_sync_portfolio_lines(sync_portfolio),
        DISCLAIMER,
        f"QuantConnect source: {metadata.source}",
        "Paper mode: paper-only",
        f"Portfolio status: {snapshot.portfolio.status.value}",
        f"Freshness: {metadata.freshness_status.value}",
        f"Open positions: {len(snapshot.positions.items)}",
        f"Recent signals: {len(snapshot.signals.items)}",
        f"Recent activity: {len(snapshot.activity.items)}",
        f"System warnings: {warnings}",
    )
    return OverviewView(lines=lines, sync_portfolio=sync_portfolio)


def build_sync_portfolio_view(snapshot: DashboardSnapshot) -> SyncPortfolioView:
    metadata = snapshot.source_metadata
    unavailable = (
        metadata.freshness_status is DashboardFreshnessStatus.UNKNOWN
        or snapshot.portfolio.status
        in {DashboardSectionStatus.NOT_AVAILABLE, DashboardSectionStatus.NOT_CONFIGURED}
    )
    if unavailable:
        return SyncPortfolioView(
            freshness_label="Portfolio sync data unavailable - run python -m marketpilot sync to start",
            freshness_level="unavailable",
            cash=None,
            equity=None,
            unrealized_pnl=None,
            holdings=None,
            sync_status_label=_sync_status_label(snapshot),
            authority_label=_authority_label(),
        )

    source_time = _format_et_time(metadata.source_timestamp)
    freshness_level = _freshness_level(metadata.freshness_status)
    freshness_label = render_freshness_banner(freshness_level, source_time)
    holdings = tuple(_holding_row(holding) for holding in snapshot.portfolio.holdings)

    return SyncPortfolioView(
        freshness_label=freshness_label,
        freshness_level=freshness_level,
        cash=_format_currency(snapshot.portfolio.cash),
        equity=_format_currency(snapshot.portfolio.equity),
        unrealized_pnl=_format_currency(_unrealized_pnl_from_holdings(snapshot)),
        holdings=holdings,
        sync_status_label=_sync_status_label(snapshot),
        authority_label=_authority_label(),
    )


def render_freshness_banner(freshness_level: str, et_time: str) -> str:
    if freshness_level == "fresh":
        return f"Portfolio data fresh - last update: {et_time}"
    if freshness_level == "stale":
        return f"Portfolio data stale (>10 min) - last update: {et_time}"
    if freshness_level == "error":
        return f"Portfolio data error (>30 min) - last update: {et_time}"
    return "Portfolio sync data unavailable - run python -m marketpilot sync to start"


def _system_warnings(snapshot: DashboardSnapshot) -> str:
    values: list[str] = []
    values.extend(snapshot.source_metadata.reasons)
    values.extend(snapshot.portfolio.reasons)
    values.extend(snapshot.system.reasons)
    values.extend(error.message for error in snapshot.system.errors)
    if snapshot.system.status.value not in {"available", "not_available"}:
        values.append(snapshot.system.status.value)
    if not values:
        return "none"
    return ", ".join(values)


def _safe_sync_portfolio_view(snapshot: DashboardSnapshot) -> SyncPortfolioView | None:
    try:
        return build_sync_portfolio_view(snapshot)
    except Exception:
        return None


def _sync_portfolio_lines(view: SyncPortfolioView | None) -> tuple[str, ...]:
    if view is None:
        return ("Portfolio sync view: unavailable",)

    metric_parts = (
        f"Cash: {view.cash or 'not available'}",
        f"Equity: {view.equity or 'not available'}",
        f"Unrealized P&L: {view.unrealized_pnl or 'not available'}",
    )
    if view.holdings is None:
        holdings_line = "Holdings: not available"
    elif not view.holdings:
        holdings_line = "Holdings: none reported by QuantConnect"
    else:
        symbols = ", ".join(row.symbol for row in view.holdings[:5])
        suffix = "" if len(view.holdings) <= 5 else f" +{len(view.holdings) - 5} more"
        holdings_line = f"Holdings: {len(view.holdings)} ({symbols}{suffix})"

    return (
        view.freshness_label,
        " | ".join(metric_parts),
        holdings_line,
        view.sync_status_label,
        view.authority_label,
    )


def _freshness_level(status: DashboardFreshnessStatus) -> str:
    if status is DashboardFreshnessStatus.FRESH:
        return "fresh"
    if status is DashboardFreshnessStatus.STALE:
        return "stale"
    if status is DashboardFreshnessStatus.ERROR:
        return "error"
    return "unavailable"


def _holding_row(holding: object) -> HoldingRow:
    avg_price = getattr(holding, "average_price")
    market_price = getattr(holding, "market_price")
    return HoldingRow(
        symbol=str(getattr(holding, "symbol")),
        quantity=str(getattr(holding, "quantity")),
        avg_price=_format_currency(avg_price) or "not available",
        market_price=_format_currency(market_price) or "not available",
        pnl_pct=_format_pnl_pct(avg_price, market_price),
    )


def _format_pnl_pct(avg_price: object, market_price: object) -> str:
    avg = _to_decimal(avg_price)
    market = _to_decimal(market_price)
    if avg is None or market is None or avg == 0:
        return "not available"
    pct = (market - avg) / avg * Decimal("100")
    return f"{pct:+.2f}%"


def _format_currency(value: object) -> str | None:
    parsed = _to_decimal(value)
    if parsed is None:
        return None
    return f"${parsed:,.2f}"


def _unrealized_pnl_from_holdings(snapshot: DashboardSnapshot) -> Decimal | None:
    if not snapshot.portfolio.holdings:
        return None
    total = Decimal("0")
    for holding in snapshot.portfolio.holdings:
        avg = _to_decimal(holding.average_price)
        market = _to_decimal(holding.market_price)
        quantity = _to_decimal(holding.quantity)
        if avg is None or market is None or quantity is None:
            return None
        total += (market - avg) * quantity
    return total


def _sync_status_label(snapshot: DashboardSnapshot) -> str:
    last_sync = _format_et_time(snapshot.source_metadata.source_timestamp)
    last_poll = _format_et_time(snapshot.source_metadata.cache_timestamp)
    error_count = _snapshot_error_count(snapshot)
    return f"Last sync: {last_sync} | Last poll: {last_poll} | Errors: {error_count}"


def _format_et_time(value: datetime | None) -> str:
    if value is None:
        return "not available"
    return _ensure_utc(value).astimezone(ET).strftime("%H:%M:%S ET")


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _snapshot_error_count(snapshot: DashboardSnapshot) -> int:
    return sum(len(section.errors) for section in snapshot.sections())


def _authority_label() -> str:
    return "Source: QuantConnect (authoritative)"


def _to_decimal(value: object) -> Decimal | None:
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
