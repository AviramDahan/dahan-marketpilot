from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SECRET_ENV_NAMES = {
    "DASHBOARD_PASSWORD",
    "QUANTCONNECT_USER_ID",
    "QUANTCONNECT_API_TOKEN",
    "QUANTCONNECT_PROJECT_ID",
    "QUANTCONNECT_LIVE_DEPLOY_ID",
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID",
}


def _render_service() -> dict[str, object]:
    return _service_by_name("dahan-marketpilot-dashboard")


def _service_by_name(name: str) -> dict[str, object]:
    loaded = yaml.safe_load((ROOT / "render.yaml").read_text(encoding="utf-8"))
    services = loaded["services"]
    matches = [service for service in services if service.get("name") == name]
    assert len(matches) == 1
    return matches[0]


def test_render_blueprint_starts_streamlit_on_render_port():
    service = _render_service()

    assert service["type"] == "web"
    assert service["runtime"] == "python"
    assert service["buildCommand"] == "pip install -r requirements.txt && pip install -e ."
    assert service["startCommand"] == (
        "streamlit run dashboard/app.py --server.address=0.0.0.0 --server.port=$PORT"
    )


def test_render_blueprint_uses_python_311_and_secret_references_only():
    service = _render_service()
    env_vars = {item["key"]: item for item in service["envVars"]}

    assert env_vars["PYTHON_VERSION"]["value"].startswith("3.11.")
    assert env_vars["PYTHONPATH"]["value"] == "."
    for name in SECRET_ENV_NAMES:
        assert name in env_vars
        assert env_vars[name]["sync"] is False
        assert "value" not in env_vars[name]


def test_render_blueprint_defines_scheduler_background_worker():
    service = _service_by_name("dahan-marketpilot-scheduler")
    env_vars = {item["key"]: item for item in service["envVars"]}

    assert service["type"] == "worker"
    assert service["runtime"] == "python"
    assert service["buildCommand"] == "pip install -r requirements.txt && pip install -e ."
    assert service["startCommand"] == "python -m marketpilot.production_runner scheduler"
    assert env_vars["PYTHON_VERSION"]["value"].startswith("3.11.")
    assert env_vars["PYTHONPATH"]["value"] == "."
    assert env_vars["MARKETPILOT_ENV"]["value"] == "paper"
    for name in {
        "QUANTCONNECT_USER_ID",
        "QUANTCONNECT_API_TOKEN",
        "QUANTCONNECT_PROJECT_ID",
        "QUANTCONNECT_LIVE_DEPLOY_ID",
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
    }:
        assert env_vars[name]["sync"] is False
        assert "value" not in env_vars[name]


def test_render_blueprint_defines_shared_key_value_and_injects_redis_url():
    keyvalue = _service_by_name("dahan-marketpilot-state")
    dashboard_env = {item["key"]: item for item in _service_by_name("dahan-marketpilot-dashboard")["envVars"]}
    worker_env = {item["key"]: item for item in _service_by_name("dahan-marketpilot-scheduler")["envVars"]}
    health_env = {item["key"]: item for item in _service_by_name("dahan-marketpilot-heartbeat-health")["envVars"]}

    assert keyvalue["type"] == "keyvalue"
    assert keyvalue["persistenceMode"] == "journal-snapshot"
    assert keyvalue["maxmemoryPolicy"] == "noeviction"
    assert keyvalue["ipAllowList"] == []

    for env_vars in (dashboard_env, worker_env, health_env):
        redis_url = env_vars["REDIS_URL"]
        assert redis_url["fromService"] == {
            "name": "dahan-marketpilot-state",
            "type": "keyvalue",
            "property": "connectionString",
        }
        assert "value" not in redis_url


def test_render_blueprint_defines_read_only_heartbeat_health_service():
    service = _service_by_name("dahan-marketpilot-heartbeat-health")
    env_vars = {item["key"]: item for item in service["envVars"]}

    assert service["type"] == "web"
    assert service["runtime"] == "python"
    assert service["buildCommand"] == "pip install -r requirements.txt && pip install -e ."
    assert service["startCommand"] == "python -m marketpilot.heartbeat_health_server --host=0.0.0.0 --port=$PORT"
    assert service["healthCheckPath"] == "/"
    assert env_vars["MARKETPILOT_ENV"]["value"] == "paper"
    assert env_vars["MARKETPILOT_HEALTH_MAX_AGE_SECONDS"]["value"] == "900"


def test_runtime_dependencies_are_limited_to_approved_packages():
    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert "APScheduler>=3.10,<4" in requirements
    assert '"APScheduler>=3.10,<4"' in pyproject
    assert "PyYAML>=6.0.2" in requirements
    assert "redis>=5.0,<6" in requirements
    assert '"redis>=5.0,<6"' in pyproject
    assert "streamlit>=1.51,<2" in requirements
    assert "streamlit>=1.51,<2" in pyproject
    assert "Authlib" not in pyproject
    assert "streamlit[auth]" not in pyproject
    assert "requests" not in pyproject
    assert "httpx" not in pyproject


def test_env_example_and_docs_list_names_without_secret_values():
    combined = "\n".join(
        [
            (ROOT / ".env.example").read_text(encoding="utf-8"),
            (ROOT / "docs" / "render_dashboard.md").read_text(encoding="utf-8"),
            (ROOT / "docs" / "configuration.md").read_text(encoding="utf-8"),
        ]
    )

    for name in SECRET_ENV_NAMES:
        assert name in combined

    for line in (ROOT / ".env.example").read_text(encoding="utf-8").splitlines():
        if any(line.startswith(f"{name}=") for name in SECRET_ENV_NAMES):
            assert line.endswith("=")


def test_dashboard_package_is_included_for_render_runtime():
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert '"dashboard*"' in pyproject


def test_dashboard_cache_thresholds_are_documented_and_configured():
    config = yaml.safe_load((ROOT / "config" / "dashboard.yaml").read_text(encoding="utf-8"))["dashboard"]
    docs = (ROOT / "docs" / "render_dashboard.md").read_text(encoding="utf-8")

    assert config["cache_ttl_seconds"] == 60
    assert config["stale_warning_seconds"] == 600
    assert config["stale_error_seconds"] == 1800
    assert "10 minutes" in docs
    assert "30 minutes" in docs
