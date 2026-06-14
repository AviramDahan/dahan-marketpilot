import pytest

from marketpilot.backtest_reports import ArtifactSource, build_backtest_report, build_validation_windows


def test_report_requires_source_label_and_disclaimer():
    report = build_backtest_report(
        title="Fixture schema example",
        source=ArtifactSource.FIXTURE,
        windows=build_validation_windows(2020, 2022, 2021),
        assumptions={"fees": "configured", "slippage": "configured"},
        limitations=["Fixture data is not a real QuantConnect result."],
        activation_outcome={"state": "validation_failed"},
    )

    assert report.source is ArtifactSource.FIXTURE
    assert report.disclaimer == "SIMULATED PAPER TRADING ONLY - NOT FINANCIAL ADVICE"
    assert report.report_complete is True


def test_non_real_artifact_cannot_hold_performance_metrics():
    with pytest.raises(ValueError, match="real QuantConnect"):
        build_backtest_report(
            title="Fixture with forbidden metrics",
            source=ArtifactSource.FIXTURE,
            windows=build_validation_windows(2020, 2022, 2021),
            assumptions={"fees": "configured"},
            limitations=["Synthetic fixture only."],
            activation_outcome={"state": "validation_failed"},
            metrics={"total_return": 0.12},
        )
