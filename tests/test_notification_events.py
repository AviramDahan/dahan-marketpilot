from marketpilot.notification_events import (
    NotificationEventType,
    event_for_backtest_preview,
    event_for_full_close,
    event_for_lifecycle_transition,
    event_for_order_intent,
    event_for_partial_close,
    event_for_recovery_mismatch,
    event_for_risk_rejection,
    event_for_sizing_decision,
    event_for_stop_target_update,
)


def test_notification_domain_events_have_stable_types_and_sanitized_payloads():
    event = event_for_risk_rejection("risk-1", {"symbol": "MSFT", "telegram_token": "secret"})

    assert event.event_type == "risk_rejection"
    assert event.payload["telegram_token"] == "[redacted]"
    assert event.severity == "warning"


def test_all_phase_6_event_factories_exist():
    factories = (
        event_for_risk_rejection,
        event_for_sizing_decision,
        event_for_order_intent,
        event_for_lifecycle_transition,
        event_for_stop_target_update,
        event_for_partial_close,
        event_for_full_close,
        event_for_recovery_mismatch,
        event_for_backtest_preview,
    )

    assert {factory("id", {}).event_type for factory in factories} == {event.value for event in NotificationEventType}
