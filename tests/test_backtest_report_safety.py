from marketpilot.backtest_reports import ArtifactSource, build_backtest_report, build_validation_windows, report_to_dict


def test_report_surfaces_limitations_and_missing_data():
    report = build_backtest_report(
        title="Not run report",
        source=ArtifactSource.NOT_RUN,
        windows=build_validation_windows(2022, 2022, 2022),
        assumptions={"fees": "configured", "slippage": "configured"},
        limitations=["QuantConnect access was unavailable."],
        missing_data_warnings=["Out-of-sample window unavailable."],
        activation_outcome={"state": "validation_failed"},
    )
    payload = report_to_dict(report)

    assert payload["limitations"]
    assert payload["missing_data_warnings"] == ["Out-of-sample window unavailable."]
    assert payload["metrics"] == {}
