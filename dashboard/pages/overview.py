"""Pure Overview page helpers."""

from __future__ import annotations

from dataclasses import dataclass

from dashboard.models import DashboardSnapshot
from marketpilot.constants import DISCLAIMER


@dataclass(frozen=True)
class OverviewView:
    lines: tuple[str, ...]


def build_overview(snapshot: DashboardSnapshot) -> OverviewView:
    metadata = snapshot.source_metadata
    warnings = _system_warnings(snapshot)
    lines = (
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
    return OverviewView(lines=lines)


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
