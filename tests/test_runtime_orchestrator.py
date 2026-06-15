from datetime import datetime, timezone
from decimal import Decimal

from marketpilot.backtesting import BacktestRunStatus
from marketpilot.notification_events import NotificationDomainEvent
from marketpilot.paper_modes import PaperTradingMode
from marketpilot.quantconnect_paper import (
    QuantConnectAlgorithmStatus,
    QuantConnectDeploymentStatus,
    QuantConnectPaperPerformance,
    QuantConnectPaperSnapshot,
)
from marketpilot.risk import PortfolioSnapshot, RiskRejectionReason
from marketpilot.runtime_orchestrator import (
    RuntimeOrchestrationInput,
    RuntimeOrchestrationStatus,
    RuntimeSkippedReason,
    run_runtime_pipeline,
)
from marketpilot.scoring import CandidateClassification
from marketpilot.setups.base import NumericEvidence, SetupResult, SetupStatus, SetupTiming
from marketpilot.timeframes import StrategyMode
from marketpilot.validation import ActivationApprovalState, evaluate_activation_gates


SIGNAL_TIME = datetime(2026, 6, 15, 20, 0, tzinfo=timezone.utc)


def _setup_result(symbol: str = "MSFT") -> SetupResult:
    return SetupResult(
        setup_name="relative_strength_leader",
        symbol=symbol,
        status=SetupStatus.VALID,
        timing=SetupTiming(signal_time=SIGNAL_TIME, strategy_mode=StrategyMode.DAILY_ONLY, bar_end=SIGNAL_TIME),
        evidence=(
            NumericEvidence("close_above_ema50", True, True, True),
            NumericEvidence("ema50_above_ema200", True, True, True),
            NumericEvidence("spy_rs20", 0.04, "> 0", True),
            NumericEvidence("spy_rs60", 0.06, "> 0", True),
            NumericEvidence("rsi14", 55.0, "supporting", True),
            NumericEvidence("breakout_close", 100.0, 99.0, True),
            NumericEvidence("volume_ratio", 1.8, 1.5, True),
            NumericEvidence("reward_risk_proxy", 2.5, 2.0, True),
            NumericEvidence("atr_pct", 4.0, 8.0, True),
            NumericEvidence("regime", "risk_on", "entry_allowed", True),
            NumericEvidence("strategy_mode", "daily_only", "config", True),
            NumericEvidence("planned_entry_price", 100.0, "later_valid_price", True),
            NumericEvidence("initial_stop_price", 95.0, "risk_model", True),
            NumericEvidence("target_price", 112.5, "risk_model", True),
            NumericEvidence("sector", "Technology", "classification_source", True),
        ),
        explanation=("Deterministic valid setup fixture.",),
    )


def _validation_decision(state: ActivationApprovalState = ActivationApprovalState.APPROVED_FOR_LIMITED_PAPER):
    return evaluate_activation_gates(
        run_status=BacktestRunStatus.REAL_QUANTCONNECT,
        no_lookahead_passed=True,
        no_fake_results=True,
        coverage_complete=True,
        benchmark_available=True,
        risk_checks_passed=True,
        assumptions_present=True,
        report_complete=True,
        requested_state=state,
    )


def _quantconnect_snapshot() -> QuantConnectPaperSnapshot:
    return QuantConnectPaperSnapshot(
        fixture_label="deterministic-test-fixture",
        captured_at=datetime(2026, 6, 15, 20, 5, tzinfo=timezone.utc),
        cash=Decimal("100000"),
        portfolio_equity=Decimal("100000"),
        holdings=(),
        orders=(),
        fills=(),
        deployment_status=QuantConnectDeploymentStatus.RUNNING,
        algorithm_status=QuantConnectAlgorithmStatus.RUNNING,
        performance=QuantConnectPaperPerformance(
            total_orders=0,
            total_fills=0,
            unrealized_profit=Decimal("0"),
        ),
    )


def _portfolio(open_positions: int = 0, new_entries_today: int = 0) -> PortfolioSnapshot:
    return PortfolioSnapshot(
        simulated_equity=Decimal("100000"),
        available_cash=Decimal("100000"),
        open_positions=open_positions,
        sector_exposure={"Technology": Decimal("0")},
        new_entries_today=new_entries_today,
        portfolio_epoch="qc-paper-epoch-1",
    )


def test_valid_setup_can_be_scored_and_ranked_without_becoming_an_order_instruction():
    result = run_runtime_pipeline(
        RuntimeOrchestrationInput(
            correlation_id="runtime-score-only",
            strategy_mode=StrategyMode.DAILY_ONLY,
            setup_results=(_setup_result(),),
        )
    )

    assert result.status is RuntimeOrchestrationStatus.SHADOW_ONLY
    assert result.ranked_candidates[0].symbol == "MSFT"
    assert result.ranked_candidates[0].classification is CandidateClassification.WATCH
    assert result.risk_decisions == ()
    assert result.order_intents == ()
    assert RuntimeSkippedReason.QUANTCONNECT_AUTHORITY_MISSING in result.skipped_reasons
    assert result.evidence["classification_is_instruction"] is False
    assert result.evidence["executes_orders"] is False


