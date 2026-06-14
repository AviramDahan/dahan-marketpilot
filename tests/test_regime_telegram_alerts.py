from datetime import datetime, timezone

from marketpilot.notification_events import (
    event_for_regime_transition,
    notification_delivery_key,
)
from marketpilot.regime import MarketRegime


def test_regime_transition_event_emits_only_when_state_changes():
    event = event_for_regime_transition(
        previous_regime=MarketRegime.NEUTRAL,
        current_regime=MarketRegime.RISK_OFF,
        correlation_id="regime-2026-06-14",
        timestamp=datetime(2026, 6, 14, 20, 30, tzinfo=timezone.utc),
        reasons=("benchmarks_defensive",),
    )

    assert event is not None
    assert event.event_type == "regime_change"
    assert event.correlation_id == "regime-2026-06-14"
    assert event.payload["previous_regime"] == "NEUTRAL"
    assert event.payload["current_regime"] == "RISK_OFF"
    assert event.payload["reasons"] == ("benchmarks_defensive",)
    assert event.severity == "warning"


def test_unchanged_regime_state_produces_no_alert():
    event = event_for_regime_transition(
        previous_regime=MarketRegime.RISK_ON,
        current_regime=MarketRegime.RISK_ON,
        correlation_id="regime-unchanged",
        timestamp=datetime(2026, 6, 14, 20, 30, tzinfo=timezone.utc),
    )

    assert event is None


def test_regime_delivery_key_uses_event_type_and_correlation_id():
    first = event_for_regime_transition(
        previous_regime="RISK_ON",
        current_regime="NEUTRAL",
        correlation_id="regime-same-correlation",
    )
    second = event_for_regime_transition(
        previous_regime="NEUTRAL",
        current_regime="RISK_OFF",
        correlation_id="regime-same-correlation",
    )

    assert first is not None
    assert second is not None
    assert notification_delivery_key(first) == "regime_change|regime-same-correlation"
    assert notification_delivery_key(second) == "regime_change|regime-same-correlation"
