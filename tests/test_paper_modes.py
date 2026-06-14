from decimal import Decimal

import pytest

from marketpilot.backtesting import BacktestRunStatus
from marketpilot.paper_modes import (
    PaperTradingMode,
    evaluate_paper_mode,
    load_paper_mode_config,
)
from marketpilot.validation import ActivationApprovalState, evaluate_activation_gates


def _gate_decision(state: ActivationApprovalState):
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


def test_default_inactive_mode_cannot_submit_paper_orders():
    decision = evaluate_paper_mode(
        validation_decision=evaluate_activation_gates(
            run_status=BacktestRunStatus.NOT_RUN,
            no_lookahead_passed=True,
            no_fake_results=True,
            coverage_complete=True,
            benchmark_available=True,
            risk_checks_passed=True,
            assumptions_present=True,
            report_complete=True,
        )
    )

    assert decision.mode is PaperTradingMode.INACTIVE
    assert decision.paper_order_eligible is False
    assert decision.signal_preview_enabled is False
    assert decision.telegram_preview_enabled is False
    assert "real_quantconnect_results" in decision.reasons


def test_validation_passed_is_not_paper_order_eligible():
    decision = evaluate_paper_mode(
        validation_decision=_gate_decision(ActivationApprovalState.VALIDATION_PASSED)
    )

    assert decision.mode is PaperTradingMode.INACTIVE
    assert decision.paper_order_eligible is False
    assert decision.signal_preview_enabled is False
    assert "explicit_paper_approval_required" in decision.reasons


def test_shadow_allows_previews_only():
    decision = evaluate_paper_mode(
        validation_decision=_gate_decision(ActivationApprovalState.APPROVED_FOR_SHADOW)
    )

    assert decision.mode is PaperTradingMode.SHADOW
    assert decision.paper_order_eligible is False
    assert decision.signal_preview_enabled is True
    assert decision.telegram_preview_enabled is True


def test_limited_and_full_paper_are_the_only_order_eligible_states():
    limited = evaluate_paper_mode(
        validation_decision=_gate_decision(ActivationApprovalState.APPROVED_FOR_LIMITED_PAPER)
    )
    full = evaluate_paper_mode(
        validation_decision=_gate_decision(ActivationApprovalState.APPROVED_FOR_FULL_PAPER)
    )

    assert limited.mode is PaperTradingMode.LIMITED_PAPER
    assert limited.paper_order_eligible is True
    assert limited.risk_config.per_trade_risk_pct == Decimal("0.5")
    assert full.mode is PaperTradingMode.FULL_PAPER
    assert full.paper_order_eligible is True
    assert full.risk_config.per_trade_risk_pct == Decimal("1.0")


def test_limited_paper_caps_are_stricter_than_phase_6_and_preserve_checks():
    config = load_paper_mode_config()

    assert config.limited_risk_config.per_trade_risk_pct == Decimal("0.5")
    assert config.limited_risk_config.max_open_positions == 3
    assert config.limited_risk_config.max_new_entries_per_day == 1
    assert config.full_risk_config.per_trade_risk_pct == Decimal("1.0")
    assert config.full_risk_config.max_open_positions == 10
    assert config.full_risk_config.max_new_entries_per_day == 3
    assert config.require_phase6_allocation_check is True
    assert config.require_phase6_sector_check is True
    assert config.require_phase6_reward_risk_check is True
    assert config.require_phase6_stop_check is True
    assert config.require_phase6_target_check is True


@pytest.mark.parametrize(
    ("run_status", "expected_reason"),
    [
        (BacktestRunStatus.NOT_RUN, "real_quantconnect_results"),
        (BacktestRunStatus.FIXTURE, "real_quantconnect_results"),
        (BacktestRunStatus.UNAVAILABLE, "real_quantconnect_results"),
    ],
)
def test_stale_unavailable_fixture_or_not_run_evidence_fails_closed(run_status, expected_reason):
    decision = evaluate_paper_mode(
        validation_decision=evaluate_activation_gates(
            run_status=run_status,
            no_lookahead_passed=True,
            no_fake_results=True,
            coverage_complete=True,
            benchmark_available=True,
            risk_checks_passed=True,
            assumptions_present=True,
            report_complete=True,
            requested_state=ActivationApprovalState.APPROVED_FOR_FULL_PAPER,
        )
    )

    assert decision.mode is PaperTradingMode.INACTIVE
    assert decision.paper_order_eligible is False
    assert expected_reason in decision.reasons
