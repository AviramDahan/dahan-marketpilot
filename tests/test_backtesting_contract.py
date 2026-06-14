from marketpilot.backtesting import BacktestRunStatus, load_backtesting_config, record_quantconnect_not_run


def test_backtesting_config_is_fail_closed_and_conservative():
    config = load_backtesting_config()

    assert config.paper_trading_only is True
    assert config.official_authority == "quantconnect_cloud_lean"
    assert config.local_harness_enabled is True
    assert config.conservative_assumptions_present is True
    assert config.disabled_behaviors["paper_trading"] is False
    assert config.disabled_behaviors["submit_orders"] is False
    assert config.disabled_behaviors["real_broker"] is False


def test_quantconnect_not_run_record_has_no_metrics():
    event = record_quantconnect_not_run("LEAN credentials unavailable", "lean cloud backtest")

    assert event.status is BacktestRunStatus.NOT_RUN
    assert event.source == "quantconnect_cloud_lean"
    assert event.contains_performance_results is False
    assert event.metrics == {}
