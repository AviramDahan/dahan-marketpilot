from datetime import datetime, timezone

from marketpilot.notification_events import (
    NotificationEventType,
    event_for_alert_family,
    event_for_backtest_preview,
    event_for_full_close,
    event_for_lifecycle_transition,
    event_for_order_intent,
    event_for_partial_close,
    event_for_recovery_mismatch,
    event_for_risk_rejection,
    event_for_sizing_decision,
    event_for_stop_target_update,
    required_telegram_alert_families,
)
from marketpilot.telegram import format_telegram_message


def test_all_required_telegram_alert_families_have_stable_event_types():
    required = {
        "buy_candidate",
        "watch",
        "paper_buy",
        "paper_sell",
        "submitted_order",
        "partial_fill",
        "full_fill",
        "stop",
        "target",
        "partial_close",
        "full_close",
        "rejected_order",
        "canceled_order",
        "regime_change",
        "system",
        "error",
        "start_restart",
        "daily_summary",
    }

    families = required_telegram_alert_families()

    assert set(families) == required
    assert all(families[name] for name in required)
    assert len(set(families.values())) == len(families)


def test_required_alert_payloads_are_sanitized_and_format_ready():
    event = event_for_alert_family(
        "buy_candidate",
        "signal-1",
        {
            "symbol": "MSFT",
            "setup": "volume_breakout",
            "classification": "BUY_CANDIDATE",
            "score": 82,
            "mode": "limited_paper",
            "activation_state": "approved_for_limited_paper",
            "telegram_token": "must-not-render",
            "reason": "guaranteed profit is prohibited",
        },
        timestamp=datetime(2026, 6, 14, 20, 0, tzinfo=timezone.utc),
    )

    text = format_telegram_message(event)

    assert event.event_type == "buy_candidate"
    assert event.payload["telegram_token"] == "[redacted]"
    assert "SIMULATED PAPER TRADING ONLY - NOT FINANCIAL ADVICE" in text
    assert "MSFT" in text
    assert "must-not-render" not in text
    assert "guaranteed profit" not in text.lower()
    assert "[removed unsafe claim]" in text


def test_existing_phase_6_event_types_remain_backward_compatible():
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
