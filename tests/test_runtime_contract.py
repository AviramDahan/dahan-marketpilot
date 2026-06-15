from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from marketpilot.order_lifecycle import OrderIntent
from marketpilot.ranking import RankedCandidate
from marketpilot.risk import RiskDecision
from marketpilot.runtime_orchestrator import (
    RuntimeAuthority,
    RuntimeOrchestrationInput,
    RuntimeOrchestrationResult,
    RuntimeOrchestrationStatus,
    RuntimeSkippedReason,
    create_order_intent,
)
from marketpilot.scoring import CandidateClassification
from marketpilot.setups.base import NumericEvidence, SetupTiming
from marketpilot.timeframes import BarTimeframe, StrategyMode


SIGNAL_TIME = datetime(2026, 6, 15, 20, 0, tzinfo=timezone.utc)


def ranked_candidate() -> RankedCandidate:
    return RankedCandidate(
        symbol="MSFT",
        primary_setup="trend_pullback",
        supporting_setups=("relative_strength_leader",),
        total_score=82.0,
        component_scores=(),
        classification=CandidateClassification.WATCH,
        confidence=76.0,
        evidence=(NumericEvidence("strategy_mode", "daily_only", "config", True),),
        hard_rejections=(),
        timing=SetupTiming(
            signal_time=SIGNAL_TIME,
            strategy_mode=StrategyMode.DAILY_ONLY,
            signal_timeframe=BarTimeframe.DAILY,
            bar_end=SIGNAL_TIME,
        ),
        explanation=("Candidate is audit evidence only.",),
    )


def risk_decision() -> RiskDecision:
    return RiskDecision(
        accepted=True,
        symbol="MSFT",
        primary_setup="trend_pullback",
        quantity=5,
        risk_amount=Decimal("500"),
        allocation_amount=Decimal("1500"),
        rejection_reasons=(),
        evidence={"portfolio_epoch": "qc-paper-epoch-1", "source_authority": "quantconnect"},
    )


def test_runtime_status_and_skipped_reason_values_are_stable_dashboard_strings():
    assert [status.value for status in RuntimeOrchestrationStatus] == [
        "not_configured",
        "not_ready",
        "blocked",
        "shadow_only",
        "paper_intent_ready",
    ]
    assert RuntimeSkippedReason.MISSING_RUNTIME_INPUT.value == "missing_runtime_input"
    assert RuntimeSkippedReason.QUANTCONNECT_AUTHORITY_MISSING.value == "quantconnect_authority_missing"
    assert RuntimeSkippedReason.RECONCILIATION_BLOCKED.value == "reconciliation_blocked"
    assert RuntimeSkippedReason.PAPER_MODE_NOT_ELIGIBLE.value == "paper_mode_not_eligible"


def test_default_runtime_result_is_fail_closed_and_side_effect_free():
    result = RuntimeOrchestrationResult.not_configured(
        correlation_id="run-001",
        strategy_mode=StrategyMode.DAILY_ONLY,
        skipped_reasons=(RuntimeSkippedReason.MISSING_RUNTIME_INPUT,),
    )

    assert result.status is RuntimeOrchestrationStatus.NOT_CONFIGURED
    assert result.correlation_id == "run-001"
    assert result.strategy_mode is StrategyMode.DAILY_ONLY
    assert result.source_authority is RuntimeAuthority.QUANTCONNECT
    assert result.skipped_reasons == (RuntimeSkippedReason.MISSING_RUNTIME_INPUT,)
    assert result.ranked_candidates == ()
    assert result.risk_decisions == ()
    assert result.order_intents == ()
    assert result.notification_events == ()
    assert result.executed_quantconnect_order_ids == ()
    assert result.quantconnect_fill_ids == ()
    assert result.quantconnect_backtest_id is None
    assert result.quantconnect_deployment_id is None
    assert result.authoritative_portfolio_state is None
    assert result.evidence["paper_trading_only"] is True
    assert result.evidence["executes_orders"] is False
    assert result.evidence["creates_backtest_results"] is False
    assert result.evidence["telegram_delivery_required_for_safety"] is False

    with pytest.raises(FrozenInstanceError):
        result.status = RuntimeOrchestrationStatus.PAPER_INTENT_READY


