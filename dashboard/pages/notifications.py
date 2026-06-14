"""Notifications page view helpers."""

from __future__ import annotations

from dataclasses import dataclass

from dashboard.models import DashboardSectionStatus, DashboardSnapshot
from dashboard.redaction import REDACTED, SECRET_KEY_HINTS, redact_mapping


@dataclass(frozen=True)
class NotificationsView:
    status: DashboardSectionStatus
    lines: tuple[str, ...]


def build_notifications(snapshot: DashboardSnapshot) -> NotificationsView:
    lines = [
        "Delivery is non-authoritative.",
        f"Freshness: {snapshot.source_metadata.freshness_status.value}",
        f"Notifications status: {snapshot.notifications.status.value}",
    ]
    if snapshot.notifications.status is not DashboardSectionStatus.AVAILABLE:
        lines.extend(snapshot.notifications.reasons or ("not_available",))
    elif snapshot.notifications.items:
        for item in snapshot.notifications.items:
            safe = redact_mapping(item)
            detail = _safe_detail(safe.get("detail", ""))
            lines.append(
                f"{safe.get('channel', 'notification')}: {safe.get('status', 'unknown')} "
                f"{detail}".strip()
            )
    else:
        lines.append("No notification delivery records reported by the typed dashboard source.")
    return NotificationsView(status=snapshot.notifications.status, lines=tuple(lines))


def _safe_detail(value: object) -> str:
    text = str(value)
    lowered = text.lower()
    if any(marker in lowered for marker in SECRET_KEY_HINTS):
        return REDACTED
    return text
