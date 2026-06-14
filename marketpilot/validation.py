"""Validation, benchmark, and activation-gate contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Sequence

from marketpilot.backtest_reports import ValidationWindow, WindowStatus
from marketpilot.backtesting import BacktestRunStatus


class ValidationStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    UNAVAILABLE = "unavailable"


class ActivationApprovalState(str, Enum):
    UNVALIDATED = "unvalidated"
    VALIDATION_FAILED = "validation_failed"
    VALIDATION_PASSED = "validation_passed"
    APPROVED_FOR_SHADOW = "approved_for_shadow"
    APPROVED_FOR_LIMITED_PAPER = "approved_for_limited_paper"
    APPROVED_FOR_FULL_PAPER = "approved_for_full_paper"


@dataclass(frozen=True)
class ChronologicalValidationResult:
    status: ValidationStatus
    windows: tuple[ValidationWindow, ...]
    reasons: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return self.status is ValidationStatus.PASSED


@dataclass(frozen=True)
class SensitivityScenario:
    name: str
    assumptions: Mapping[str, object]
    comparison_fields: Mapping[str, float]


@dataclass(frozen=True)
class SensitivityAnalysis:
    status: ValidationStatus
    scenarios: tuple[SensitivityScenario, ...]
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class BenchmarkComparison:
    primary_symbol: str
    secondary_symbol: str
    status: ValidationStatus
    values: Mapping[str, float]
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class ValidationGateDecision:
    state: ActivationApprovalState
    passed_gates: tuple[str, ...]
    failed_gates: tuple[str, ...]

    @property
    def paper_eligible(self) -> bool:
        return self.state in {
            ActivationApprovalState.APPROVED_FOR_LIMITED_PAPER,
            ActivationApprovalState.APPROVED_FOR_FULL_PAPER,
        }


def run_chronological_validation(windows: Sequence[ValidationWindow]) -> ChronologicalValidationResult:
    reasons: list[str] = []
    if not windows:
        reasons.append("no_windows")
    unavailable = [window.name for window in windows if window.status is WindowStatus.UNAVAILABLE]
    reasons.extend(f"window_unavailable:{name}" for name in unavailable)
    status = ValidationStatus.UNAVAILABLE if reasons else ValidationStatus.PASSED
    return ChronologicalValidationResult(status, tuple(windows), tuple(reasons))


def run_sensitivity_analysis(scenarios: Sequence[SensitivityScenario]) -> SensitivityAnalysis:
    reasons: list[str] = []
    if not scenarios:
        reasons.append("no_scenarios")
    for scenario in scenarios:
        required = {"fee_per_order_usd", "slippage_bps", "fill_timing"}
        missing = required - set(scenario.assumptions)
        if missing:
            reasons.append(f"missing_assumptions:{scenario.name}:{','.join(sorted(missing))}")
    status = ValidationStatus.FAILED if reasons else ValidationStatus.PASSED
    return SensitivityAnalysis(status, tuple(scenarios), tuple(reasons))


def compare_benchmarks(
    *,
    strategy_return: float | None,
    spy_return: float | None,
    qqq_return: float | None = None,
) -> BenchmarkComparison:
    reasons: list[str] = []
    values: dict[str, float] = {}
    if strategy_return is None:
        reasons.append("strategy_return_unavailable")
    else:
        values["strategy_return"] = strategy_return
    if spy_return is None:
        reasons.append("primary_benchmark_spy_unavailable")
    else:
        values["spy_return"] = spy_return
    if qqq_return is None:
        reasons.append("secondary_benchmark_qqq_unavailable")
    else:
        values["qqq_return"] = qqq_return

    if "strategy_return" in values and "spy_return" in values:
        values["excess_vs_spy"] = values["strategy_return"] - values["spy_return"]
    status = ValidationStatus.UNAVAILABLE if reasons else ValidationStatus.PASSED
    return BenchmarkComparison("SPY", "QQQ", status, values, tuple(reasons))


def evaluate_activation_gates(
    *,
    run_status: BacktestRunStatus | str,
    no_lookahead_passed: bool,
    no_fake_results: bool,
    coverage_complete: bool,
    benchmark_available: bool,
    risk_checks_passed: bool,
    assumptions_present: bool,
    report_complete: bool,
    requested_state: ActivationApprovalState | str = ActivationApprovalState.VALIDATION_PASSED,
) -> ValidationGateDecision:
    status = run_status if isinstance(run_status, BacktestRunStatus) else BacktestRunStatus(str(run_status))
    requested = (
        requested_state
        if isinstance(requested_state, ActivationApprovalState)
        else ActivationApprovalState(str(requested_state))
    )
    gate_values = {
        "real_quantconnect_results": status is BacktestRunStatus.REAL_QUANTCONNECT,
        "no_lookahead": no_lookahead_passed,
        "no_fake_results": no_fake_results,
        "coverage_complete": coverage_complete,
        "benchmark_available": benchmark_available,
        "risk_checks_passed": risk_checks_passed,
        "assumptions_present": assumptions_present,
        "report_complete": report_complete,
    }
    passed = tuple(name for name, value in gate_values.items() if value)
    failed = tuple(name for name, value in gate_values.items() if not value)
    if failed:
        return ValidationGateDecision(ActivationApprovalState.VALIDATION_FAILED, passed, failed)

    if requested in {
        ActivationApprovalState.APPROVED_FOR_SHADOW,
        ActivationApprovalState.APPROVED_FOR_LIMITED_PAPER,
        ActivationApprovalState.APPROVED_FOR_FULL_PAPER,
    }:
        return ValidationGateDecision(requested, passed, failed)
    return ValidationGateDecision(ActivationApprovalState.VALIDATION_PASSED, passed, failed)
