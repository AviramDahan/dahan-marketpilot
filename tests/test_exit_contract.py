from marketpilot.exits import ExitPlan, load_exit_config


def test_exit_config_is_paper_only_and_trailing_disabled_by_default():
    config = load_exit_config()

    assert config["paper_trading_only"] is True
    assert config["minimum_target_r_multiple"] == 2.0
    assert config["trailing_stop"]["enabled"] is False
    assert config["partial_exits"]["rules"][0]["r_multiple"] == 2.0


def test_exit_plan_contract_has_no_execution_methods():
    assert not hasattr(ExitPlan, "submit")
    assert not hasattr(ExitPlan, "cancel")
