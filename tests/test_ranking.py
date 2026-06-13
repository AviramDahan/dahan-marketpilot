from datetime import datetime, timezone
from pathlib import Path

from marketpilot.ranking import RankedCandidate, evaluate_combined_swing_readiness, rank_candidates
from marketpilot.scoring import CandidateClassification, GateStatus, MarketPilotScore, ScoreComponent
from marketpilot.setups.base import NumericEvidence, SetupTiming


def component(category, raw):
    return ScoreComponent(category=category, raw_score=raw, weight=10, weighted_score=raw / 10, evidence=(), passed=True)


def score(symbol="MSFT", setup="trend_pullback", total=80, confidence=70, risk=50, rs=50):
    return MarketPilotScore(
        symbol=symbol,
        setup_name=setup,
        total_score=total,
        classification=CandidateClassification.WATCH,
        confidence=confidence,
        component_scores=(
            component("risk_quality", risk),
            component("relative_strength", rs),
        ),
        evidence=(NumericEvidence("strategy_mode", "daily_only", "config", True),),
        hard_rejections=(),
        timing=SetupTiming(signal_time=datetime(2026, 6, 14, tzinfo=timezone.utc)),
        gate_statuses={"portfolio_gate": GateStatus.NOT_EVALUATED},
        explanation=(f"{setup} scored.",),
    )


def test_rank_candidates_emits_one_candidate_per_symbol_with_supporting_setups():
    ranked = rank_candidates(
        [
            score(setup="trend_pullback", total=80),
            score(setup="volume_breakout", total=75),
            score(symbol="AAPL", setup="relative_strength_leader", total=70),
        ]
    )

    msft = next(candidate for candidate in ranked if candidate.symbol == "MSFT")
    assert isinstance(msft, RankedCandidate)
    assert msft.primary_setup == "trend_pullback"
    assert msft.supporting_setups == ("volume_breakout",)
    assert len([candidate for candidate in ranked if candidate.symbol == "MSFT"]) == 1


def test_tie_breakers_use_confidence_then_risk_quality_then_relative_strength():
    ranked = rank_candidates(
        [
            score(setup="low_confidence", total=80, confidence=60, risk=90, rs=90),
            score(setup="high_confidence", total=80, confidence=70, risk=10, rs=10),
        ]
    )

    assert ranked[0].primary_setup == "high_confidence"

    ranked = rank_candidates(
        [
            score(setup="low_risk", total=80, confidence=70, risk=20, rs=90),
            score(setup="high_risk", total=80, confidence=70, risk=90, rs=10),
        ]
    )

    assert ranked[0].primary_setup == "high_risk"

    ranked = rank_candidates(
        [
            score(setup="low_rs", total=80, confidence=70, risk=90, rs=20),
            score(setup="high_rs", total=80, confidence=70, risk=90, rs=95),
        ]
    )

    assert ranked[0].primary_setup == "high_rs"


def test_combined_swing_remains_disabled_with_unmet_reasons():
    readiness = evaluate_combined_swing_readiness()

    assert readiness.enabled is False
    assert readiness.ready is False
    assert "independent_backtests" in readiness.unmet_reasons


def test_ranked_candidate_is_audit_only():
    candidate = rank_candidates([score()])[0]

    for name in ("entry", "stop", "target", "quantity", "order", "broker", "paper_order", "portfolio_state", "telegram_message", "backtest_result"):
        assert not hasattr(candidate, name)


def test_ranking_production_file_has_no_forbidden_behavior():
    text = (Path("marketpilot/ranking.py").read_text(encoding="utf-8"))

    for value in ("MarketOrder", "SetHoldings", "Liquidate", "send_telegram", "api_key", "password"):
        assert value not in text
