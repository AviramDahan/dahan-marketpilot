from marketpilot.backtest_reports import ArtifactSource, build_backtest_report, build_validation_windows, render_backtest_report, report_to_dict


def _report():
    return build_backtest_report(
        title="Phase 7 validation report",
        source=ArtifactSource.SCHEMA,
        windows=build_validation_windows(2020, 2022, 2021),
        assumptions={"fees": "configured", "slippage": "configured", "fill_timing": "next_valid_open"},
        limitations=["Schema example only; no real run metrics."],
        missing_data_warnings=[],
        benchmark_comparison={"primary": "SPY", "secondary": "QQQ"},
        activation_outcome={"state": "validation_failed", "paper_eligible": False},
    )


def test_report_to_dict_is_machine_readable():
    payload = report_to_dict(_report())

    assert payload["source"] == "schema"
    assert payload["benchmark_comparison"]["primary"] == "SPY"
    assert payload["activation_outcome"]["paper_eligible"] is False


def test_rendered_report_contains_required_sections():
    rendered = render_backtest_report(_report())

    assert "# Phase 7 validation report" in rendered
    assert "SIMULATED PAPER TRADING ONLY - NOT FINANCIAL ADVICE" in rendered
    assert "Artifact source: `schema`" in rendered
    assert "## Activation Outcome" in rendered
