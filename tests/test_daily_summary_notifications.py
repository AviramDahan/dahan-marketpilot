from datetime import date, datetime, timezone

from marketpilot.notification_events import (
    FakeNotificationCollector,
    event_for_backtest_preview,
    event_for_daily_summary,
)
from marketpilot.telegram import (
    TelegramConfig,
    TelegramDeliveryService,
    TelegramDeliveryStatus,
    format_telegram_message,
)


def test_daily_summary_event_contains_required_end_of_day_sections():
    event = event_for_daily_summary(
        correlation_id="summary-2026-06-14",
        summary_date=date(2026, 6, 14),
        active_paper_mode="limited_paper",
        new_signals=3,
        entries=1,
        exits=2,
        open_positions=4,
        rejected_actions=1,
        system_warnings=("reconciliation_check_pending",),
        timestamp=datetime(2026, 6, 14, 21, 0, tzinfo=timezone.utc),
    )

    assert event.event_type == "daily_summary"
    assert event.payload["artifact"] == "end_of_day_summary"
    assert event.payload["source"] == "scheduled_end_of_day"
    assert event.payload["summary_date"] == "2026-06-14"
    assert event.payload["active_paper_mode"] == "limited_paper"
    assert event.payload["new_signals"] == 3
    assert event.payload["entries"] == 1
    assert event.payload["exits"] == 2
    assert event.payload["open_positions"] == 4
    assert event.payload["rejected_actions"] == 1
    assert event.payload["system_warnings"] == ("reconciliation_check_pending",)
    assert event.payload["authoritative_portfolio_source"] == "quantconnect"
    assert event.payload["invented_portfolio_values"] is False


def test_daily_summary_message_is_sanitized_plain_text():
    event = event_for_daily_summary(
        correlation_id="summary-safe",
        summary_date=date(2026, 6, 14),
        active_paper_mode="shadow",
        new_signals=1,
        entries=0,
        exits=0,
        open_positions=0,
        rejected_actions=0,
        system_warnings=("guaranteed return is forbidden",),
        payload={"telegram_token": "must-not-render"},
    )

    text = format_telegram_message(event)

    assert "SIMULATED PAPER TRADING ONLY - NOT FINANCIAL ADVICE" in text
    assert "shadow" in text
    assert "must-not-render" not in text
    assert "telegram_token" not in text
    assert "guaranteed return" not in text.lower()


def test_backtest_preview_remains_fake_collector_only_and_real_telegram_disabled_by_default():
    event = event_for_backtest_preview("bt-preview-1", {"symbol": "MSFT"})
    collector = FakeNotificationCollector()
    service = TelegramDeliveryService(
        TelegramConfig(
            paper_trading_only=True,
            telegram_enabled=False,
            delivery_required_for_safety=False,
        )
    )

    assert collector.emit(event) is True
    assert collector.events == [event]
    assert event.payload["transport"] == "fake_collector_only"
    assert service.deliver(event).status is TelegramDeliveryStatus.DISABLED
