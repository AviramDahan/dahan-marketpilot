from datetime import datetime, timezone

from marketpilot.data_quality import DataQualityStatus
from marketpilot.indicators import IndicatorResult, ReadinessStatus
from marketpilot.regime import MarketRegime, RegimeResult
from marketpilot.setups.base import SetupRejectionReason, SetupStatus
from marketpilot.setups.volume_breakout import CompletedDailyBar, VolumeBreakoutInput, evaluate_volume_breakout
from marketpilot.symbol_data import SymbolData


def ready_indicator(name, value):
    return IndicatorResult(name=name, status=ReadinessStatus.READY, value=value, required_points=20, available_points=260)


def indicators(ema20=100.0, atr14=4.0):
    return {
        "EMA20": ready_indicator("EMA20", ema20),
        "ATR14": ready_indicator("ATR14", atr14),
    }


def breakout_bars(signal_close=100.5, signal_high=101.0, signal_volume=1600000, complete=True):
    prior = tuple(
        CompletedDailyBar(
            time=datetime(2026, 6, 1 + index, tzinfo=timezone.utc),
            open=96.0 + index * 0.1,
            high=98.0 + (index % 3) * 0.5,
            low=95.0 + index * 0.1,
            close=97.0 + index * 0.1,
            volume=1000000,
        )
        for index in range(20)
    )
    signal = CompletedDailyBar(
        time=datetime(2026, 6, 21, tzinfo=timezone.utc),
        open=99.0,
        high=signal_high,
        low=98.5,
        close=signal_close,
        volume=signal_volume,
        complete=complete,
    )
    return prior + (signal,)


def valid_input(**overrides):
    active_indicators = overrides.pop("indicator_values", indicators())
    symbol_data = SymbolData("MSFT", "Technology", DataQualityStatus.ACCEPTED, active_indicators)
    setup_input = VolumeBreakoutInput(
        symbol_data=symbol_data,
        regime=RegimeResult(MarketRegime.RISK_ON, True, True, None, ("supportive",)),
        bars=breakout_bars(),
        indicators=active_indicators,
        average_volume=1000000,
        average_dollar_volume=30000000,
        atr_pct=4.0,
        projected_target=110.0,
    )
    return VolumeBreakoutInput(**{**setup_input.__dict__, **overrides})


def evidence_value(result, name):
    return next(item.value for item in result.evidence if item.name == name)


def test_detects_valid_volume_breakout_on_completed_close_and_volume():
    result = evaluate_volume_breakout(valid_input())

    assert result.status is SetupStatus.VALID
    assert result.valid is True
    assert result.rejection_reasons == ()
    assert evidence_value(result, "prior_resistance") == 99.0
    assert evidence_value(result, "buffered_resistance") == 99.2475
    assert evidence_value(result, "breakout_close") == 100.5
    assert evidence_value(result, "volume_ratio") == 1.6
    assert result.timing.uses_completed_daily_bar is True
    assert result.timing.intrabar_valid is False


def test_rejects_intraday_high_without_completed_close_breakout():
    setup_input = valid_input(bars=breakout_bars(signal_close=99.0, signal_high=105.0))
    result = evaluate_volume_breakout(setup_input)

    assert result.status is SetupStatus.REJECTED
    assert SetupRejectionReason.BREAKOUT_NOT_CONFIRMED in result.rejection_reasons


def test_current_bar_high_does_not_affect_prior_resistance():
    setup_input = valid_input(bars=breakout_bars(signal_close=100.5, signal_high=500.0))
    result = evaluate_volume_breakout(setup_input)

    assert result.status is SetupStatus.VALID
    assert evidence_value(result, "prior_resistance") == 99.0


def test_rejects_weak_breakout_bar_volume():
    setup_input = valid_input(bars=breakout_bars(signal_volume=1200000))
    result = evaluate_volume_breakout(setup_input)

    assert result.status is SetupStatus.REJECTED
    assert SetupRejectionReason.VOLUME_CONFIRMATION_WEAK in result.rejection_reasons
