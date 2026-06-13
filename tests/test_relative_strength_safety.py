from pathlib import Path

from marketpilot.setups.base import SetupStatus
from marketpilot.setups.relative_strength import evaluate_relative_strength_leader
from test_relative_strength_detection import valid_input


ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_FILES = [
    ROOT / "marketpilot" / "setups" / "relative_strength.py",
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
    "api_key",
    "password",
]


def test_relative_strength_production_files_contain_no_forbidden_behavior():
    text = "\n".join(path.read_text(encoding="utf-8") for path in PRODUCTION_FILES)

    for value in FORBIDDEN:
        assert value not in text


def test_relative_strength_behavior_is_setup_result_only():
    result = evaluate_relative_strength_leader(valid_input())

    assert result.status is SetupStatus.VALID
    assert not hasattr(result, "order")
    assert not hasattr(result, "quantity")
    assert not hasattr(result, "portfolio_weight")
    assert not hasattr(result, "telegram_message")
    assert not hasattr(result, "backtest_result")
    assert not hasattr(result, "classification")
    assert not hasattr(result, "total_score")


def test_relative_strength_documentation_records_boundaries():
    text = (ROOT / "docs" / "relative_strength.md").read_text(encoding="utf-8")

    assert "SPY as the hard" in text
    assert "QQQ" in text
    assert "setup-only" in text
    assert "no score" in text.lower()
