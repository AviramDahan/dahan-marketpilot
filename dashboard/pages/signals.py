"""Signals page view helpers."""

from __future__ import annotations

from dataclasses import dataclass

from dashboard.models import DashboardSectionStatus, DashboardSnapshot


@dataclass(frozen=True)
class SignalsView:
    status: DashboardSectionStatus
    lines: tuple[str, ...]


def build_signals(snapshot: DashboardSnapshot) -> SignalsView:
    lines = [
        "Evidence is observational.",
        f"Freshness: {snapshot.source_metadata.freshness_status.value}",
        f"Signals status: {snapshot.signals.status.value}",
    ]
    if snapshot.signals.status is not DashboardSectionStatus.AVAILABLE:
        lines.extend(snapshot.signals.reasons or ("not_available",))
    elif snapshot.signals.items:
        for item in snapshot.signals.items:
            lines.append(
                f"{item.get('symbol', 'UNKNOWN')}: "
                f"{item.get('classification', item.get('state', 'unclassified'))}"
            )
    else:
        lines.append("No signal evidence reported by the typed dashboard source.")
    return SignalsView(status=snapshot.signals.status, lines=tuple(lines))
