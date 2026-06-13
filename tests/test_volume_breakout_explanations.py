from marketpilot.setups.base import SetupRejectionReason, SetupStatus
from marketpilot.setups.volume_breakout import evaluate_volume_breakout

from test_volume_breakout_detection import valid_input


def evidence_by_name(result):
    return {item.name: item for item in result.evidence}


def test_valid_result_includes_breakout_evidence_components():
    result = evaluate_volume_breakout(valid_input())
    evidence = evidence_by_name(result)

    assert result.status is SetupStatus.VALID
    assert {
        "resistance_lookback_bars",
        "prior_resistance",
        "breakout_buffer_pct",
        "buffered_resistance",
        "breakout_close",
        "volume_ratio",
        "ema20_extension_pct",
        "atr_pct",
        "average_dollar_volume",
        "reward_risk_proxy",
        "regime",
    }.issubset(evidence)
    assert result.explanation
    assert "completed daily-bar breakout evidence" in result.explanation[0]


def test_rejected_result_includes_rejection_explanations_and_failed_evidence():
    result = evaluate_volume_breakout(valid_input(bars=()))

    assert result.status is SetupStatus.REJECTED
    assert SetupRejectionReason.INCOMPLETE_COMPLETED_BAR_DATA in result.rejection_reasons
    assert any("incomplete_completed_bar_data" in line for line in result.explanation)
    assert evidence_by_name(result)["resistance_lookback_bars"].passed is False


def test_volume_breakout_result_has_no_score_confidence_ranking_or_classification_evidence():
    result = evaluate_volume_breakout(valid_input())
    names = {item.name for item in result.evidence}

    assert "total_score" not in names
    assert "confidence" not in names
    assert "ranking" not in names
    assert "classification" not in names
    assert "BUY" not in names
    assert "WATCH" not in names
    assert "AVOID" not in names
    assert not hasattr(result, "total_score")
    assert not hasattr(result, "confidence")
    assert not hasattr(result, "ranking")
    assert not hasattr(result, "classification")
