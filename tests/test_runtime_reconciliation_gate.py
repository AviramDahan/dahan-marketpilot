from datetime import datetime, timezone
from decimal import Decimal

from marketpilot.backtesting import BacktestRunStatus
from marketpilot.order_lifecycle import OrderLifecycleEvent, OrderLifecycleState
from marketpilot.quantconnect_paper import (
    QuantConnectAlgorithmStatus,
    QuantConnectDeploymentStatus,
    QuantConnectHolding,
    QuantConnectPaperFill,
    QuantConnectPaperOrder,
    QuantConnectPaperPerformance,
    QuantConnectPaperSnapshot,
)
from marketpilot.reconciliation import ReconciliationMismatchType
from marketpilot.risk import PortfolioSnapshot
from marketpilot.runtime_orchestrator import (
    RuntimeOrchestrationInput,
    RuntimeOrchestrationStatus,
    RuntimeSkippedReason,
    run_runtime_pipeline,
)
from marketpilot.setups.base import NumericEvidence, SetupResult, SetupStatus, SetupTiming
from marketpilot.timeframes import StrategyMode
from marketpilot.validation import ActivationApprovalState, evaluate_activation_gates


SIGNAL_TIME = datetime(2026, 6, 15, 20, 0, tzinfo=timezone.utc)


def _setup_result() -> SetupResult:
    return SetupResult(
        setup_name="relative_strength_leader",
        symbol="MSFT",
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
    )


def _validation_decision():
    return evaluate_activation_gates(
        run_status=BacktestRunStatus.REAL_QUANTCONNECT,
        no_lookahead_passed=True,
        no_fake_results=True,
        coverage_complete=True,
        benchmark_available=True,
        risk_checks_passed=True,
        assumptions_present=True,
        report_complete=True,
        requested_state=ActivationApprovalState.APPROVED_FOR_LIMITED_PAPER,
    )


def _portfolio() -> PortfolioSnapshot:
    return PortfolioSnapshot(
        simulated_equity=Decimal("100000"),
        available_cash=Decimal("100000"),
        sector_exposure={"Technology": Decimal("0")},
        portfolio_epoch="qc-paper-epoch-1",
    )


def _snapshot_with_mismatch() -> QuantConnectPaperSnapshot:
    return QuantConnectPaperSnapshot(
        fixture_label="deterministic-test-fixture",
        captured_at=datetime(2026, 6, 15, 20, 5, tzinfo=timezone.utc),
        cash=Decimal("98500"),
        portfolio_equity=Decimal("101250"),
        holdings=(
            QuantConnectHolding(symbol="MSFT", quantity=10, average_price=Decimal("420"), market_price=Decimal("425")),
        ),
        orders=(
            QuantConnectPaperOrder(
                quantconnect_order_id="qc-order-1",
                symbol="MSFT",
                status="filled",
                quantity=10,
                submitted_at=datetime(2026, 6, 15, 20, 1, tzinfo=timezone.utc),
                idempotency_key="intent-msft",
            ),
        ),
        fills=(
            QuantConnectPaperFill(
                quantconnect_order_id="qc-order-1",
                symbol="MSFT",
                quantity=10,
                fill_price=Decimal("421.50"),
                filled_at=datetime(2026, 6, 15, 20, 2, tzinfo=timezone.utc),
            ),
        ),
        deployment_status=QuantConnectDeploymentStatus.RUNNING,
        algorithm_status=QuantConnectAlgorithmStatus.RUNNING,
        performance=QuantConnectPaperPerformance(total_orders=1, total_fills=1, unrealized_profit=Decimal("35")),
    )


def test_quantconnect_unavailable_blocks_new_entries_but_preserves_exit_obligations():
    result = run_runtime_pipeline(
        RuntimeOrchestrationInput(
            correlation_id="runtime-qc-unavailable",
            strategy_mode=StrategyMode.DAILY_ONLY,
            setup_results=(_setup_result(),),
            validation_decision=_validation_decision(),
            portfolio_snapshot=_portfolio(),
            existing_exit_obligations=({"symbol": "MSFT", "obligation": "protective_stop"},),
        )
    )

    assert result.status is RuntimeOrchestrationStatus.BLOCKED
    assert result.order_intents == ()
    assert RuntimeSkippedReason.QUANTCONNECT_AUTHORITY_MISSING in result.skipped_reasons
    assert result.evidence["reconciliation_status"] == "quantconnect_unavailable"
    assert result.evidence["block_new_entries"] is True
    assert result.evidence["preserve_exits"] is True
    assert result.evidence["existing_exit_obligations"] == ({"symbol": "MSFT", "obligation": "protective_stop"},)
    assert result.notification_events[0].event_type == "system"
    assert result.notification_events[0].payload["delivery_required_for_safety"] is False


def test_reconciliation_mismatch_blocks_entries_and_emits_non_authoritative_system_event():
    local_lifecycle = (
        OrderLifecycleEvent(
            idempotency_key="intent-msft",
            previous_state=OrderLifecycleState.SUBMITTED,
            next_state=OrderLifecycleState.SUBMITTED,
            timestamp=datetime(2026, 6, 15, 20, 1, tzinfo=timezone.utc),
            reason="submitted locally before authoritative fill",
            payload={"quantconnect_order_id": "local-stale-order"},
        ),
    )

    result = run_runtime_pipeline(
        RuntimeOrchestrationInput(
            correlation_id="runtime-reconciliation-mismatch",
            strategy_mode=StrategyMode.DAILY_ONLY,
            setup_results=(_setup_result(),),
            validation_decision=_validation_decision(),
            quantconnect_snapshot=_snapshot_with_mismatch(),
            portfolio_snapshot=_portfolio(),
            local_lifecycle_events=local_lifecycle,
            existing_exit_obligations=({"symbol": "MSFT", "obligation": "target_or_stop"},),
        )
    )

    assert result.status is RuntimeOrchestrationStatus.BLOCKED
    assert result.order_intents == ()
    assert RuntimeSkippedReason.RECONCILIATION_BLOCKED in result.skipped_reasons
    assert result.evidence["reconciliation_status"] == "blocked"
    assert result.evidence["block_new_entries"] is True
    assert result.evidence["preserve_exits"] is True
    assert "order_id" in result.evidence["reconciliation_mismatch_types"]
    assert ReconciliationMismatchType.ORDER_ID.value in result.evidence["reconciliation_mismatch_types"]
    assert result.notification_events[0].event_type == "system"
    assert result.notification_events[0].severity == "high"
    assert result.notification_events[0].payload["controls_safety_logic"] is False
    assert result.notification_events[0].payload["delivery_required_for_safety"] is False


def test_reconciliation_gate_does_not_turn_quantconnect_events_into_local_authority():
    result = run_runtime_pipeline(
        RuntimeOrchestrationInput(
            correlation_id="runtime-authority-labels",
            strategy_mode=StrategyMode.DAILY_ONLY,
            setup_results=(_setup_result(),),
            validation_decision=_validation_decision(),
            quantconnect_snapshot=_snapshot_with_mismatch(),
            portfolio_snapshot=_portfolio(),
            local_audit_records=({"event_type": "paper_order_submitted"},),
        )
    )

    assert result.status is RuntimeOrchestrationStatus.BLOCKED
    assert result.source_authority.value == "quantconnect"
    assert result.authoritative_portfolio_state is None
    assert result.executed_quantconnect_order_ids == ()
    assert result.quantconnect_fill_ids == ()
    assert result.evidence["authoritative_portfolio_source"] == "quantconnect"
    assert "local_audit" in result.evidence["reconciliation_mismatch_types"]
