from datetime import datetime, timezone

from marketpilot.setups.base import SetupTiming
from marketpilot.timeframes import (
    BarCompletionStatus,
    BarSessionMetadata,
    BarTimeframe,
    CompletedBar,
    StrategyMode,
    TimeframeReadiness,
    TimeframeReadinessStatus,
    timeframe_allowed_for_strategy_mode,
)


def test_completed_bar_rejects_partial_session_as_signal():
    bar = CompletedBar(
        time=datetime(2026, 6, 15, 17, 30, tzinfo=timezone.utc),
        open=100,
        high=101,
        low=99,
        close=100.5,
        volume=1000000,
        timeframe=BarTimeframe.FOUR_HOUR,
        completion_status=BarCompletionStatus.PARTIAL_SESSION,
        session=BarSessionMetadata(
            exchange_timezone="America/New_York",
            regular_hours=True,
            partial_session=True,
            source_resolution="minute",
        ),
    )

    assert bar.complete is False
    assert bar.valid_for_signal() is False


def test_setup_timing_preserves_mtf_metadata():
    signal_time = datetime(2026, 6, 15, 17, 30, tzinfo=timezone.utc)
    timing = SetupTiming(
        signal_time=signal_time,
        timing_mode=BarTimeframe.FOUR_HOUR.timing_mode,
        uses_completed_daily_bar=False,
        strategy_mode=StrategyMode.DAILY_FILTER_4H_SETUP,
        signal_timeframe=BarTimeframe.FOUR_HOUR,
        bar_start=datetime(2026, 6, 15, 13, 30, tzinfo=timezone.utc),
        bar_end=signal_time,
        exchange_timezone="America/New_York",
        regular_hours=True,
        partial_session=False,
        freshness="fresh",
        source_resolution="minute",
        later_valid_execution_required=True,
    )

    assert timing.timing_mode == "completed_four_hour_bar"
    assert timing.strategy_mode is StrategyMode.DAILY_FILTER_4H_SETUP
    assert timing.signal_timeframe is BarTimeframe.FOUR_HOUR
    assert timing.partial_session is False
    assert timing.later_valid_execution_required is True


def test_timeframe_allowed_for_strategy_mode():
    assert timeframe_allowed_for_strategy_mode(StrategyMode.DAILY_ONLY, BarTimeframe.DAILY)
    assert not timeframe_allowed_for_strategy_mode(StrategyMode.DAILY_ONLY, BarTimeframe.FOUR_HOUR)
    assert timeframe_allowed_for_strategy_mode(StrategyMode.DAILY_FILTER_4H_SETUP, BarTimeframe.FOUR_HOUR)
    assert not timeframe_allowed_for_strategy_mode(StrategyMode.DAILY_FILTER_4H_SETUP, BarTimeframe.ONE_HOUR)
    assert timeframe_allowed_for_strategy_mode(StrategyMode.DAILY_FILTER_4H_SETUP_1H_OPTIONAL, BarTimeframe.ONE_HOUR)


def test_optional_one_hour_readiness_does_not_reject_signal():
    readiness = TimeframeReadiness(
        timeframe=BarTimeframe.ONE_HOUR,
        status=TimeframeReadinessStatus.OPTIONAL_MISSING,
        mandatory=False,
        reason="not subscribed",
    )

    assert readiness.ready is False
    assert readiness.rejects_signal is False
