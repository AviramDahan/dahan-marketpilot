import json

from scripts import phase16_2_resilience_checks


def test_resilience_all_checks_pass(capsys):
    result = phase16_2_resilience_checks.main(["all"])

    output = json.loads(capsys.readouterr().out)
    assert result == 0
    assert output["status"] == "passed"
    assert output["checks"]["duplicate-lock"]["second_acquired"] is False
    assert output["checks"]["telegram-failure"]["delivery_required_for_safety"] is False
    assert output["paper_trading_only"] is True


def test_duplicate_lock_check_releases_lock():
    output = phase16_2_resilience_checks.duplicate_lock_check()

    assert output["status"] == "passed"
    assert output["cleanup_success"] is True
    assert output["controls_orders"] is False

