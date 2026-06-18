from pathlib import Path
from unittest.mock import patch

from scripts import phase16_2_uat01_preflight


def test_preflight_reports_missing_env_without_values():
    result = phase16_2_uat01_preflight.run_preflight(
        env={},
        dashboard_url="https://example.test",
        heartbeat_url=None,
        shared_state_url=None,
        heartbeat_path=Path("missing.jsonl"),
        max_heartbeat_age_seconds=900,
        timeout_seconds=1,
    )

    assert result["status"] == "blocked_external_not_verified"
    assert result["checks"]["environment"]["missing"]
    assert result["checks"]["environment"]["values_printed"] is False
    assert result["controls_orders"] is False


def test_preflight_detects_temporary_probe_configuration():
    env = {
        "QUANTCONNECT_USER_ID": "configured",
        "QUANTCONNECT_API_TOKEN": "configured",
        "QC_PROJECT_ID": "123",
        "QC_DEPLOY_ID": "L-paper",
        "TELEGRAM_BOT_TOKEN": "configured",
        "TELEGRAM_CHAT_ID": "configured",
        "MARKETPILOT_RUNTIME_INPUT_KIND": "operator_paper_probe",
        "MARKETPILOT_OPERATOR_PAPER_PROBE_ENABLED": "true",
    }

    with (
        patch("scripts.phase16_2_uat01_preflight._check_quantconnect_deployment", return_value={"status": "passed"}),
        patch("scripts.phase16_2_uat01_preflight._check_telegram_configuration", return_value={"status": "passed"}),
        patch("scripts.phase16_2_uat01_preflight.observe_deployed_session", return_value={"status": "passed"}),
    ):
        result = phase16_2_uat01_preflight.run_preflight(
            env=env,
            dashboard_url="https://example.test",
            heartbeat_url="https://example.test/heartbeat",
            shared_state_url="https://example.test/dashboard-state",
            heartbeat_path=Path("missing.jsonl"),
            max_heartbeat_age_seconds=900,
            timeout_seconds=1,
        )

    assert result["status"] == "blocked_external_not_verified"
    assert result["checks"]["operator_probe_disabled"]["status"] == "temporary_uat_configuration_present"
    assert result["checks"]["operator_probe_disabled"]["restore_runtime_input_kind"] == "none"
