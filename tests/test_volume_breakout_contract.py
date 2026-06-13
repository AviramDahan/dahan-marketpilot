from pathlib import Path

import pytest

from marketpilot.setups.base import SetupRejectionReason
from marketpilot.setups.volume_breakout import load_volume_breakout_config


ROOT = Path(__file__).resolve().parents[1]


def test_volume_breakout_config_contains_safety_bounded_defaults():
    config = load_volume_breakout_config()

    assert config["paper_trading_only"] is True
    assert config["timing_mode"] == "completed_daily_bar"
    assert config["resistance"]["lookback_bars"] == 20
    assert config["resistance"]["breakout_buffer_pct"] == 0.25
    assert config["resistance"]["require_close_above_buffered_resistance"] is True
    assert config["volume"]["average_volume_period"] == 20
    assert config["volume"]["min_volume_ratio"] == 1.5
    assert config["volume"]["min_dollar_volume"] == 20000000
    assert config["disabled_behaviors"]["intrabar_validity"] is False
    assert config["disabled_behaviors"]["create_orders"] is False
    assert config["disabled_behaviors"]["buy_watch_avoid_classifications"] is False
    assert config["disabled_behaviors"]["backtest_result_creation"] is False
    assert config["disabled_behaviors"]["telegram_delivery"] is False
    assert config["disabled_behaviors"]["paper_deployment"] is False
    assert config["disabled_behaviors"]["live_deployment"] is False


def test_volume_breakout_config_fails_closed_for_unsafe_timing(tmp_path):
    unsafe_config = tmp_path / "volume_breakout.yaml"
    unsafe_config.write_text(
        """
volume_breakout:
  paper_trading_only: false
  timing_mode: completed_daily_bar
  disabled_behaviors:
    intrabar_validity: false
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="paper_trading_only"):
        load_volume_breakout_config(unsafe_config)

    intrabar_config = tmp_path / "intrabar_volume_breakout.yaml"
    intrabar_config.write_text(
        """
volume_breakout:
  paper_trading_only: true
  timing_mode: completed_daily_bar
  disabled_behaviors:
    intrabar_validity: true
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="completed daily bars"):
        load_volume_breakout_config(intrabar_config)


def test_rejection_reason_contract_covers_volume_breakout_gates():
    required = {
        SetupRejectionReason.INVALID_PRIOR_RESISTANCE,
        SetupRejectionReason.BREAKOUT_NOT_CONFIRMED,
        SetupRejectionReason.VOLUME_CONFIRMATION_WEAK,
        SetupRejectionReason.EMA20_EXTENSION_EXCESSIVE,
        SetupRejectionReason.INSUFFICIENT_DOLLAR_VOLUME,
        SetupRejectionReason.EARNINGS_RISK_CONFLICT,
        SetupRejectionReason.PORTFOLIO_CONFLICT,
    }

    assert required.issubset(set(SetupRejectionReason))

