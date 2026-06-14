from pathlib import Path

from dashboard.auth import AuthStatus, DashboardAuth
from dashboard.config import DashboardConfig
from dashboard.safety_view import (
    DASHBOARD_NAVIGATION_SECTIONS,
    READ_ONLY_ALLOWED_ACTIONS,
    build_dashboard_shell,
    render_markdown,
)


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_CONTROL_TERMS = [
    "submit order",
    "buy button",
    "sell button",
    "cancel button",
    "modify button",
    "manual trade entry",
    "telegram send",
    "paper mode switch",
    "recovery approval",
    "quantconnect mutation",
    "csv export",
    "acknowledge",
    "mark read",
]


def test_navigation_is_overview_first_and_operational():
    assert DASHBOARD_NAVIGATION_SECTIONS == (
        "Overview",
        "Positions",
        "Trades",
        "Signals",
        "Backtests",
        "Strategies",
        "Risk",
        "Notifications",
        "Activity",
        "System",
    )


def test_unauthenticated_shell_never_exposes_dashboard_data():
    shell = build_dashboard_shell(
        config=DashboardConfig(password=None),
        auth=DashboardAuth(status=AuthStatus.AUTH_REQUIRED, authenticated=False),
    )

    assert shell.data_visible is False
    assert shell.controls == ("login",)
    assert shell.sections == ()
    assert "auth_required" in shell.status
    assert "portfolio" not in render_markdown().lower()


def test_authenticated_shell_exposes_only_read_only_controls():
    shell = build_dashboard_shell(
        config=DashboardConfig(password="strong-test-password"),
        auth=DashboardAuth(status=AuthStatus.AUTHENTICATED, authenticated=True),
    )

    assert shell.data_visible is True
    assert shell.sections[0] == "Overview"
    assert shell.controls == ("view", "refresh", "logout")
    assert READ_ONLY_ALLOWED_ACTIONS == ("view", "refresh", "login", "logout")
    assert "SIMULATED PAPER TRADING ONLY - NOT FINANCIAL ADVICE" in shell.disclaimer
    assert "source" in shell.status.lower()
    assert "freshness" in shell.status.lower()


def test_dashboard_source_and_rendered_shell_do_not_expose_forbidden_controls():
    combined = "\n".join(
        [
            (ROOT / "dashboard" / "app.py").read_text(encoding="utf-8"),
            (ROOT / "dashboard" / "auth.py").read_text(encoding="utf-8"),
            (ROOT / "dashboard" / "config.py").read_text(encoding="utf-8"),
            (ROOT / "dashboard" / "safety_view.py").read_text(encoding="utf-8"),
            render_markdown(),
        ]
    ).lower()

    for forbidden in FORBIDDEN_CONTROL_TERMS:
        assert forbidden not in combined


def test_dashboard_docs_capture_auth_and_read_only_surface():
    dashboard_doc = (ROOT / "docs" / "dashboard.md").read_text(encoding="utf-8")
    config_doc = (ROOT / "docs" / "configuration.md").read_text(encoding="utf-8")
    safety_doc = (ROOT / "docs" / "safety.md").read_text(encoding="utf-8")
    combined = "\n".join([dashboard_doc, config_doc, safety_doc])

    assert "DASHBOARD_PASSWORD" in combined
    assert "No dashboard data is rendered before login" in combined
    assert "view, refresh, login, and logout" in combined
    assert "Overview-first" in combined
    assert "raw dashboard password" in combined
