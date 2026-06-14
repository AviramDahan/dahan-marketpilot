"""Read-only dashboard page registry."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from dashboard.models import DashboardSectionStatus, DashboardSnapshot


class PageKind(str, Enum):
    OBSERVATIONAL = "observational"


@dataclass(frozen=True)
class PageMetadata:
    slug: str
    title: str
    kind: PageKind = PageKind.OBSERVATIONAL
    allowed_actions: tuple[str, ...] = ("view", "refresh")


@dataclass(frozen=True)
class PageView:
    title: str
    status: DashboardSectionStatus
    lines: tuple[str, ...]


PAGE_REGISTRY: tuple[PageMetadata, ...] = (
    PageMetadata(slug="overview", title="Overview"),
    PageMetadata(slug="positions", title="Positions"),
    PageMetadata(slug="trades", title="Trades"),
    PageMetadata(slug="signals", title="Signals"),
    PageMetadata(slug="backtests", title="Backtests"),
    PageMetadata(slug="strategies", title="Strategies"),
    PageMetadata(slug="risk", title="Risk"),
    PageMetadata(slug="notifications", title="Notifications"),
    PageMetadata(slug="activity", title="Activity"),
    PageMetadata(slug="system-status", title="System Status"),
)


def render_page(slug: str, snapshot: DashboardSnapshot) -> PageView:
    normalized = slug.strip().lower()
    if normalized == "overview":
        from dashboard.pages.overview import build_overview

        overview = build_overview(snapshot)
        return PageView(
            title="Overview",
            status=DashboardSectionStatus.AVAILABLE,
            lines=overview.lines,
        )
    if normalized == "positions":
        from dashboard.pages.positions import build_positions

        view = build_positions(snapshot)
        return PageView(title="Positions", status=view.status, lines=view.lines)
    if normalized == "trades":
        from dashboard.pages.trades import build_trades

        view = build_trades(snapshot)
        return PageView(title="Trades", status=view.status, lines=view.lines)
    if normalized == "signals":
        from dashboard.pages.signals import build_signals

        view = build_signals(snapshot)
        return PageView(title="Signals", status=view.status, lines=view.lines)
    if normalized == "backtests":
        from dashboard.pages.backtests import build_backtests

        view = build_backtests(snapshot)
        return PageView(title="Backtests", status=view.status, lines=view.lines)
    if normalized == "strategies":
        from dashboard.pages.strategies import build_strategies

        view = build_strategies(snapshot)
        return PageView(title="Strategies", status=view.status, lines=view.lines)
    if normalized == "risk":
        from dashboard.pages.risk import build_risk

        view = build_risk(snapshot)
        return PageView(title="Risk", status=view.status, lines=view.lines)
    if normalized == "notifications":
        from dashboard.pages.notifications import build_notifications

        view = build_notifications(snapshot)
        return PageView(title="Notifications", status=view.status, lines=view.lines)
    if normalized == "activity":
        from dashboard.pages.activity import build_activity

        view = build_activity(snapshot)
        return PageView(title="Activity", status=view.status, lines=view.lines)
    if normalized == "system-status":
        from dashboard.pages.system_status import build_system_status

        view = build_system_status(snapshot)
        return PageView(title="System Status", status=view.status, lines=view.lines)

    title = _title_for_slug(normalized)
    return PageView(
        title=title,
        status=DashboardSectionStatus.NOT_AVAILABLE,
        lines=(f"{title}: not_available until its dedicated page module is implemented.",),
    )


def _title_for_slug(slug: str) -> str:
    for page in PAGE_REGISTRY:
        if page.slug == slug:
            return page.title
    return "Unknown"
