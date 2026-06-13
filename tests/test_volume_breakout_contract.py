from datetime import datetime, timezone
from pathlib import Path

import pytest

from marketpilot.setups.base import SetupRejectionReason, SetupResult, SetupStatus
from marketpilot.setups.volume_breakout import (
    CompletedDailyBar,
    calculate_prior_resistance,
    contract_result,
    load_volume_breakout_config,
)


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


def completed_bar(index, high, complete=True):
    return CompletedDailyBar(
        time=datetime(2026, 6, 1 + index, tzinfo=timezone.utc),
        open=high - 2.0,
        high=high,
        low=high - 4.0,
        close=high - 1.0,
        volume=1000000,
        complete=complete,
    )


def test_volume_breakout_contract_result_is_setup_evidence_only():
    signal_time = datetime(2026, 6, 13, tzinfo=timezone.utc)
    result = contract_result("msft", signal_time)

    assert isinstance(result, SetupResult)
    assert result.setup_name == "volume_breakout"
    assert result.symbol == "MSFT"
    assert result.status is SetupStatus.REJECTED
    assert result.rejection_reasons == (SetupRejectionReason.INCOMPLETE_COMPLETED_BAR_DATA,)
    assert result.timing.signal_time == signal_time
    assert result.timing.timing_mode == "completed_daily_bar"
    assert result.timing.uses_completed_daily_bar is True
    assert result.timing.intrabar_valid is False
    assert not hasattr(result, "order")
    assert not hasattr(result, "quantity")
    assert not hasattr(result, "portfolio_weight")
    assert not hasattr(result, "classification")
    assert not hasattr(result, "backtest_result")
    assert not hasattr(result, "telegram_message")


def test_prior_resistance_excludes_current_bar_high():
    prior_highs = [80 + index for index in range(20)]
    bars = tuple(completed_bar(index, high) for index, high in enumerate(prior_highs))
    signal_bar = completed_bar(20, 500.0)

    resistance = calculate_prior_resistance(bars + (signal_bar,), lookback_bars=20)

    assert resistance == 99


def test_prior_resistance_rejects_invalid_inputs():
    bars = tuple(completed_bar(index, 90 + index) for index in range(20))

    with pytest.raises(ValueError, match="insufficient"):
        calculate_prior_resistance(bars, lookback_bars=20)

    with pytest.raises(ValueError, match="lookback"):
        calculate_prior_resistance(bars + (completed_bar(20, 110),), lookback_bars=0)

    incomplete_prior = bars[:-1] + (completed_bar(19, 109, complete=False), completed_bar(20, 110))
    with pytest.raises(ValueError, match="complete"):
        calculate_prior_resistance(incomplete_prior, lookback_bars=20)

    incomplete_signal = bars + (completed_bar(20, 110, complete=False),)
    with pytest.raises(ValueError, match="complete"):
        calculate_prior_resistance(incomplete_signal, lookback_bars=20)

    invalid_high = bars[:-1] + (completed_bar(19, float("nan")), completed_bar(20, 110))
    with pytest.raises(ValueError, match="high"):
        calculate_prior_resistance(invalid_high, lookback_bars=20)
