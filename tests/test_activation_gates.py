from marketpilot.backtesting import BacktestRunStatus
from marketpilot.validation import ActivationApprovalState, evaluate_activation_gates


def test_activation_gates_block_paper_by_default_for_not_run_results():
    decision = evaluate_activation_gates(
        run_status=BacktestRunStatus.NOT_RUN,
        no_lookahead_passed=True,
        no_fake_results=True,
        coverage_complete=True,
        benchmark_available=True,
        risk_checks_passed=True,
        assumptions_present=True,
        report_complete=True,
    )

    assert decision.state is ActivationApprovalState.VALIDATION_FAILED
    assert decision.paper_eligible is False
    assert "real_quantconnect_results" in decision.failed_gates


def test_activation_gates_can_validate_without_paper_approval():
    decision = evaluate_activation_gates(
        run_status=BacktestRunStatus.REAL_QUANTCONNECT,
        no_lookahead_passed=True,
        no_fake_results=True,
        coverage_complete=True,
        benchmark_available=True,
        risk_checks_passed=True,
        assumptions_present=True,
        report_complete=True,
    )

    assert decision.state is ActivationApprovalState.VALIDATION_PASSED
    assert decision.paper_eligible is False


def test_activation_gates_require_explicit_paper_state_request():
    decision = evaluate_activation_gates(
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

    assert decision.state is ActivationApprovalState.APPROVED_FOR_LIMITED_PAPER
    assert decision.paper_eligible is True
