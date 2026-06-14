"""Transport-neutral notification-domain events."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Mapping


class NotificationEventType(str, Enum):
    RISK_REJECTION = "risk_rejection"
    SIZING_DECISION = "sizing_decision"
    ORDER_INTENT = "order_intent"
    LIFECYCLE_TRANSITION = "lifecycle_transition"
    STOP_TARGET_UPDATE = "stop_target_update"
    PARTIAL_CLOSE = "partial_close"
    FULL_CLOSE = "full_close"
    RECOVERY_MISMATCH = "recovery_mismatch"
    BACKTEST_PREVIEW = "backtest_preview"


_REQUIRED_TELEGRAM_ALERT_FAMILIES: dict[str, str] = {
    "buy_candidate": "buy_candidate",
    "watch": "watch",
    "paper_buy": "paper_buy",
    "paper_sell": "paper_sell",
    "submitted_order": "submitted_order",
    "partial_fill": "partial_fill",
    "full_fill": "full_fill",
    "stop": "stop",
    "target": "target",
    "partial_close": "partial_close",
    "full_close": "full_close",
    "rejected_order": "rejected_order",
    "canceled_order": "canceled_order",
    "regime_change": "regime_change",
    "system": "system",
    "error": "error",
    "start_restart": "start_restart",
    "daily_summary": "daily_summary",
}

_WARNING_ALERT_FAMILIES = {
    "watch",
    "stop",
    "target",
    "rejected_order",
    "canceled_order",
    "regime_change",
    "system",
}

_HIGH_SEVERITY_ALERT_FAMILIES = {"error"}


@dataclass(frozen=True)
class NotificationDomainEvent:
    event_type: str
    timestamp: datetime
    correlation_id: str
    payload: Mapping[str, object]
    severity: str = "info"

    @classmethod
    def create(
        cls,
        event_type: NotificationEventType | str,
        correlation_id: str,
        payload: Mapping[str, object],
        *,
        severity: str = "info",
        timestamp: datetime | None = None,
    ) -> "NotificationDomainEvent":
        event_value = event_type.value if isinstance(event_type, NotificationEventType) else str(event_type)
        return cls(
            event_type=event_value,
            timestamp=timestamp or datetime.now(timezone.utc),
            correlation_id=correlation_id,
            payload=_sanitize_payload(payload),
            severity=severity,
        )


@dataclass
class FakeNotificationCollector:
    fail_delivery: bool = False
    events: list[NotificationDomainEvent] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)

    def emit(self, event: NotificationDomainEvent) -> bool:
        if self.fail_delivery:
            self.failures.append(event.event_type)
            return False
        self.events.append(event)
        return True


@dataclass
class NotificationDeduplicator:
    seen_keys: set[str] = field(default_factory=set)

    def should_emit(self, event: NotificationDomainEvent) -> bool:
        key = notification_delivery_key(event)
        if key in self.seen_keys:
            return False
        self.seen_keys.add(key)
        return True


@dataclass
class NotificationRateLimiter:
    max_events: int
    window_seconds: int
    timestamps: list[datetime] = field(default_factory=list)

    def allow(self, now: datetime | None = None) -> bool:
        current = now or datetime.now(timezone.utc)
        window_start = current - timedelta(seconds=self.window_seconds)
        self.timestamps = [stamp for stamp in self.timestamps if stamp >= window_start]
        if len(self.timestamps) >= self.max_events:
            return False
        self.timestamps.append(current)
        return True


def event_for_risk_rejection(correlation_id: str, payload: Mapping[str, object]) -> NotificationDomainEvent:
    return NotificationDomainEvent.create(NotificationEventType.RISK_REJECTION, correlation_id, payload, severity="warning")


def event_for_sizing_decision(correlation_id: str, payload: Mapping[str, object]) -> NotificationDomainEvent:
    return NotificationDomainEvent.create(NotificationEventType.SIZING_DECISION, correlation_id, payload)


def event_for_order_intent(correlation_id: str, payload: Mapping[str, object]) -> NotificationDomainEvent:
    return NotificationDomainEvent.create(NotificationEventType.ORDER_INTENT, correlation_id, payload)


def event_for_lifecycle_transition(correlation_id: str, payload: Mapping[str, object]) -> NotificationDomainEvent:
    return NotificationDomainEvent.create(NotificationEventType.LIFECYCLE_TRANSITION, correlation_id, payload)


def event_for_stop_target_update(correlation_id: str, payload: Mapping[str, object]) -> NotificationDomainEvent:
    return NotificationDomainEvent.create(NotificationEventType.STOP_TARGET_UPDATE, correlation_id, payload)


def event_for_partial_close(correlation_id: str, payload: Mapping[str, object]) -> NotificationDomainEvent:
    return NotificationDomainEvent.create(NotificationEventType.PARTIAL_CLOSE, correlation_id, payload)


def event_for_full_close(correlation_id: str, payload: Mapping[str, object]) -> NotificationDomainEvent:
    return NotificationDomainEvent.create(NotificationEventType.FULL_CLOSE, correlation_id, payload)


def event_for_recovery_mismatch(correlation_id: str, payload: Mapping[str, object]) -> NotificationDomainEvent:
    return NotificationDomainEvent.create(NotificationEventType.RECOVERY_MISMATCH, correlation_id, payload, severity="warning")


def required_telegram_alert_families() -> Mapping[str, str]:
    """Return stable Phase 8 alert family names mapped to event type values."""

    return dict(_REQUIRED_TELEGRAM_ALERT_FAMILIES)


def event_for_alert_family(
    family: str,
    correlation_id: str,
    payload: Mapping[str, object],
    *,
    severity: str | None = None,
    timestamp: datetime | None = None,
) -> NotificationDomainEvent:
    event_type = _REQUIRED_TELEGRAM_ALERT_FAMILIES.get(family)
    if event_type is None:
        raise ValueError(f"unsupported telegram alert family: {family}")
    resolved_severity = severity or _default_alert_severity(family)
    return NotificationDomainEvent.create(event_type, correlation_id, payload, severity=resolved_severity, timestamp=timestamp)


def event_for_system_incident(
    correlation_id: str,
    payload: Mapping[str, object],
    *,
    severity: str = "high",
) -> NotificationDomainEvent:
    return NotificationDomainEvent.create("system", correlation_id, payload, severity=severity)


def event_for_protective_recovery(correlation_id: str, payload: Mapping[str, object]) -> NotificationDomainEvent:
    return NotificationDomainEvent.create("protective_recovery", correlation_id, payload, severity="high")


def event_for_backtest_preview(correlation_id: str, payload: Mapping[str, object]) -> NotificationDomainEvent:
    preview_payload = {
        "preview": True,
        "historical": True,
        "transport": "fake_collector_only",
        "controls_safety_logic": False,
        **payload,
    }
    return NotificationDomainEvent.create(NotificationEventType.BACKTEST_PREVIEW, correlation_id, preview_payload)


def notification_delivery_key(event: NotificationDomainEvent) -> str:
    return f"{event.event_type}|{event.correlation_id}"


def _default_alert_severity(family: str) -> str:
    if family in _HIGH_SEVERITY_ALERT_FAMILIES:
        return "high"
    if family in _WARNING_ALERT_FAMILIES:
        return "warning"
    return "info"


def _sanitize_payload(payload: Mapping[str, object]) -> dict[str, object]:
    sanitized: dict[str, object] = {}
    for key, value in payload.items():
        if any(marker in key.lower() for marker in ("secret", "token", "password", "credential", "api_key", "chat_id")):
            sanitized[key] = "[redacted]"
        else:
            sanitized[key] = value
    return sanitized
