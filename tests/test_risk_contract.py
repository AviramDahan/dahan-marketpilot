from decimal import Decimal

import pytest

from marketpilot.risk import RiskConfig, load_risk_config


def test_risk_config_defaults_match_phase_6_decisions():
    config = load_risk_config()

    assert isinstance(config, RiskConfig)
    assert config.per_trade_risk_pct == Decimal("1.0")
    assert config.max_open_positions == 10
    assert config.max_sector_exposure_pct == Decimal("30.0")
    assert config.max_new_entries_per_day == 3
    assert config.max_position_allocation_pct == Decimal("15.0")
    assert config.minimum_reward_risk == Decimal("2.0")


def test_risk_config_requires_paper_only(tmp_path):
    path = tmp_path / "risk.yaml"
    path.write_text("risk:\n  paper_trading_only: false\n", encoding="utf-8")

    with pytest.raises(ValueError, match="paper_trading_only"):
        load_risk_config(path)


def test_risk_config_rejects_enabled_unsafe_behavior(tmp_path):
    path = tmp_path / "risk.yaml"
    path.write_text(
        """
risk:
  paper_trading_only: true
  per_trade_risk_pct: 1.0
  max_open_positions: 10
  max_sector_exposure_pct: 30.0
  max_new_entries_per_day: 3
  max_position_allocation_pct: 15.0
  minimum_reward_risk: 2.0
  minimum_quantity: 1
  disabled_behaviors:
    submit_orders: true
    broker_adapters: false
    telegram_delivery: false
    live_deployment: false
    fake_portfolio_authority: false
    leverage: false
    margin: false
    short_selling: false
    real_money_paths: false
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="submit_orders"):
        load_risk_config(path)
