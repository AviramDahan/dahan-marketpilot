from datetime import datetime, timezone

from marketpilot.notification_events import (
    NotificationDeduplicator,
    NotificationRateLimiter,
    event_for_lifecycle_transition,
)


def test_deduplicator_suppresses_same_event_and_correlation_id_only():
    dedup = NotificationDeduplicator()
    event = event_for_lifecycle_transition("order-1", {"state": "submitted"})

    assert dedup.should_emit(event) is True
    assert dedup.should_emit(event) is False
    assert dedup.should_emit(event_for_lifecycle_transition("order-2", {"state": "submitted"})) is True


def test_rate_limiter_limits_notification_emission_only():
    limiter = NotificationRateLimiter(max_events=2, window_seconds=60)
    now = datetime(2026, 6, 14, tzinfo=timezone.utc)

    assert limiter.allow(now) is True
    assert limiter.allow(now) is True
    assert limiter.allow(now) is False
