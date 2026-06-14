from marketpilot.validation import ValidationStatus, compare_benchmarks


def test_benchmark_comparison_uses_spy_primary_and_qqq_secondary():
    result = compare_benchmarks(strategy_return=0.05, spy_return=0.03, qqq_return=0.04)

    assert result.primary_symbol == "SPY"
    assert result.secondary_symbol == "QQQ"
    assert result.status is ValidationStatus.PASSED
    assert result.values["excess_vs_spy"] == 0.020000000000000004


def test_missing_spy_makes_benchmark_unavailable():
    result = compare_benchmarks(strategy_return=0.05, spy_return=None, qqq_return=0.04)

    assert result.status is ValidationStatus.UNAVAILABLE
    assert "primary_benchmark_spy_unavailable" in result.reasons
