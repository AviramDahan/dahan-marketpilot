from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_backtesting_module_has_no_order_or_external_delivery_behavior():
    text = (ROOT / "marketpilot" / "backtesting.py").read_text(encoding="utf-8").lower()

    forbidden = ["submit_order", "market_order", "telegram", "brokerage", "api_key", "password"]
    assert not any(token in text for token in forbidden)


def test_backtesting_config_keeps_unsafe_behaviors_disabled():
    text = (ROOT / "config" / "backtesting.yaml").read_text(encoding="utf-8").lower()

    assert "paper_trading_only: true" in text
    assert "submit_orders: false" in text
    assert "real_broker: false" in text
    assert "fake_results: false" in text
    assert "fake_portfolio: false" in text
