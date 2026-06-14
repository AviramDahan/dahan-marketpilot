"""Strategies page view helpers."""

from __future__ import annotations

from dataclasses import dataclass

from dashboard.models import DashboardSectionStatus, DashboardSnapshot


@dataclass(frozen=True)
class StrategiesView:
    status: DashboardSectionStatus
    lines: tuple[str, ...]


def build_strategies(snapshot: DashboardSnapshot) -> StrategiesView:
    lines = [
        "Status display only.",
        f"Freshness: {snapshot.source_metadata.freshness_status.value}",
        f"Strategies status: {snapshot.strategies.status.value}",
    ]
    if snapshot.strategies.status is not DashboardSectionStatus.AVAILABLE:
        lines.extend(snapshot.strategies.reasons or ("not_available",))
    elif snapshot.strategies.items:
        for item in snapshot.strategies.items:
            lines.append(
                f"{item.get('name', 'strategy')}: {item.get('readiness', 'unknown')} "
                f"Paper mode: {item.get('paper_mode', 'unknown')}"
            )
    else:
        lines.append("No strategy readiness records reported by the typed dashboard source.")
    return StrategiesView(status=snapshot.strategies.status, lines=tuple(lines))
