import json

from scripts import phase16_2_resilience_checks


def test_resilience_all_checks_pass(capsys):
    result = phase16_2_resilience_checks.main(["all"])

    output = json.loads(capsys.readouterr().out)
    assert result == 0
    assert output["status"] == "passed"
    assert output["store"] == "memory"
    assert output["production_scheduler_lock_touched"] is False
    assert output["controls_scheduler"] is False
    assert output["checks"]["duplicate-lock"]["second_acquired"] is False
    assert output["checks"]["duplicate-lock"]["isolated_lock_namespace"] is True
    assert output["checks"]["stale-data"]["production_dashboard_touched"] is False
    assert output["checks"]["telegram-failure"]["delivery_required_for_safety"] is False
    assert output["paper_trading_only"] is True


def test_duplicate_lock_check_releases_lock():
    output = phase16_2_resilience_checks.duplicate_lock_check()

    assert output["status"] == "passed"
    assert output["cleanup_success"] is True
    assert output["controls_orders"] is False


def test_stale_data_check_uses_isolated_store():
    store = phase16_2_resilience_checks.InMemorySharedStateStore()

    output = phase16_2_resilience_checks.stale_data_check(store=store)

    assert output["status"] == "passed"
    assert output["freshness_level"] == "stale"
    assert output["production_dashboard_touched"] is False
    assert store.get_json("resilience/stale-dashboard-sample")["paper_trading_only"] is True


def test_resilience_render_store_without_env_fails_closed(capsys, monkeypatch):
    monkeypatch.delenv("REDIS_URL", raising=False)

    result = phase16_2_resilience_checks.main(["duplicate-lock", "--store", "render"])

    output = json.loads(capsys.readouterr().out)
    assert result == 1
    assert output["status"] == "failed"
    assert output["reason"] == "render_store_not_configured"
    assert output["controls_orders"] is False
