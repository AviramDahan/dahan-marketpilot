from __future__ import annotations

import re
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
CHECKOUT_SHA = "df4cb1c069e1874edd31b4311f1884172cec0e10"
SETUP_PYTHON_SHA = "a309ff8b426b58ec0e2a45f0f869d46889d02405"
APPROVED_ACTIONS = {
    f"actions/checkout@{CHECKOUT_SHA}",
    f"actions/setup-python@{SETUP_PYTHON_SHA}",
}
SECRET_PATTERNS = (
    "secrets.QUANTCONNECT",
    "secrets.TELEGRAM",
    "secrets.RENDER",
    "secrets.DASHBOARD",
    "QUANTCONNECT_API_TOKEN",
    "TELEGRAM_BOT_TOKEN",
    "RENDER_DEPLOY",
    "DASHBOARD_HEALTH_URL",
    "broker",
)
FORBIDDEN_EXTERNAL_COMMANDS = (
    "lean cloud push",
    "lean cloud backtest",
    "lean live",
    "lean deploy",
    "sendMessage",
    "curl -X POST",
    "Invoke-WebRequest -Method Post",
)


def _workflow(name: str) -> dict[str, object]:
    return yaml.safe_load((WORKFLOWS / name).read_text(encoding="utf-8"))


def _workflow_text(name: str) -> str:
    return (WORKFLOWS / name).read_text(encoding="utf-8")


def _walk_values(value: object):
    if isinstance(value, dict):
        for child in value.values():
            yield from _walk_values(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_values(child)
    else:
        yield value


def _workflow_triggers(workflow: dict[str, object]) -> dict[str, object]:
    return workflow.get("on", {})


def test_default_tests_workflow_is_offline_secret_free_and_least_privilege():
    workflow = _workflow("tests.yml")
    text = _workflow_text("tests.yml")
    values = [str(value) for value in _walk_values(workflow)]

    assert workflow["permissions"] == {"contents": "read"}
    assert "push" in _workflow_triggers(workflow)
    assert "pull_request" in _workflow_triggers(workflow)
    assert any("3.11.9" in value for value in values)
    assert any("python -m pip install -r requirements-dev.txt" in value for value in values)
    assert any("python -m pytest -q" in value for value in values)

    for pattern in SECRET_PATTERNS:
        assert pattern not in text


def test_all_workflow_actions_are_official_and_pinned_to_full_shas():
    sha_ref = re.compile(r"^actions/(checkout|setup-python)@[0-9a-f]{40}$")

    for path in WORKFLOWS.glob("*.yml"):
        workflow = _workflow(path.name)
        uses_values = [
            str(value) for value in _walk_values(workflow) if str(value).startswith("actions/")
        ]
        assert uses_values, path.name
        for uses in uses_values:
            assert uses in APPROVED_ACTIONS
            assert sha_ref.match(uses)
            assert "@v" not in uses


def test_quantconnect_workflow_is_manual_guarded_and_records_not_run():
    workflow = _workflow("quantconnect.yml")
    text = _workflow_text("quantconnect.yml")
    triggers = _workflow_triggers(workflow)

    assert set(triggers) == {"workflow_dispatch"}
    assert "operator_confirmation" in text
    assert "QUANTCONNECT_USER_ID" in text
    assert "QUANTCONNECT_API_TOKEN" in text
    assert "QUANTCONNECT_PROJECT_ID" in text
    assert "not_run" in text
    assert "Lean package install is intentionally disabled" in text
    assert "python -m pip install lean" not in text

    for command in FORBIDDEN_EXTERNAL_COMMANDS:
        assert command not in text


def test_weekly_validation_is_offline_scheduled_and_manual():
    workflow = _workflow("weekly-validation.yml")
    text = _workflow_text("weekly-validation.yml")
    triggers = _workflow_triggers(workflow)
    values = [str(value) for value in _walk_values(workflow)]

    assert "schedule" in triggers
    assert "workflow_dispatch" in triggers
    assert any("python -m pytest -q" in value for value in values)
    assert "secrets." not in text
    assert "not_run" in text


def test_dashboard_health_is_read_only_guarded_and_does_not_print_url():
    workflow = _workflow("dashboard-health.yml")
    text = _workflow_text("dashboard-health.yml")
    triggers = _workflow_triggers(workflow)

    assert "schedule" in triggers
    assert "workflow_dispatch" in triggers
    assert "DASHBOARD_HEALTH_URL" in text
    assert "not_run" in text
    assert "curl --fail --silent --show-error --location" in text
    assert "echo \"$DASHBOARD_HEALTH_URL\"" not in text
    assert "Write-Output $env:DASHBOARD_HEALTH_URL" not in text

    for command in FORBIDDEN_EXTERNAL_COMMANDS:
        assert command not in text
