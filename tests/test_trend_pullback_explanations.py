from marketpilot.setups.base import SetupRejectionReason, SetupStatus
from marketpilot.setups.trend_pullback import evaluate_trend_pullback

from test_trend_pullback_detection import valid_input


def evidence_by_name(result):
    return {item.name: item for item in result.evidence}


def test_valid_result_includes_numeric_evidence_and_readable_explanation():
    result = evaluate_trend_pullback(valid_input())
    evidence = evidence_by_name(result)

    assert result.status is SetupStatus.VALID
    assert {"pullback_bars", "ema20_distance_pct", "ema50_distance_pct", "close_above_prior_high"}.issubset(evidence)
    assert {"recovery_volume_ratio", "atr_pct", "reward_risk_proxy", "rsi14", "macd"}.issubset(evidence)
    assert {"regime", "earnings_source_verified"}.issubset(evidence)
    assert result.explanation
    assert "completed daily-bar evidence" in result.explanation[0]


def test_rejected_result_includes_rejection_explanations_and_evidence():
    result = evaluate_trend_pullback(valid_input(closes=(103.0, 101.0, 99.8, 100.7, 100.9)))

    assert result.status is SetupStatus.REJECTED
    assert SetupRejectionReason.RECOVERY_NOT_CONFIRMED in result.rejection_reasons
    assert any("recovery_not_confirmed" in line for line in result.explanation)
    assert evidence_by_name(result)["close_above_prior_high"].passed is False


def test_trend_pullback_result_has_no_total_score_confidence_ranking_or_classification():
    result = evaluate_trend_pullback(valid_input())
    names = {item.name for item in result.evidence}

    assert "total_score" not in names
    assert "confidence" not in names
    assert "ranking" not in names
    assert not hasattr(result, "classification")

