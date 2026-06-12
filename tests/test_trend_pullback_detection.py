from datetime import datetime, timezone

from marketpilot.data_quality import DataQualityStatus
from marketpilot.indicators import IndicatorResult, ReadinessStatus
from marketpilot.regime import MarketRegime, RegimeResult
from marketpilot.setups.base import SetupRejectionReason, SetupStatus
from marketpilot.setups.trend_pullback import CompletedDailyBar, TrendPullbackInput, evaluate_trend_pullback
from marketpilot.symbol_data import SymbolData


def ready_indicator(name, value):
    return IndicatorResult(name=name, status=ReadinessStatus.READY, value=value, required_points=20, available_points=260)


def indicators(ema20=100.0, ema50=98.0, ema200=80.0):
    return {
        "EMA20": ready_indicator("EMA20", ema20),
        "EMA50": ready_indicator("EMA50", ema50),
        "EMA200": ready_indicator("EMA200", ema200),
        "RSI14": ready_indicator("RSI14", 55.0),
        "MACD": ready_indicator("MACD", 1.5),
        "ATR14": ready_indicator("ATR14", 3.0),
    }


def bars(closes):
    result = []
    for index, close in enumerate(closes):
        result.append(
            CompletedDailyBar(
                time=datetime(2026, 6, 1 + index, tzinfo=timezone.utc),
                open=close + 0.3,
                high=close + 1.0,
                low=close - 1.0,
                close=close,
                volume=900000 if index < len(closes) - 1 else 1200000,
            )
        )
    return tuple(result)


def valid_input(closes=(103.0, 101.0, 99.8, 100.7, 102.0), indicator_values=None):
    active_indicators = indicator_values or indicators()
    symbol_data = SymbolData("MSFT", "Technology", DataQualityStatus.ACCEPTED, active_indicators)
    return TrendPullbackInput(
        symbol_data=symbol_data,
        regime=RegimeResult(MarketRegime.RISK_ON, True, True, None, ("supportive",)),
        bars=bars(closes),
        indicators=active_indicators,
        average_volume=1000000,
        atr_pct=4.0,
        reward_risk_proxy=2.0,
    )


def test_detects_valid_pullback_toward_ema20():
    result = evaluate_trend_pullback(valid_input())

    assert result.status is SetupStatus.VALID
    assert result.valid is True
    assert result.rejection_reasons == ()
    assert any(item.name == "ema20_distance_pct" and item.passed for item in result.evidence)
    assert result.timing.uses_completed_daily_bar is True


def test_detects_valid_pullback_toward_ema50():
    result = evaluate_trend_pullback(
            valid_input(
            closes=(104.0, 102.0, 100.0, 99.2, 101.0),
            indicator_values=indicators(ema20=106.0, ema50=99.0, ema200=80.0),
        )
    )

    assert result.status is SetupStatus.VALID
    assert any(item.name == "ema50_distance_pct" and item.passed for item in result.evidence)


def test_recovery_requires_close_above_prior_completed_bar_high():
    setup_input = valid_input(closes=(103.0, 101.0, 99.8, 101.2, 101.8))
    result = evaluate_trend_pullback(setup_input)

    assert result.status is SetupStatus.REJECTED
    assert SetupRejectionReason.RECOVERY_NOT_CONFIRMED in result.rejection_reasons


def test_incomplete_current_bar_is_rejected_not_treated_as_intrabar_signal():
    setup_input = valid_input()
    incomplete = setup_input.bars[:-1] + (CompletedDailyBar(**{**setup_input.bars[-1].__dict__, "complete": False}),)
    result = evaluate_trend_pullback(TrendPullbackInput(**{**setup_input.__dict__, "bars": incomplete}))

    assert result.status is SetupStatus.REJECTED
    assert SetupRejectionReason.INCOMPLETE_COMPLETED_BAR_DATA in result.rejection_reasons
    assert result.timing.intrabar_valid is False
