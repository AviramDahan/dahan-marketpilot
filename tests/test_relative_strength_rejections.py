from marketpilot.regime import MarketRegime, RegimeResult
from marketpilot.setups.base import SetupRejectionReason, SetupStatus
from marketpilot.setups.relative_strength import RelativeStrengthInput, evaluate_relative_strength_leader
from test_relative_strength_detection import bars, valid_input


def reject_reason(setup_input):
    return evaluate_relative_strength_leader(setup_input).rejection_reasons


def test_rejects_weak_spy_rs20_or_rs60():
    result = evaluate_relative_strength_leader(valid_input(symbol_returns=[0.0] * 70, spy_returns=[0.01] * 70))

    assert result.status is SetupStatus.REJECTED
    assert SetupRejectionReason.WEAK_SPY_RELATIVE_STRENGTH in result.rejection_reasons


def test_rejects_risk_off():
    setup_input = valid_input(regime=RegimeResult(MarketRegime.RISK_OFF, False, True, None, ("risk off",)))

    assert SetupRejectionReason.RISK_OFF in reject_reason(setup_input)


def test_rejects_stale_symbol_data():
    setup_input = valid_input(symbol_data_stale=True)

    assert SetupRejectionReason.DATA_NOT_READY in reject_reason(setup_input)


def test_rejects_bad_structure_liquidity_atr_extension_and_high_distance():
    setup_input = valid_input(average_dollar_volume=1000, atr_pct=12.0, ema20_extension_pct=20.0)
    result = evaluate_relative_strength_leader(setup_input)

    assert SetupRejectionReason.INSUFFICIENT_DOLLAR_VOLUME in result.rejection_reasons
    assert SetupRejectionReason.EXCESSIVE_ATR in result.rejection_reasons
    assert SetupRejectionReason.EMA20_EXTENSION_EXCESSIVE in result.rejection_reasons

    distant = tuple(RelativeStrengthInput(**{**valid_input().__dict__, "bars": bars()}).bars)
    # Force a latest close far below the prior high.
    lowered = distant[:-1] + (distant[-1].__class__(**{**distant[-1].__dict__, "close": 70.0}),)
    result = evaluate_relative_strength_leader(valid_input(bars=lowered))

    assert SetupRejectionReason.EXCESSIVE_52_WEEK_HIGH_DISTANCE in result.rejection_reasons


def test_rejects_incomplete_bar():
    active_bars = valid_input().bars
    incomplete = active_bars[:-1] + (active_bars[-1].__class__(**{**active_bars[-1].__dict__, "complete": False}),)
    result = evaluate_relative_strength_leader(valid_input(bars=incomplete))

    assert result.status is SetupStatus.REJECTED
    assert SetupRejectionReason.INCOMPLETE_COMPLETED_BAR_DATA in result.rejection_reasons
