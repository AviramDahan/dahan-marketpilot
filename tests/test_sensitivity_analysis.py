from marketpilot.validation import SensitivityScenario, ValidationStatus, run_sensitivity_analysis


def test_sensitivity_analysis_requires_fee_slippage_and_timing():
    scenario = SensitivityScenario(
        name="conservative",
        assumptions={"fee_per_order_usd": 1.0, "slippage_bps": 5.0, "fill_timing": "next_valid_open"},
        comparison_fields={"trade_count_delta": 0.0},
    )

    result = run_sensitivity_analysis([scenario])

    assert result.status is ValidationStatus.PASSED
    assert result.reasons == ()


def test_sensitivity_analysis_fails_missing_assumptions():
    scenario = SensitivityScenario(name="missing", assumptions={}, comparison_fields={})

    result = run_sensitivity_analysis([scenario])

    assert result.status is ValidationStatus.FAILED
    assert result.reasons
