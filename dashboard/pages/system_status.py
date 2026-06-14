"""System Status page view helpers."""

from __future__ import annotations

from dataclasses import dataclass

from dashboard.models import DashboardSectionStatus, DashboardSnapshot
from dashboard.redaction import redact_mapping


@dataclass(frozen=True)
class SystemStatusView:
    status: DashboardSectionStatus
    lines: tuple[str, ...]


def build_system_status(snapshot: DashboardSnapshot) -> SystemStatusView:
    lines = [
        f"Freshness: {snapshot.source_metadata.freshness_status.value}",
        f"System status: {snapshot.system.status.value}",
    ]
    if snapshot.system.status is not DashboardSectionStatus.AVAILABLE:
        lines.extend(snapshot.system.reasons or ("not_available",))
    elif snapshot.system.items:
        for item in snapshot.system.items:
            safe = redact_mapping(item)
            lines.append(
                f"{safe.get('subsystem', 'system')}: {safe.get('severity', 'info')} "
                f"{safe.get('message', '')}".strip()
            )
    else:
        lines.extend(snapshot.system.reasons or ("no_system_warnings",))
    return SystemStatusView(status=snapshot.system.status, lines=tuple(lines))
