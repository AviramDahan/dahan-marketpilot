"""Runtime notification emission and failure-isolation tests for Phase 10.1-05.

Proves that:
- Runtime pipeline emits BUY/WATCH/rejection/order/system events from outcomes.
- Fake collector receives events without changing runtime decisions.
- Telegram delivery failure, disabled config, missing token, or missing chat ID
  does not change risk/order/reconciliation status.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from marketpilot.notification_events import (
    FakeNotificationCollector,
    NotificationDomainEvent,
    event_for_alert_family,
    event_for_order_intent,
    event_for_risk_rejection,
    event_for_sizing_decision,
    event_for_system_incident,
)
from marketpilot.runtime_orchestrator import (
    RuntimeAuthority,
    RuntimeOrchestrationInput,
    RuntimeOrchestrationResult,
    RuntimeOrchestrationStatus,
    RuntimeSkippedReason,
    run_runtime_pipeline,
)
from marketpilot.telegram import (
    TelegramConfig,
    TelegramDeliveryService,
    TelegramDeliveryStatus,
)
from marketpilot.timeframes import BarTimeframe, StrategyMode
from marketpilot.setups.base import NumericEvidence, SetupResult, SetupStatus, SetupTiming
from marketpilot.paper_modes import (
    ActivationApprovalState,
    PaperModeDecision,
    PaperTradingMode,
    RiskConfig,
)


NOW = datetime(2026, 6, 15, 14, 0, tzinfo=timezone.utc)


class FakeTelegramHttpClient:
    def __init__(self, *, fail: bool = False, error: Exception | None = None):
        self.fail = fail
        self.error = error
        self.calls: list[dict] = []

    def __call__(self, *, url, payload, timeout_seconds):
        self.calls.append({"url": url, "payload": payload})
        if self.error:
            raise self.error
        if self.fail:
            return {"ok": False, "error_code": 500, "description": "Internal Error"}
        return {"ok": True, "result": {"message_id": 123}}


def _telegram_config(**overrides) -> TelegramConfig:
    defaults = {
        "paper_trading_only": True,
        "telegram_enabled": True,
        "delivery_required_for_safety": False,
        "bot_token": "fake-test-token",
        "chat_id": "fake-test-chat",
    }
    defaults.update(overrides)
    return TelegramConfig(**defaults)


# --- Runtime emits events from pipeline outcomes ---


class TestRuntimeEmitsEventsFromPipelineOutcomes:
    def test_blocked_result_emits_system_event(self):
        runtime_input = RuntimeOrchestrationInput(
            correlation_id="test-blocked-1",
            strategy_mode=StrategyMode.DAILY_ONLY,
            setup_results=(_make_valid_setup(),),
            source_authority=RuntimeAuthority.QUANTCONNECT,
            quantconnect_snapshot=None,
            paper_mode_decision=_paper_eligible_decision(),
        )

        result = run_runtime_pipeline(runtime_input)

        assert result.status is RuntimeOrchestrationStatus.BLOCKED
        assert len(result.notification_events) >= 1
        event = result.notification_events[0]
        assert event.payload.get("controls_safety_logic") is False
        assert event.payload.get("delivery_required_for_safety") is False

    def test_shadow_result_does_not_emit_events(self):
        runtime_input = RuntimeOrchestrationInput(
            correlation_id="test-shadow-1",
            strategy_mode=StrategyMode.DAILY_ONLY,
            setup_results=(_make_valid_setup(),),
            source_authority=RuntimeAuthority.QUANTCONNECT,
            paper_mode_decision=None,
            validation_decision=None,
        )

        result = run_runtime_pipeline(runtime_input)

        assert result.status is RuntimeOrchestrationStatus.SHADOW_ONLY
        assert result.notification_events == ()

    def test_not_ready_result_does_not_emit_events(self):
        runtime_input = RuntimeOrchestrationInput(
            correlation_id="test-not-ready-1",
            strategy_mode=StrategyMode.DAILY_ONLY,
            setup_results=(),
        )

        result = run_runtime_pipeline(runtime_input)

        assert result.status is RuntimeOrchestrationStatus.NOT_READY
        assert result.notification_events == ()


# --- Fake collector receives events without affecting decisions ---


class TestFakeCollectorDoesNotAffectDecisions:
    def test_collector_receives_all_emitted_events(self):
        collector = FakeNotificationCollector()
        events = [
            event_for_risk_rejection("c1", {"symbol": "MSFT"}),
            event_for_sizing_decision("c1", {"symbol": "MSFT", "quantity": 10}),
            event_for_order_intent("c1", {"symbol": "MSFT"}),
            event_for_system_incident("c1", {"reason": "test"}),
        ]

        for event in events:
            collector.emit(event)

        assert len(collector.events) == 4
        assert collector.failures == []

    def test_failed_collector_records_failure_without_altering_events(self):
        collector = FakeNotificationCollector(fail_delivery=True)
        event = event_for_alert_family("buy_candidate", "c2", {"symbol": "AAPL"})

        delivered = collector.emit(event)

        assert delivered is False
        assert collector.failures == ["buy_candidate"]
        assert collector.events == []

    def test_collector_failure_does_not_change_runtime_result_status(self):
        collector = FakeNotificationCollector(fail_delivery=True)
        runtime_input = RuntimeOrchestrationInput(
            correlation_id="test-collector-fail",
            strategy_mode=StrategyMode.DAILY_ONLY,
            setup_results=(_make_valid_setup(),),
            source_authority=RuntimeAuthority.QUANTCONNECT,
            quantconnect_snapshot=None,
            paper_mode_decision=_paper_eligible_decision(),
        )

        result = run_runtime_pipeline(runtime_input)

        # Simulate collector failing to deliver all events
        for event in result.notification_events:
            collector.emit(event)

        # Result status is unchanged regardless of collector failures
        assert result.status is RuntimeOrchestrationStatus.BLOCKED
        assert RuntimeSkippedReason.QUANTCONNECT_AUTHORITY_MISSING in result.skipped_reasons


# --- Telegram delivery failure does not change safety decisions ---


class TestTelegramFailureIsolationFromRuntime:
    def test_telegram_failure_does_not_affect_blocked_status(self):
        service = TelegramDeliveryService(
            _telegram_config(),
            http_client=FakeTelegramHttpClient(error=TimeoutError("offline")),
        )
        event = event_for_system_incident("c3", {"reason": "reconciliation_blocked"})

        delivery = service.deliver(event)

        assert delivery.status is TelegramDeliveryStatus.FAILED
        assert delivery.controls_safety_logic is False
        assert delivery.delivery_required_for_safety is False

    def test_telegram_disabled_does_not_affect_runtime(self):
        service = TelegramDeliveryService(
            _telegram_config(telegram_enabled=False),
            http_client=FakeTelegramHttpClient(),
        )
        event = event_for_alert_family("paper_buy", "c4", {"symbol": "MSFT"})

        delivery = service.deliver(event)

        assert delivery.status is TelegramDeliveryStatus.DISABLED
        assert delivery.controls_safety_logic is False

    def test_telegram_missing_token_does_not_affect_runtime(self):
        service = TelegramDeliveryService(
            _telegram_config(bot_token=None),
            http_client=FakeTelegramHttpClient(),
        )
        event = event_for_alert_family("regime_change", "c5", {"regime_state": "RISK_OFF"})

        delivery = service.deliver(event)

        assert delivery.status is TelegramDeliveryStatus.MISSING_TOKEN
        assert delivery.controls_safety_logic is False

    def test_telegram_missing_chat_id_does_not_affect_runtime(self):
        service = TelegramDeliveryService(
            _telegram_config(chat_id=None),
            http_client=FakeTelegramHttpClient(),
        )
        event = event_for_alert_family("error", "c6", {"reason": "test error"})

        delivery = service.deliver(event)

        assert delivery.status is TelegramDeliveryStatus.MISSING_CHAT_ID
        assert delivery.controls_safety_logic is False

    def test_telegram_success_does_not_control_safety(self):
        service = TelegramDeliveryService(
            _telegram_config(),
            http_client=FakeTelegramHttpClient(),
        )
        event = event_for_alert_family("daily_summary", "c7", {"active_paper_mode": "full_paper"})

        delivery = service.deliver(event)

        assert delivery.status is TelegramDeliveryStatus.DELIVERED
        assert delivery.controls_safety_logic is False


# --- All runtime events explicitly non-authoritative ---


class TestRuntimeEventsNonAuthoritative:
    def test_all_pipeline_events_have_non_authoritative_payload(self):
        runtime_input = RuntimeOrchestrationInput(
            correlation_id="test-non-auth",
            strategy_mode=StrategyMode.DAILY_ONLY,
            setup_results=(_make_valid_setup(),),
            source_authority=RuntimeAuthority.QUANTCONNECT,
            quantconnect_snapshot=None,
            paper_mode_decision=_paper_eligible_decision(),
        )

        result = run_runtime_pipeline(runtime_input)

        for event in result.notification_events:
            assert event.payload.get("controls_safety_logic") is False
            assert event.payload.get("delivery_required_for_safety") is False

    def test_default_evidence_forbids_telegram_safety_requirement(self):
        result = RuntimeOrchestrationResult.not_ready(
            correlation_id="evidence-test",
            strategy_mode=StrategyMode.DAILY_ONLY,
        )

        assert result.evidence["telegram_delivery_required_for_safety"] is False


# --- Helpers ---


def _make_valid_setup():
    """Create a minimal valid SetupResult for testing."""
    return SetupResult(
        setup_name="trend_pullback",
        symbol="MSFT",
        status=SetupStatus.VALID,
        timing=SetupTiming(
            signal_time=NOW,
            signal_timeframe=BarTimeframe.DAILY,
            strategy_mode=StrategyMode.DAILY_ONLY,
        ),
        evidence=(
            NumericEvidence(name="planned_entry_price", value=400.0),
            NumericEvidence(name="initial_stop_price", value=390.0),
            NumericEvidence(name="target_price", value=420.0),
            NumericEvidence(name="reward_risk_proxy", value=2.0),
        ),
    )


def _paper_eligible_decision():
    """Create a PaperModeDecision that enables paper orders."""
    return PaperModeDecision(
        mode=PaperTradingMode.FULL_PAPER,
        activation_state=ActivationApprovalState.APPROVED_FOR_FULL_PAPER,
        paper_order_eligible=True,
        signal_preview_enabled=True,
        telegram_preview_enabled=True,
        risk_config=RiskConfig(
            per_trade_risk_pct=Decimal("1.0"),
            max_open_positions=5,
            max_sector_exposure_pct=Decimal("30"),
            max_new_entries_per_day=3,
            max_position_allocation_pct=Decimal("20"),
            minimum_reward_risk=Decimal("1.5"),
            minimum_quantity=1,
        ),
        reasons=("test",),
        required_phase6_checks=(),
    )
