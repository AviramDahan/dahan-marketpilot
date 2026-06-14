from marketpilot.notification_events import FakeNotificationCollector, NotificationEventType, event_for_backtest_preview


def test_backtest_preview_event_is_historical_and_transport_neutral():
    event = event_for_backtest_preview("bt-1", {"api_key": "secret", "symbol": "SPY"})

    assert event.event_type == NotificationEventType.BACKTEST_PREVIEW.value
    assert event.payload["preview"] is True
    assert event.payload["historical"] is True
    assert event.payload["transport"] == "fake_collector_only"
    assert event.payload["controls_safety_logic"] is False
    assert event.payload["api_key"] == "[redacted]"


def test_preview_uses_fake_collector_only():
    collector = FakeNotificationCollector()
    event = event_for_backtest_preview("bt-2", {"message": "preview"})

    assert collector.emit(event) is True
    assert collector.events == [event]
