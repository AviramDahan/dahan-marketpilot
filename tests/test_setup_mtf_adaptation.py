from datetime import datetime, timezone

from marketpilot.data_quality import DataQualityStatus
from marketpilot.indicators import IndicatorResult, ReadinessStatus
from marketpilot.regime import MarketRegime, RegimeResult
from marketpilot.setups.base import SetupStatus
from marketpilot.setups.trend_pullback import CompletedDailyBar as TrendBar
from marketpilot.setups.trend_pullback import TrendPullbackInput, evaluate_trend_pullback
from marketpilot.setups.volume_breakout import CompletedDailyBar as BreakoutBar
from marketpilot.setups.volume_breakout import VolumeBreakoutInput, evaluate_volume_breakout
from marketpilot.symbol_data import SymbolData
from marketpilot.timeframes import BarTimeframe, StrategyMode


def evidence_value(result, name):
    return next(item.value for item in result.evidence if item.name == name)


def ready_indicator(name, value):
    return IndicatorResult(name=name, status=ReadinessStatus.READY, value=value, required_points=20, available_points=260)


def trend_indicators():
    return {
        "EMA20": ready_indicator("EMA20", 100.0),
        "EMA50": ready_indicator("EMA50", 98.0),
        "EMA200": ready_indicator("EMA200", 80.0),
        "RSI14": ready_indicator("RSI14", 55.0),
        "MACD": ready_indicator("MACD", 1.5),
        "ATR14": ready_indicator("ATR14", 3.0),
    }


def breakout_indicators():
    return {
        "EMA20": ready_indicator("EMA20", 100.0),
        "ATR14": ready_indicator("ATR14", 4.0),
    }


def valid_trend_input():
    active_indicators = trend_indicators()
    symbol_data = SymbolData("MSFT", "Technology", DataQualityStatus.ACCEPTED, active_indicators)
    closes = (103.0, 101.0, 99.8, 100.7, 102.0)
    bars = tuple(
        TrendBar(
            time=datetime(2026, 6, 1 + index, tzinfo=timezone.utc),
            open=close + 0.3,
            high=close + 1.0,
            low=close - 1.0,
            close=close,
            volume=900000 if index < len(closes) - 1 else 1200000,
        )
        for index, close in enumerate(closes)
    )
    return TrendPullbackInput(
        symbol_data=symbol_data,
        regime=RegimeResult(MarketRegime.RISK_ON, True, True, None, ("supportive",)),
        bars=bars,
        indicators=active_indicators,
        average_volume=1000000,
        atr_pct=4.0,
        reward_risk_proxy=2.0,
    )


def valid_breakout_input():
    active_indicators = breakout_indicators()
    symbol_data = SymbolData("MSFT", "Technology", DataQualityStatus.ACCEPTED, active_indicators)
    prior = tuple(
        BreakoutBar(
            time=datetime(2026, 6, 1 + index, tzinfo=timezone.utc),
            open=96.0 + index * 0.1,
            high=98.0 + (index % 3) * 0.5,
            low=95.0 + index * 0.1,
            close=97.0 + index * 0.1,
            volume=1000000,
        )
        for index in range(20)
    )
    signal = BreakoutBar(
        time=datetime(2026, 6, 21, tzinfo=timezone.utc),
        open=99.0,
        high=101.0,
        low=98.5,
        close=100.5,
        volume=1600000,
    )
    return VolumeBreakoutInput(
        symbol_data=symbol_data,
        regime=RegimeResult(MarketRegime.RISK_ON, True, True, None, ("supportive",)),
        bars=prior + (signal,),
        indicators=active_indicators,
        average_volume=1000000,
        average_dollar_volume=30000000,
        atr_pct=4.0,
        projected_target=110.0,
    )


def test_trend_pullback_accepts_4h_primary_setup_mode_without_one_hour_confirmation():
    base = valid_trend_input()
    setup_input = TrendPullbackInput(
        **{
            **base.__dict__,
            "strategy_mode": StrategyMode.DAILY_FILTER_4H_SETUP_1H_OPTIONAL,
            "signal_timeframe": BarTimeframe.FOUR_HOUR,
            "one_hour_confirmation_available": False,
        }
    )

    result = evaluate_trend_pullback(setup_input)

    assert result.status is SetupStatus.VALID
    assert result.timing.timing_mode == "completed_four_hour_bar"
    assert result.timing.uses_completed_daily_bar is False
    assert result.timing.strategy_mode is StrategyMode.DAILY_FILTER_4H_SETUP_1H_OPTIONAL
    assert evidence_value(result, "strategy_mode") == "daily_filter_4h_setup_1h_optional"
    assert evidence_value(result, "one_hour_confirmation_available") is False


def test_volume_breakout_accepts_4h_primary_setup_mode_without_one_hour_confirmation():
    base = valid_breakout_input()
    setup_input = VolumeBreakoutInput(
        **{
            **base.__dict__,
            "strategy_mode": StrategyMode.DAILY_FILTER_4H_SETUP_1H_OPTIONAL,
            "signal_timeframe": BarTimeframe.FOUR_HOUR,
            "one_hour_confirmation_available": False,
        }
    )

    result = evaluate_volume_breakout(setup_input)

    assert result.status is SetupStatus.VALID
    assert result.timing.timing_mode == "completed_four_hour_bar"
    assert result.timing.uses_completed_daily_bar is False
    assert result.timing.strategy_mode is StrategyMode.DAILY_FILTER_4H_SETUP_1H_OPTIONAL
    assert evidence_value(result, "strategy_mode") == "daily_filter_4h_setup_1h_optional"
    assert evidence_value(result, "one_hour_confirmation_available") is False


def test_daily_only_rejects_four_hour_signal_timeframe():
    base = valid_breakout_input()
    setup_input = VolumeBreakoutInput(
        **{
            **base.__dict__,
            "strategy_mode": StrategyMode.DAILY_ONLY,
            "signal_timeframe": BarTimeframe.FOUR_HOUR,
        }
    )

    result = evaluate_volume_breakout(setup_input)

    assert result.status is SetupStatus.REJECTED
