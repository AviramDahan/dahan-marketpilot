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
    loaded = yaml.safe_load((ROOT / "render.yaml").read_text(encoding="utf-8"))
    services = loaded["services"]
    assert len(services) == 1
    return services[0]


def test_render_blueprint_starts_streamlit_on_render_port():
    service = _render_service()

    assert service["type"] == "web"
    assert service["runtime"] == "python"
    assert service["buildCommand"] == "pip install -r requirements.txt"
    assert service["startCommand"] == (
        "streamlit run dashboard/app.py --server.address=0.0.0.0 --server.port=$PORT"
    )


def test_render_blueprint_uses_python_311_and_secret_references_only():
    service = _render_service()
    env_vars = {item["key"]: item for item in service["envVars"]}

    assert env_vars["PYTHON_VERSION"]["value"].startswith("3.11.")
    for name in SECRET_ENV_NAMES:
        assert name in env_vars
        assert env_vars[name]["sync"] is False
        assert "value" not in env_vars[name]


def test_runtime_dependencies_are_limited_to_approved_packages():
    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert "PyYAML>=6.0.2" in requirements
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
