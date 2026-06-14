from marketpilot.notification_events import FakeNotificationCollector, event_for_order_intent


def test_fake_collector_records_events_without_real_delivery():
    collector = FakeNotificationCollector()
    event = event_for_order_intent("order-1", {"symbol": "MSFT"})

    assert collector.emit(event) is True
    assert collector.events == [event]


def test_fake_delivery_failure_does_not_raise_or_block_safety_flow():
    collector = FakeNotificationCollector(fail_delivery=True)
    event = event_for_order_intent("order-1", {"symbol": "MSFT"})

    assert collector.emit(event) is False
    assert collector.failures == ["order_intent"]
    assert collector.events == []
