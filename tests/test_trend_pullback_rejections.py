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
    return tuple(
        CompletedDailyBar(
            time=datetime(2026, 6, 1 + index, tzinfo=timezone.utc),
            open=close + 0.3,
            high=close + 1.0,
            low=close - 1.0,
            close=close,
            volume=900000 if index < len(closes) - 1 else 1200000,
        )
        for index, close in enumerate(closes)
    )


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


def assert_rejected(setup_input, reason):
    result = evaluate_trend_pullback(setup_input)
    assert result.status is SetupStatus.REJECTED
    assert reason in result.rejection_reasons
    return result


def test_rejects_risk_off_regime():
    setup_input = valid_input()
    risk_off = RegimeResult(MarketRegime.RISK_OFF, False, True, MarketRegime.NEUTRAL, ("defensive",))

    assert_rejected(TrendPullbackInput(**{**setup_input.__dict__, "regime": risk_off}), SetupRejectionReason.RISK_OFF)


def test_rejects_unready_or_rejected_symbol_data_and_missing_indicators():
    setup_input = valid_input()
    rejected_symbol = SymbolData("MSFT", "Technology", DataQualityStatus.REJECTED, setup_input.indicators)
    assert_rejected(TrendPullbackInput(**{**setup_input.__dict__, "symbol_data": rejected_symbol}), SetupRejectionReason.DATA_NOT_READY)

    missing = dict(setup_input.indicators)
    missing.pop("MACD")
    missing_symbol = SymbolData("MSFT", "Technology", DataQualityStatus.ACCEPTED, missing)
    assert_rejected(
        TrendPullbackInput(**{**setup_input.__dict__, "symbol_data": missing_symbol, "indicators": missing}),
        SetupRejectionReason.DATA_NOT_READY,
    )


def test_rejects_invalid_indicator_value():
    setup_input = valid_input()
    invalid = dict(setup_input.indicators)
    invalid["RSI14"] = IndicatorResult("RSI14", ReadinessStatus.INVALID)
    symbol_data = SymbolData("MSFT", "Technology", DataQualityStatus.ACCEPTED, invalid)

    assert_rejected(TrendPullbackInput(**{**setup_input.__dict__, "symbol_data": symbol_data, "indicators": invalid}), SetupRejectionReason.DATA_NOT_READY)


def test_rejects_close_below_ema50_and_broken_trend():
    assert_rejected(valid_input(closes=(103.0, 101.0, 97.5, 99.0, 101.0)), SetupRejectionReason.EMA50_BREAK)
    assert_rejected(valid_input(indicator_values=indicators(ema20=95, ema50=98, ema200=90)), SetupRejectionReason.BROKEN_TREND)


def test_rejects_pullback_window_too_short_or_too_long():
    assert_rejected(valid_input(closes=(101.0, 103.0)), SetupRejectionReason.PULLBACK_TOO_SHORT)
    assert_rejected(valid_input(closes=(112, 111, 110, 109, 108, 107, 106, 105, 104, 103, 102, 104)), SetupRejectionReason.PULLBACK_TOO_LONG)


def test_rejects_excessive_atr_and_weak_reward_risk_proxy():
    setup_input = valid_input()
    assert_rejected(TrendPullbackInput(**{**setup_input.__dict__, "atr_pct": 9.0}), SetupRejectionReason.EXCESSIVE_ATR)
    assert_rejected(TrendPullbackInput(**{**setup_input.__dict__, "reward_risk_proxy": 1.0}), SetupRejectionReason.WEAK_REWARD_RISK)


def test_rejects_failed_recovery_volume_and_no_ema_proximity():
    setup_input = valid_input()
    assert_rejected(TrendPullbackInput(**{**setup_input.__dict__, "average_volume": 2000000}), SetupRejectionReason.RECOVERY_VOLUME_WEAK)
    assert_rejected(valid_input(closes=(120.0, 118.0, 116.0, 117.0, 119.0)), SetupRejectionReason.NO_EMA_PROXIMITY)


def test_earnings_risk_is_deferred_not_fabricated_rejection():
    result = evaluate_trend_pullback(valid_input())

    assert SetupRejectionReason.EARNINGS_SOURCE_UNVERIFIED not in result.rejection_reasons
    assert any(item.name == "earnings_source_verified" and item.value is False for item in result.evidence)
