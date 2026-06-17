import json
from unittest.mock import patch

from scripts import telegram_runtime_smoke, verify_render_golive


def test_verify_render_golive_blocks_without_required_external_evidence(capsys):
    result = verify_render_golive.main(["--require-dashboard-url", "--require-shared-state"])

    output = json.loads(capsys.readouterr().out)
    assert result == 2
    assert output["status"] == "blocked_external_not_verified"
    assert output["checks"]["dashboard_url"]["status"] == "not_run"
    assert output["checks"]["shared_state"]["status"] == "not_run"
    assert output["paper_trading_only"] is True


def test_verify_render_golive_can_pass_with_mocked_required_evidence(capsys):
    class FakeSnapshot:
        key = "dashboard:latest"
        payload = {
            "source": "quantconnect",
            "authority": "authoritative",
            "fixture_label": "scheduler-production-cycle",
            "source_timestamp": "2026-06-16T14:00:00+00:00",
            "paper_trading_only": True,
        }

    with (
        patch("scripts.verify_render_golive.load_dashboard_payload_from_env", return_value=FakeSnapshot()),
        patch("scripts.verify_render_golive._check_dashboard_url", return_value={"status": "passed", "http_status": 200}),
    ):
        result = verify_render_golive.main(
            ["--dashboard-url", "https://dashboard.example", "--require-dashboard-url", "--require-shared-state"]
        )

    output = json.loads(capsys.readouterr().out)
    assert result == 0
    assert output["status"] == "passed"
    assert output["checks"]["shared_state"]["paper_trading_only"] is True


def test_runtime_telegram_smoke_is_disabled_by_default(monkeypatch, capsys):
    monkeypatch.delenv("MARKETPILOT_RUNTIME_TELEGRAM_SMOKE_ENABLED", raising=False)

    result = telegram_runtime_smoke.main()

    output = json.loads(capsys.readouterr().out)
    assert result == 2
    assert output["status"] == "not_run"
    assert output["paper_trading_only"] is True