def test_all_gates_passing_produces_order_intent_evidence_without_submitting_order():
    result = run_runtime_pipeline(
        RuntimeOrchestrationInput(
            correlation_id="runtime-paper-ready",
            strategy_mode=StrategyMode.DAILY_ONLY,
            setup_results=(_setup_result(),),
            validation_decision=_validation_decision(),
            quantconnect_snapshot=_quantconnect_snapshot(),
            portfolio_snapshot=_portfolio(),
        )
    )

    assert result.status is RuntimeOrchestrationStatus.PAPER_INTENT_READY
    assert result.ranked_candidates[0].classification is CandidateClassification.BUY_CANDIDATE
    assert result.risk_decisions[0].accepted is True
    assert len(result.order_intents) == 1
    assert result.order_intents[0].idempotency_key.startswith("order-intent-")
    assert result.order_intents[0].symbol == "MSFT"
    assert result.order_intents[0].portfolio_epoch == "qc-paper-epoch-1"
    assert result.executed_quantconnect_order_ids == ()
    assert result.quantconnect_fill_ids == ()
    assert result.evidence["paper_mode"] == PaperTradingMode.LIMITED_PAPER.value
    assert result.evidence["source_authority"] == "quantconnect"
    assert result.evidence["authoritative_portfolio_source"] == "quantconnect"
    assert result.evidence["executes_orders"] is False
    assert any(event.event_type == "sizing_decision" for event in result.notification_events)
    assert any(event.event_type == "order_intent" for event in result.notification_events)


def test_risk_rejection_emits_risk_event_and_no_order_intent():
    result = run_runtime_pipeline(
        RuntimeOrchestrationInput(
            correlation_id="runtime-risk-rejected",
            strategy_mode=StrategyMode.DAILY_ONLY,
            setup_results=(_setup_result(),),
            validation_decision=_validation_decision(),
            quantconnect_snapshot=_quantconnect_snapshot(),
            portfolio_snapshot=_portfolio(open_positions=3),
        )
    )

    assert result.status is RuntimeOrchestrationStatus.BLOCKED
    assert result.order_intents == ()
    assert result.risk_decisions[0].accepted is False
    assert RiskRejectionReason.MAX_OPEN_POSITIONS in result.risk_decisions[0].rejection_reasons
    assert RuntimeSkippedReason.RISK_REJECTED in result.skipped_reasons
    risk_events = [event for event in result.notification_events if event.event_type == "risk_rejection"]
    assert len(risk_events) == 1
    assert risk_events[0].severity == "warning"
    assert risk_events[0].payload["controls_safety_logic"] is False


def test_shadow_paper_mode_emits_evidence_but_no_order_intent():
    result = run_runtime_pipeline(
        RuntimeOrchestrationInput(
            correlation_id="runtime-shadow-only",
            strategy_mode=StrategyMode.DAILY_ONLY,
            setup_results=(_setup_result(),),
            validation_decision=_validation_decision(ActivationApprovalState.APPROVED_FOR_SHADOW),
            quantconnect_snapshot=_quantconnect_snapshot(),
            portfolio_snapshot=_portfolio(),
        )
    )

    assert result.status is RuntimeOrchestrationStatus.SHADOW_ONLY
    assert result.ranked_candidates
    assert result.risk_decisions == ()
    assert result.order_intents == ()
    assert RuntimeSkippedReason.PAPER_MODE_NOT_ELIGIBLE in result.skipped_reasons
    assert result.evidence["paper_mode"] == PaperTradingMode.SHADOW.value
    assert result.evidence["paper_order_eligible"] is False


def test_runtime_output_preserves_correlation_ids_and_non_authoritative_notification_delivery():
    result = run_runtime_pipeline(
        RuntimeOrchestrationInput(
            correlation_id="runtime-correlation",
            strategy_mode=StrategyMode.DAILY_ONLY,
            setup_results=(_setup_result(),),
            validation_decision=_validation_decision(),
            quantconnect_snapshot=_quantconnect_snapshot(),
            portfolio_snapshot=_portfolio(),
        )
    )

    assert result.correlation_id == "runtime-correlation"
    assert result.evidence["correlation_id"] == "runtime-correlation"
    assert result.evidence["telegram_delivery_required_for_safety"] is False
    assert all(isinstance(event, NotificationDomainEvent) for event in result.notification_events)
    assert {event.correlation_id for event in result.notification_events} == {"runtime-correlation"}
    assert all(event.payload["delivery_required_for_safety"] is False for event in result.notification_events)
