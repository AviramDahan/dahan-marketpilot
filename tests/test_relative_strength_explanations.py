from marketpilot.setups.base import SetupRejectionReason
from marketpilot.setups.relative_strength import evaluate_relative_strength_leader
from test_relative_strength_detection import valid_input


def test_valid_explanation_mentions_relative_strength_evidence():
    result = evaluate_relative_strength_leader(valid_input())

    assert any("Relative Strength Leader is valid" in line for line in result.explanation)


def test_rejected_explanation_includes_reason_value():
    result = evaluate_relative_strength_leader(valid_input(symbol_returns=[0.0] * 70, spy_returns=[0.01] * 70))

    assert SetupRejectionReason.WEAK_SPY_RELATIVE_STRENGTH in result.rejection_reasons
    assert any("weak_spy_relative_strength" in line for line in result.explanation)
