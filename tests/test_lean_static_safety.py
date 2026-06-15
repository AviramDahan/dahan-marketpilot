import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEAN_MAIN = ROOT / "lean" / "main.py"

FORBIDDEN_METHODS = [
    "MarketOrder",
    "market_order",
    "LimitOrder",
    "limit_order",
    "StopMarketOrder",
    "stop_market_order",
    "StopLimitOrder",
    "stop_limit_order",
    "SetHoldings",
    "set_holdings",
    "Liquidate",
    "liquidate",
    "SetBrokerageModel",
    "set_brokerage_model",
    "CloudLive",
    "LiveMode",
    "live_mode",
]


def test_lean_shell_defines_qcalgorithm_subclass():
    text = LEAN_MAIN.read_text(encoding="utf-8")

    assert "QCAlgorithm" in text
    assert "class DahanMarketPilotRuntime(QCAlgorithm)" in text


def test_lean_adapter_keeps_benchmark_subscriptions_and_audited_dynamic_universe():
    text = LEAN_MAIN.read_text(encoding="utf-8")
    symbols = re.findall(r'add_equity\("([A-Z]+)"', text)

    assert symbols == ["SPY", "QQQ"]
    assert "add_universe(" in text
    assert "select_dynamic_universe" in text
    assert "runtime_bridge.on_securities_changed" in text


def test_lean_adapter_contains_no_uncontrolled_order_or_live_trading_calls():
    text = LEAN_MAIN.read_text(encoding="utf-8")

    for method in FORBIDDEN_METHODS:
        assert method not in text


def test_lean_adapter_delegates_strategy_decisions_to_marketpilot_runtime():
    text = LEAN_MAIN.read_text(encoding="utf-8")

    assert "LeanRuntimeBridge" in text
    assert "runtime_bridge.on_completed_bar" in text
    assert "runtime_bridge.export_dashboard_evidence" in text
    assert "run_runtime_pipeline(" not in text
    assert "score_setup_result(" not in text
    assert "rank_candidates(" not in text
    assert "evaluate_portfolio_risk(" not in text


def test_lean_config_contains_no_credentials():
    config_text = (ROOT / "lean" / "config.json").read_text(encoding="utf-8")
    config = json.loads(config_text)

    assert "credentials" not in config_text.lower()
    assert "token" not in config_text.lower()
    assert config["algorithm-language"] == "Python"
