from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def test_paper_trading_config_contains_no_secret_values_or_real_brokerage():
    data = yaml.safe_load((ROOT / "config" / "paper_trading.yaml").read_text(encoding="utf-8"))
    text = (ROOT / "config" / "paper_trading.yaml").read_text(encoding="utf-8").lower()

    assert data["paper_trading"]["paper_trading_only"] is True
    assert "interactive brokers" not in text
    assert "tradier" not in text
    assert "schwab" not in text
    assert "real_money: true" not in text
    assert "api_token:" not in text
    assert "telegram_bot_token:" not in text


def test_quantconnect_paper_module_never_executes_deployment_commands():
    text = (ROOT / "marketpilot" / "quantconnect_paper.py").read_text(encoding="utf-8")

    assert "subprocess" not in text
    assert "os.system" not in text
    assert ".run(" not in text
    assert "Popen" not in text
    assert "start live node" not in text.lower()


def test_quantconnect_paper_module_does_not_create_fake_deployment_state():
    text = (ROOT / "marketpilot" / "quantconnect_paper.py").read_text(encoding="utf-8").lower()

    assert "fake_deployment_id" not in text
    assert "deployment_id = " not in text
    assert "paper_portfolio = " not in text
