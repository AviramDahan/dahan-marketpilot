"""Activity page view helpers."""

from __future__ import annotations

from dataclasses import dataclass

from dashboard.models import DashboardSectionStatus, DashboardSnapshot


@dataclass(frozen=True)
class ActivityView:
    status: DashboardSectionStatus
    lines: tuple[str, ...]


def build_activity(snapshot: DashboardSnapshot) -> ActivityView:
    lines = [
        f"Freshness: {snapshot.source_metadata.freshness_status.value}",
        f"Activity status: {snapshot.activity.status.value}",
    ]
    if snapshot.activity.status is not DashboardSectionStatus.AVAILABLE:
        lines.extend(snapshot.activity.reasons or ("not_available",))
    elif snapshot.activity.items:
        for item in snapshot.activity.items:
            lines.append(
                f"{item.get('event', 'event')}: "
                f"{item.get('source_timestamp', snapshot.source_metadata.source_timestamp or 'unknown')}"
            )
    else:
        lines.append("No recent activity reported by the typed dashboard source.")
    return ActivityView(status=snapshot.activity.status, lines=tuple(lines))
