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
