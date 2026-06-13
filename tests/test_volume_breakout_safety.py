from pathlib import Path

from marketpilot.setups.base import SetupStatus
from marketpilot.setups.volume_breakout import evaluate_volume_breakout

from test_volume_breakout_detection import valid_input


ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_FILES = [
    ROOT / "marketpilot" / "setups" / "base.py",
    ROOT / "marketpilot" / "setups" / "volume_breakout.py",
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


def test_volume_breakout_production_files_contain_no_forbidden_behavior():
    text = "\n".join(path.read_text(encoding="utf-8") for path in PRODUCTION_FILES)

    for value in FORBIDDEN:
        assert value not in text


def test_volume_breakout_behavior_is_setup_result_only():
    result = evaluate_volume_breakout(valid_input())

    assert result.status is SetupStatus.VALID
    assert result.valid is True
    assert result.setup_name == "volume_breakout"
    assert not hasattr(result, "order")
    assert not hasattr(result, "quantity")
    assert not hasattr(result, "portfolio_weight")
    assert not hasattr(result, "telegram_message")
    assert not hasattr(result, "backtest_result")
    assert not hasattr(result, "classification")
    assert not hasattr(result, "total_score")


def test_volume_breakout_documentation_records_setup_only_boundaries():
    text = (ROOT / "docs" / "volume_breakout.md").read_text(encoding="utf-8")

    assert "There is no BUY, WATCH, or AVOID output." in text
    assert "current-bar exclusion" in text
    assert "close-based breakout confirmation" in text
    assert "volume confirmation" in text
    assert "SET-04 hard gates" in text
    assert "no fake backtest results" in text
    assert "no profitability claims" in text


def test_testing_and_safety_docs_include_volume_breakout_coverage():
    testing = (ROOT / "docs" / "testing.md").read_text(encoding="utf-8")
    safety = (ROOT / "docs" / "safety.md").read_text(encoding="utf-8")

    assert "Phase 4 Volume Breakout" in testing
    assert "tests/test_volume_breakout_contract.py" in testing
    assert "tests/test_volume_breakout_detection.py" in testing
    assert "tests/test_volume_breakout_rejections.py" in testing
    assert "tests/test_volume_breakout_explanations.py" in testing
    assert "tests/test_volume_breakout_safety.py" in testing

    assert "SIMULATED PAPER TRADING ONLY - NOT FINANCIAL ADVICE" in safety
    assert "Volume Breakout" in safety
    assert "setup evidence only" in safety
