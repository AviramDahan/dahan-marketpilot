from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from dashboard.auth import (
    AuthStatus,
    DashboardAuth,
    authenticate_dashboard,
    dashboard_data_visible,
)
from dashboard.config import DashboardConfig, load_dashboard_config


ROOT = Path(__file__).resolve().parents[1]


def test_dashboard_config_accepts_only_safe_invariants():
    config = load_dashboard_config(
        ROOT / "config" / "dashboard.yaml",
        env={"DASHBOARD_PASSWORD": "strong-test-password"},
    )

    assert config.paper_trading_only is True
    assert config.read_only is True
    assert config.manual_order_controls_enabled is False
    assert config.trading_currency == "USD"
    assert config.display_currency == "NIS"
    assert config.password_env_var == "DASHBOARD_PASSWORD"
    assert config.allowed_actions == ("view", "refresh", "login", "logout")
    assert config.navigation_sections[0] == "Overview"
    assert "Orders" not in config.navigation_sections


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("paper_trading_only", False),
        ("read_only", False),
        ("manual_order_controls_enabled", True),
        ("trading_currency", "NIS"),
        ("display_currency", "USD"),
    ],
)
def test_dashboard_config_fails_closed_for_unsafe_values(tmp_path, key, value):
    config_path = tmp_path / "dashboard.yaml"
    config_path.write_text(
        "\n".join(
            [
                "dashboard:",
                "  paper_trading_only: true",
                "  read_only: true",
                "  manual_order_controls_enabled: false",
                "  trading_currency: USD",
                "  display_currency: NIS",
                "  password_env_var: DASHBOARD_PASSWORD",
                "  auth_enabled: true",
                "  allowed_actions: [view, refresh, login, logout]",
                "  navigation_sections: [Overview]",
                f"  {key}: {str(value).lower() if isinstance(value, bool) else value}",
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        load_dashboard_config(config_path, env={"DASHBOARD_PASSWORD": "strong-test-password"})


def test_dashboard_password_loaded_only_from_env_and_repr_is_safe():
    config = load_dashboard_config(
        ROOT / "config" / "dashboard.yaml",
        env={"DASHBOARD_PASSWORD": "strong-test-password"},
    )

    assert config.password == "strong-test-password"
    assert "strong-test-password" not in repr(config)
    assert config.to_safe_dict()["password"] == "[redacted]"
    assert "strong-test-password" not in (ROOT / "config" / "dashboard.yaml").read_text(encoding="utf-8")

    try:
        config.password_env_var = "OTHER"
    except Exception as exc:
        assert isinstance(exc, FrozenInstanceError)
    else:
        raise AssertionError("DashboardConfig must be immutable.")


def test_authenticate_dashboard_uses_safe_statuses_without_password_disclosure():
    config = DashboardConfig(password="strong-test-password")

    missing = DashboardAuth.from_config(DashboardConfig(password=None))
    assert missing.status is AuthStatus.AUTH_REQUIRED
    assert dashboard_data_visible(missing) is False

    failed = authenticate_dashboard(config, "wrong-password")
    assert failed.status is AuthStatus.AUTH_FAILED
    assert failed.authenticated is False
    assert dashboard_data_visible(failed) is False
    assert "strong-test-password" not in failed.to_safe_dict()["message"]
    assert "wrong-password" not in failed.to_safe_dict()["message"]

    passed = authenticate_dashboard(config, "strong-test-password")
    assert passed.status is AuthStatus.AUTHENTICATED
    assert passed.authenticated is True
    assert dashboard_data_visible(passed) is True


def test_missing_or_empty_dashboard_password_fails_closed():
    missing = load_dashboard_config(ROOT / "config" / "dashboard.yaml", env={})
    empty = load_dashboard_config(ROOT / "config" / "dashboard.yaml", env={"DASHBOARD_PASSWORD": " "})

    assert missing.password is None
    assert empty.password is None
    assert DashboardAuth.from_config(missing).status is AuthStatus.AUTH_REQUIRED
    assert DashboardAuth.from_config(empty).status is AuthStatus.AUTH_REQUIRED
