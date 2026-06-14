"""Risk page view helpers."""

from __future__ import annotations

from dataclasses import dataclass

from dashboard.models import DashboardSectionStatus, DashboardSnapshot


@dataclass(frozen=True)
class RiskView:
    status: DashboardSectionStatus
    lines: tuple[str, ...]


def build_risk(snapshot: DashboardSnapshot) -> RiskView:
    lines = [
        "Status only.",
        f"Freshness: {snapshot.source_metadata.freshness_status.value}",
        f"Risk status: {snapshot.risk.status.value}",
    ]
    if snapshot.risk.status is not DashboardSectionStatus.AVAILABLE:
        lines.extend(snapshot.risk.reasons or ("not_available",))
    elif snapshot.risk.items:
        for item in snapshot.risk.items:
            lines.append(f"{item.get('name', 'risk')}: {item.get('state', 'unknown')}")
    else:
        lines.append("No risk warnings reported by the typed dashboard source.")
    return RiskView(status=snapshot.risk.status, lines=tuple(lines))
