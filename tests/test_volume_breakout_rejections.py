from dataclasses import fields
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


def breakout_bars(signal_close=105.0, signal_high=106.0, signal_volume=1600000, complete=True, count=20):
    prior = tuple(
        CompletedDailyBar(
            time=datetime(2026, 6, 1 + index, tzinfo=timezone.utc),
            open=98.0,
            high=100.0 if index == count - 1 else 99.0,
            low=97.0,
            close=98.5,
            volume=1000000,
        )
        for index in range(count)
    )
    signal = CompletedDailyBar(
        time=datetime(2026, 6, 21, tzinfo=timezone.utc),
        open=101.0,
        high=signal_high,
        low=100.5,
        close=signal_close,
        volume=signal_volume,
        complete=complete,
    )
    return prior + (signal,)


def valid_input(**overrides):
    active_indicators = overrides.pop("indicator_values", indicators())
    symbol_data = overrides.pop("symbol_data", SymbolData("MSFT", "Technology", DataQualityStatus.ACCEPTED, active_indicators))
    setup_input = VolumeBreakoutInput(
        symbol_data=symbol_data,
        regime=RegimeResult(MarketRegime.RISK_ON, True, True, None, ("supportive",)),
        bars=breakout_bars(),
        indicators=active_indicators,
        average_volume=1000000,
        average_dollar_volume=30000000,
        atr_pct=4.0,
        projected_target=115.0,
    )
    return VolumeBreakoutInput(**{**setup_input.__dict__, **overrides})


def assert_rejected(setup_input, reason):
    result = evaluate_volume_breakout(setup_input)
    assert result.status is SetupStatus.REJECTED
    assert reason in result.rejection_reasons
    return result


def evidence_item(result, name):
    return next(item for item in result.evidence if item.name == name)


def test_rejects_risk_off_or_future_entries_blocked():
    setup_input = valid_input()
    risk_off = RegimeResult(MarketRegime.RISK_OFF, False, True, MarketRegime.NEUTRAL, ("defensive",))
    blocked_neutral = RegimeResult(MarketRegime.NEUTRAL, False, True, MarketRegime.RISK_ON, ("unready_benchmark",))

    assert_rejected(VolumeBreakoutInput(**{**setup_input.__dict__, "regime": risk_off}), SetupRejectionReason.RISK_OFF)
    assert_rejected(VolumeBreakoutInput(**{**setup_input.__dict__, "regime": blocked_neutral}), SetupRejectionReason.RISK_OFF)


def test_rejects_unready_data_missing_indicators_invalid_values_and_incomplete_bars():
    setup_input = valid_input()
    rejected_symbol = SymbolData("MSFT", "Technology", DataQualityStatus.REJECTED, setup_input.indicators)
    assert_rejected(
        VolumeBreakoutInput(**{**setup_input.__dict__, "symbol_data": rejected_symbol}),
        SetupRejectionReason.DATA_NOT_READY,
    )

    missing = dict(setup_input.indicators)
    missing.pop("EMA20")
    missing_symbol = SymbolData("MSFT", "Technology", DataQualityStatus.ACCEPTED, missing)
    assert_rejected(
        VolumeBreakoutInput(**{**setup_input.__dict__, "symbol_data": missing_symbol, "indicators": missing}),
        SetupRejectionReason.DATA_NOT_READY,
    )

    invalid = dict(setup_input.indicators)
    invalid["ATR14"] = IndicatorResult("ATR14", ReadinessStatus.INVALID)
    invalid_symbol = SymbolData("MSFT", "Technology", DataQualityStatus.ACCEPTED, invalid)
    assert_rejected(
        VolumeBreakoutInput(**{**setup_input.__dict__, "symbol_data": invalid_symbol, "indicators": invalid}),
        SetupRejectionReason.DATA_NOT_READY,
    )

    incomplete = setup_input.bars[:-1] + (CompletedDailyBar(**{**setup_input.bars[-1].__dict__, "complete": False}),)
    assert_rejected(
        VolumeBreakoutInput(**{**setup_input.__dict__, "bars": incomplete}),
        SetupRejectionReason.INCOMPLETE_COMPLETED_BAR_DATA,
    )
    assert_rejected(
        VolumeBreakoutInput(**{**setup_input.__dict__, "bars": breakout_bars(count=19)}),
        SetupRejectionReason.INCOMPLETE_COMPLETED_BAR_DATA,
    )


def test_rejects_stale_symbol_data_readiness():
    result = assert_rejected(valid_input(symbol_data_stale=True), SetupRejectionReason.DATA_NOT_READY)

    stale_evidence = evidence_item(result, "symbol_data_stale")
    assert stale_evidence.value is True
    assert stale_evidence.passed is False


def test_rejects_excessive_atr_ema20_extension_and_insufficient_dollar_volume():
    setup_input = valid_input()

    atr_result = assert_rejected(VolumeBreakoutInput(**{**setup_input.__dict__, "atr_pct": 9.0}), SetupRejectionReason.EXCESSIVE_ATR)
    assert evidence_item(atr_result, "atr_pct").passed is False

    extended = valid_input(indicator_values=indicators(ema20=90.0, atr14=4.0))
    extension_result = assert_rejected(extended, SetupRejectionReason.EMA20_EXTENSION_EXCESSIVE)
    assert evidence_item(extension_result, "ema20_extension_pct").passed is False

    dollar_result = assert_rejected(
        VolumeBreakoutInput(**{**setup_input.__dict__, "average_dollar_volume": 10000000}),
        SetupRejectionReason.INSUFFICIENT_DOLLAR_VOLUME,
    )
    assert evidence_item(dollar_result, "average_dollar_volume").passed is False


def test_calculates_reward_risk_proxy_from_projected_target_and_resistance():
    result = evaluate_volume_breakout(valid_input(projected_target=115.0))

    assert result.status is SetupStatus.VALID
    assert evidence_item(result, "risk_per_share_proxy").value == 5.0
    assert evidence_item(result, "reward_per_share_proxy").value == 10.0
    assert evidence_item(result, "reward_risk_proxy").value == 2.0

    rejected = assert_rejected(valid_input(projected_target=107.0), SetupRejectionReason.WEAK_REWARD_RISK)
    assert evidence_item(rejected, "reward_risk_proxy").value == 0.4


def test_volume_breakout_input_does_not_accept_precomputed_reward_risk_proxy():
    assert "projected_target" in {field.name for field in fields(VolumeBreakoutInput)}
    assert "reward_risk_proxy" not in {field.name for field in fields(VolumeBreakoutInput)}


def test_earnings_source_unverified_is_evidence_not_rejection_without_verified_conflict():
    result = evaluate_volume_breakout(valid_input())

    assert result.status is SetupStatus.VALID
    assert SetupRejectionReason.EARNINGS_SOURCE_UNVERIFIED not in result.rejection_reasons
    assert evidence_item(result, "earnings_source_verified").value is False

    conflict = assert_rejected(
        valid_input(earnings_source_verified=True, earnings_risk_conflict=True),
        SetupRejectionReason.EARNINGS_RISK_CONFLICT,
    )
    assert evidence_item(conflict, "earnings_risk_conflict").passed is False


def test_portfolio_conflict_uses_explicit_input_only():
    result = evaluate_volume_breakout(valid_input(portfolio_conflict=None))

    assert result.status is SetupStatus.VALID
    assert evidence_item(result, "portfolio_conflict").value is None

    conflict = assert_rejected(valid_input(portfolio_conflict=True), SetupRejectionReason.PORTFOLIO_CONFLICT)
    assert evidence_item(conflict, "portfolio_conflict").passed is False