def test_runtime_input_preserves_strategy_mode_and_completed_bar_timing():
    runtime_input = RuntimeOrchestrationInput(
        correlation_id="run-002",
        strategy_mode=StrategyMode.DAILY_FILTER_4H_SETUP,
        setup_results=(),
        source_authority=RuntimeAuthority.QUANTCONNECT,
        timing=SetupTiming(
            signal_time=SIGNAL_TIME,
            timing_mode="completed_four_hour_bar",
            uses_completed_daily_bar=False,
            strategy_mode=StrategyMode.DAILY_FILTER_4H_SETUP,
            signal_timeframe=BarTimeframe.FOUR_HOUR,
            bar_start=datetime(2026, 6, 15, 16, 0, tzinfo=timezone.utc),
            bar_end=SIGNAL_TIME,
            source_resolution="four_hour",
            later_valid_execution_required=True,
        ),
    )

    assert runtime_input.strategy_mode is StrategyMode.DAILY_FILTER_4H_SETUP
    assert runtime_input.timing.signal_timeframe is BarTimeframe.FOUR_HOUR
    assert runtime_input.timing.intrabar_valid is False
    assert runtime_input.timing.later_valid_execution_required is True


def test_shadow_and_paper_intent_results_mirror_evidence_without_claiming_execution():
    candidate = ranked_candidate()
    risk = risk_decision()
    intent = create_order_intent(
        candidate=candidate,
        risk_decision=risk,
        strategy_mode=StrategyMode.DAILY_ONLY,
        entry_price=Decimal("300"),
        stop_price=Decimal("280"),
        target_price=Decimal("340"),
        portfolio_epoch="qc-paper-epoch-1",
    )

    shadow = RuntimeOrchestrationResult.shadow_only(
        correlation_id="run-003",
        strategy_mode=StrategyMode.DAILY_ONLY,
        ranked_candidates=(candidate,),
        risk_decisions=(risk,),
        evidence={"reconciliation_status": "matched"},
    )
    ready = RuntimeOrchestrationResult.paper_intent_ready(
        correlation_id="run-004",
        strategy_mode=StrategyMode.DAILY_ONLY,
        ranked_candidates=(candidate,),
        risk_decisions=(risk,),
        order_intents=(intent,),
        evidence={"paper_mode": "limited_paper"},
    )

    assert shadow.status is RuntimeOrchestrationStatus.SHADOW_ONLY
    assert shadow.order_intents == ()
    assert ready.status is RuntimeOrchestrationStatus.PAPER_INTENT_READY
    assert ready.order_intents == (intent,)
    assert isinstance(ready.order_intents[0], OrderIntent)
    assert ready.executed_quantconnect_order_ids == ()
    assert ready.quantconnect_fill_ids == ()
    assert ready.authoritative_portfolio_state is None
    assert ready.evidence["executes_orders"] is False
    assert ready.evidence["source_authority"] == "quantconnect"
    assert ready.evidence["strategy_mode"] == "daily_only"


def test_runtime_result_rejects_fake_execution_authority_without_quantconnect_state():
    with pytest.raises(ValueError, match="executed QuantConnect order ids"):
        RuntimeOrchestrationResult(
            status=RuntimeOrchestrationStatus.PAPER_INTENT_READY,
            correlation_id="run-005",
            strategy_mode=StrategyMode.DAILY_ONLY,
            source_authority=RuntimeAuthority.QUANTCONNECT,
            executed_quantconnect_order_ids=("fake-order-1",),
        )

    with pytest.raises(ValueError, match="portfolio state"):
        RuntimeOrchestrationResult(
            status=RuntimeOrchestrationStatus.PAPER_INTENT_READY,
            correlation_id="run-006",
            strategy_mode=StrategyMode.DAILY_ONLY,
            source_authority=RuntimeAuthority.LOCAL_MIRROR,
            authoritative_portfolio_state={"cash": "100000"},
        )
