from datetime import datetime, timedelta, timezone

from marketpilot.notification_events import (
    NotificationDeduplicator,
    NotificationRateLimiter,
    event_for_alert_family,
    notification_delivery_key,
)
from marketpilot.telegram import (
    TelegramConfig,
    TelegramDeliveryService,
    TelegramDeliveryStatus,
)


class FakeTelegramHttpClient:
    def __init__(self):
        self.calls = []

    def __call__(self, *, url, payload, timeout_seconds):
        self.calls.append({"url": url, "payload": payload, "timeout_seconds": timeout_seconds})
        return {"ok": True, "result": {"message_id": len(self.calls)}}


def _config():
    return TelegramConfig(
        paper_trading_only=True,
        telegram_enabled=True,
        delivery_required_for_safety=False,
        token_env_var="MP_TELEGRAM_BOT_TOKEN",
        chat_id_env_var="MP_TELEGRAM_CHAT_ID",
        bot_token="fake-token-from-external-store",
        chat_id="fake-chat-from-external-store",
    )


def test_dedup_uses_event_type_and_correlation_id_across_alert_families():
    deduplicator = NotificationDeduplicator()
    client = FakeTelegramHttpClient()
    service = TelegramDeliveryService(_config(), http_client=client, deduplicator=deduplicator)
    first = event_for_alert_family("submitted_order", "shared-correlation", {"symbol": "MSFT"})
    duplicate = event_for_alert_family("submitted_order", "shared-correlation", {"symbol": "MSFT"})
    different_type = event_for_alert_family("full_fill", "shared-correlation", {"symbol": "MSFT"})

    assert notification_delivery_key(first) == "submitted_order|shared-correlation"
    assert notification_delivery_key(different_type) == "full_fill|shared-correlation"
    assert service.deliver(first).status is TelegramDeliveryStatus.DELIVERED
    assert service.deliver(duplicate).status is TelegramDeliveryStatus.DUPLICATE_SUPPRESSED
    assert service.deliver(different_type).status is TelegramDeliveryStatus.DELIVERED
    assert len(client.calls) == 2


def test_local_rate_limiter_is_conservative_and_has_no_paid_broadcast_payload():
    client = FakeTelegramHttpClient()
    service = TelegramDeliveryService(
        _config(),
        http_client=client,
        rate_limiter=NotificationRateLimiter(max_events=2, window_seconds=60),
    )
    start = datetime(2026, 6, 14, 20, 0, tzinfo=timezone.utc)

    delivered_1 = service.deliver(event_for_alert_family("system", "system-1", {"system_health": "ok"}, timestamp=start))
    delivered_2 = service.deliver(
        event_for_alert_family("error", "error-1", {"reason": "incident"}, timestamp=start + timedelta(seconds=1))
    )
    limited = service.deliver(
        event_for_alert_family("daily_summary", "summary-1", {"active_paper_mode": "limited_paper"}, timestamp=start + timedelta(seconds=2))
    )

    assert delivered_1.status is TelegramDeliveryStatus.DELIVERED
    assert delivered_2.status is TelegramDeliveryStatus.DELIVERED
    assert limited.status is TelegramDeliveryStatus.RATE_LIMITED
    assert len(client.calls) == 2
    assert all("allow_paid_broadcast" not in call["payload"] for call in client.calls)
    assert all("parse_mode" not in call["payload"] for call in client.calls)


def test_rate_limiter_window_expiry_allows_later_alerts_without_mutating_dedup():
    limiter = NotificationRateLimiter(max_events=1, window_seconds=60)
    first_time = datetime(2026, 6, 14, 20, 0, tzinfo=timezone.utc)
    later_time = first_time + timedelta(seconds=61)

    assert limiter.allow(first_time) is True
    assert limiter.allow(first_time + timedelta(seconds=5)) is False
    assert limiter.allow(later_time) is True
