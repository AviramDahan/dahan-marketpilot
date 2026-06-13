from pathlib import Path

import pytest

from marketpilot.configuration import load_strategy_config
from marketpilot.timeframes import StrategyMode


def test_strategy_config_accepts_daily_only_default():
    config = load_strategy_config("config/strategy.yaml")

    assert config.mode is StrategyMode.DAILY_ONLY
    assert config.default_mode is StrategyMode.DAILY_ONLY
    assert config.paper_trading_only is True


@pytest.mark.parametrize("mode", ["", "paper", "shadow", "daily_filter_2h_setup", None])
def test_strategy_config_fails_closed_for_invalid_modes(tmp_path, mode):
    path = tmp_path / "strategy.yaml"
    rendered_mode = "" if mode is None else mode
    path.write_text(
        f"""
strategy:
  mode: {rendered_mode}
  default_mode: daily_only
  paper_trading_only: true
  enabled_setups: []
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="strategy.mode"):
        load_strategy_config(path)


def test_strategy_config_rejects_environment_mode_leakage(tmp_path):
    path = tmp_path / "strategy.yaml"
    path.write_text(
        """
strategy:
  mode: daily_only
  default_mode: daily_only
  environment_mode: paper
  paper_trading_only: true
  enabled_setups: []
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="separate from environment mode"):
        load_strategy_config(path)


def test_strategy_config_uses_safe_yaml_loader():
    text = Path("marketpilot/configuration.py").read_text(encoding="utf-8")

    assert "yaml.safe_load" in text
