from pathlib import Path

from marketpilot.setups.base import SetupStatus
from marketpilot.setups.trend_pullback import evaluate_trend_pullback

from test_trend_pullback_detection import valid_input


ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_FILES = [
    ROOT / "marketpilot" / "setups" / "base.py",
    ROOT / "marketpilot" / "setups" / "trend_pullback.py",
]
FORBIDDEN = [
    "BUY",
    "WATCH",
    "AVOID",
    "MarketOrder",
    "SetHoldings",
    "Liquidate",
    "send_telegram",
    "BacktestResult",
    "Paper deployment",
    "Live deployment",
    "api_key",
    "token",
    "password",
]


def test_trend_pullback_production_files_contain_no_forbidden_behavior():
    text = "\n".join(path.read_text(encoding="utf-8") for path in PRODUCTION_FILES)

    for value in FORBIDDEN:
        assert value not in text


def test_trend_pullback_behavior_is_setup_result_only():
    result = evaluate_trend_pullback(valid_input())

    assert result.status is SetupStatus.VALID
    assert result.valid is True
    assert result.setup_name == "trend_pullback"
    assert not hasattr(result, "order")
    assert not hasattr(result, "quantity")
    assert not hasattr(result, "portfolio_weight")
    assert not hasattr(result, "telegram_message")
    assert not hasattr(result, "backtest_result")

