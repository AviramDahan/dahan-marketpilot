"""Backtests page view helpers."""

from __future__ import annotations

from dataclasses import dataclass

from dashboard.models import DashboardSectionStatus, DashboardSnapshot


@dataclass(frozen=True)
class BacktestsView:
    status: DashboardSectionStatus
    lines: tuple[str, ...]


def build_backtests(snapshot: DashboardSnapshot) -> BacktestsView:
    lines = [
        "No performance claim is made by this dashboard view.",
        f"Freshness: {snapshot.source_metadata.freshness_status.value}",
        f"Backtests status: {snapshot.backtests.status.value}",
    ]
    if snapshot.backtests.reasons:
        lines.extend(snapshot.backtests.reasons)
    if snapshot.backtests.status is DashboardSectionStatus.AVAILABLE and snapshot.backtests.items:
        for item in snapshot.backtests.items:
            lines.append(f"{item.get('label', 'report')}: {item.get('state', 'available')}")
    elif not snapshot.backtests.reasons:
        lines.append("not_available")
    return BacktestsView(status=snapshot.backtests.status, lines=tuple(lines))
