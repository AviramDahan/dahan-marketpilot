import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEAN_MAIN = ROOT / "lean" / "main.py"

FORBIDDEN_METHODS = [
    "MarketOrder",
    "LimitOrder",
    "StopMarketOrder",
    "StopLimitOrder",
    "SetHoldings",
    "Liquidate",
    "SetBrokerageModel",
    "AddUniverse",
    "CloudLive",
    "LiveMode",
]


def test_lean_shell_defines_qcalgorithm_subclass():
    text = LEAN_MAIN.read_text(encoding="utf-8")

    assert "QCAlgorithm" in text
    assert "class DahanMarketPilotFoundation(QCAlgorithm)" in text


def test_lean_shell_subscribes_only_to_spy_and_qqq_benchmarks():
    text = LEAN_MAIN.read_text(encoding="utf-8")
    symbols = re.findall(r'AddEquity\("([A-Z]+)"', text)

    assert symbols == ["SPY", "QQQ"]


def test_lean_shell_contains_no_order_or_live_trading_calls():
    text = LEAN_MAIN.read_text(encoding="utf-8")

    for method in FORBIDDEN_METHODS:
        assert method not in text


def test_lean_config_contains_no_credentials():
    config_text = (ROOT / "lean" / "config.json").read_text(encoding="utf-8")
    config = json.loads(config_text)

    assert "credentials" not in config_text.lower()
    assert "token" not in config_text.lower()
    assert config["algorithm-language"] == "Python"
