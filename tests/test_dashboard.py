from pathlib import Path

from dashboard.models import default_safety_state
from dashboard.safety_view import render_markdown, safety_lines
from marketpilot.constants import DISCLAIMER


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_DASHBOARD_TEXT = [
    "portfolio value",
    "mock portfolio",
    "fake holdings",
    "backtest metrics",
    "P&L",
    "profit and loss",
    "submit order",
    "buy button",
    "sell button",
    "order form",
]


def test_dashboard_safety_state_uses_shared_disclaimer():
    state = default_safety_state()

    assert state.disclaimer == DISCLAIMER
    assert "SIMULATED PAPER TRADING ONLY - NOT FINANCIAL ADVICE" in state.disclaimer


def test_dashboard_shell_lines_are_read_only_and_static():
    text = render_markdown()

    assert "Dahan MarketPilot" in text
    assert "Paper-only safety mode" in text
    assert "Read-only dashboard shell" in text
    assert "No live data connected" in text


def test_dashboard_shell_has_no_fake_trading_language():
    combined = "\n".join(
        [
            (ROOT / "dashboard" / "app.py").read_text(encoding="utf-8"),
            (ROOT / "dashboard" / "safety_view.py").read_text(encoding="utf-8"),
            (ROOT / "dashboard" / "models.py").read_text(encoding="utf-8"),
            "\n".join(safety_lines()),
        ]
    ).lower()

    for forbidden in FORBIDDEN_DASHBOARD_TEXT:
        assert forbidden.lower() not in combined
