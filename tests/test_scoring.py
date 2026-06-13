from datetime import datetime, timezone

import pytest

from marketpilot.scoring import CandidateClassification, GateStatus, load_scoring_config, score_setup_result
from marketpilot.setups.base import NumericEvidence, SetupRejectionReason, SetupResult, SetupStatus, SetupTiming


def setup_result(status=SetupStatus.VALID, reasons=()):
    return SetupResult(
        setup_name="relative_strength_leader",
        symbol="MSFT",
        status=status,
        timing=SetupTiming(signal_time=datetime(2026, 6, 14, tzinfo=timezone.utc)),
        evidence=(
            NumericEvidence("close_above_ema50", True, True, True),
            NumericEvidence("ema50_above_ema200", True, True, True),
            NumericEvidence("spy_rs20", 0.02, "> 0", True),
            NumericEvidence("spy_rs60", 0.02, "> 0", True),
            NumericEvidence("rsi14", 55.0, "supporting", True),
            NumericEvidence("breakout_close", 101.0, 100.0, True),
            NumericEvidence("volume_ratio", 1.8, 1.5, True),
            NumericEvidence("reward_risk_proxy", 2.5, 2.0, True),
            NumericEvidence("atr_pct", 4.0, 8.0, True),
            NumericEvidence("regime", "risk_on", "entry_allowed", True),
            NumericEvidence("strategy_mode", "daily_only", "config", True),
        ),
        rejection_reasons=tuple(reasons),
    )


def test_scoring_config_weights_total_100_and_disabled_behaviors():
    config = load_scoring_config()

    assert sum(config["weights"].values()) == 100
    assert config["weights"]["trend_structure"] == 25
    assert config["weights"]["relative_strength"] == 20
    assert config["weights"]["momentum"] == 15
    assert config["weights"]["setup_quality"] == 20
    assert config["weights"]["volume_confirmation"] == 10
    assert config["weights"]["risk_quality"] == 10
    assert config["disabled_behaviors"]["create_orders"] is False
    assert config["gates"]["sector_fit"] == "not_evaluated"


def test_scoring_config_rejects_weights_not_totaling_100(tmp_path):
    path = tmp_path / "scoring.yaml"
    path.write_text(
        """
scoring:
  paper_trading_only: true
  weights:
    trend_structure: 1
    relative_strength: 1
    momentum: 1
    setup_quality: 1
    volume_confirmation: 1
    risk_quality: 1
  disabled_behaviors:
    create_orders: false
    portfolio_sizing: false
    backtest_result_creation: false
    telegram_delivery: false
    paper_deployment: false
    live_deployment: false
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="total 100"):
        load_scoring_config(path)


def test_score_setup_result_preserves_components_and_defaults_to_watch_without_later_gates():
    score = score_setup_result(setup_result())

    assert score.total_score > 75
    assert score.classification is CandidateClassification.WATCH
    assert score.gate_statuses["portfolio_gate"] is GateStatus.NOT_EVALUATED
    assert score.gate_statuses["activation_gate"] is GateStatus.NOT_EVALUATED
    assert len(score.component_scores) == 6
    assert score.confidence != score.total_score


def test_buy_candidate_requires_explicit_later_gates():
    score = score_setup_result(
        setup_result(),
        gate_statuses={
            "sector_fit": GateStatus.PASSED,
            "portfolio_gate": GateStatus.PASSED,
            "activation_gate": GateStatus.PASSED,
        },
    )

    assert score.classification is CandidateClassification.BUY_CANDIDATE


def test_hard_rejection_overrides_score():
    score = score_setup_result(setup_result(status=SetupStatus.REJECTED, reasons=(SetupRejectionReason.RISK_OFF,)))

    assert score.classification is CandidateClassification.REJECTED
    assert SetupRejectionReason.RISK_OFF in score.hard_rejections


def test_missing_required_component_fails_closed():
    sparse = SetupResult(
        setup_name="empty",
        symbol="MSFT",
        status=SetupStatus.VALID,
        timing=SetupTiming(signal_time=datetime(2026, 6, 14, tzinfo=timezone.utc)),
        evidence=(NumericEvidence("regime", "risk_on", "entry_allowed", True),),
    )

    score = score_setup_result(sparse)

    assert score.classification is CandidateClassification.REJECTED
    assert any("Required scoring data failed" in line for line in score.explanation)


def test_sector_fit_not_evaluated_is_not_standalone_hard_rejection():
    score = score_setup_result(
        setup_result(),
        gate_statuses={"sector_fit": GateStatus.NOT_EVALUATED, "portfolio_gate": GateStatus.PASSED, "activation_gate": GateStatus.PASSED},
    )

    assert score.gate_statuses["sector_fit"] is GateStatus.NOT_EVALUATED
    assert score.classification is CandidateClassification.BUY_CANDIDATE


def test_scoring_output_is_audit_only():
    score = score_setup_result(setup_result())

    assert not hasattr(score, "order")
    assert not hasattr(score, "quantity")
    assert not hasattr(score, "entry")
    assert not hasattr(score, "stop")
    assert not hasattr(score, "target")
