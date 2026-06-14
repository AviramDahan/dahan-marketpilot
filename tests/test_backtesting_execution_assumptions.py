from datetime import datetime, timezone

from marketpilot.backtesting import FillModel, FillTiming, load_backtesting_config, validate_no_lookahead
from marketpilot.timeframes import BarTimeframe, StrategyMode


def _dt(hour: int) -> datetime:
    return datetime(2026, 1, 5, hour, tzinfo=timezone.utc)


def test_default_fill_assumptions_use_next_valid_open():
    config = load_backtesting_config()

    assert config.fill_model is FillModel.CONSERVATIVE_NEXT_BAR
    assert config.fill_timing is FillTiming.NEXT_VALID_OPEN
    assert config.partial_fills == "conservative_partial_or_unfilled"


def test_all_strategy_modes_have_explicit_timing_alignment():
    cases = [
        (StrategyMode.DAILY_ONLY, BarTimeframe.DAILY),
        (StrategyMode.DAILY_FILTER_4H_SETUP, BarTimeframe.FOUR_HOUR),
        (StrategyMode.DAILY_FILTER_4H_SETUP_1H_OPTIONAL, BarTimeframe.FOUR_HOUR),
        (StrategyMode.DAILY_FILTER_4H_SETUP_1H_OPTIONAL, BarTimeframe.ONE_HOUR),
    ]

    for mode, timeframe in cases:
        result = validate_no_lookahead(
            signal_time=_dt(10),
            fill_time=_dt(11),
            available_bar_times=[_dt(9), _dt(10)],
            strategy_mode=mode,
            signal_timeframe=timeframe,
        )
        assert result.passed, (mode, timeframe, result.reasons)
