from math import nan

from marketpilot.indicators import (
    ReadinessStatus,
    atr,
    average,
    distance_from_high,
    ema,
    macd,
    relative_strength,
    roc,
    rsi,
)


SERIES = [float(index) for index in range(1, 301)]


def test_ema_rsi_macd_roc_are_ready_with_enough_history():
    assert ema(SERIES, 8).ready is True
    assert rsi(SERIES, 14).ready is True
    assert macd(SERIES).ready is True
    assert roc(SERIES, 20).ready is True
    assert roc(SERIES, 60).ready is True


def test_atr_average_volume_dollar_volume_relative_strength_and_high_distance():
    highs = [value + 1 for value in SERIES]
    lows = [value - 1 for value in SERIES]

    assert atr(highs, lows, SERIES, 14).status is ReadinessStatus.READY
    assert average(SERIES, 20, "AVG_VOLUME20").status is ReadinessStatus.READY
    assert average([value * 1000 for value in SERIES], 50, "AVG_DOLLAR_VOLUME50").ready is True
    assert relative_strength(SERIES, [value - 0.5 for value in SERIES], 20).ready is True
    assert relative_strength(SERIES, [value - 0.5 for value in SERIES], 60).ready is True
    assert distance_from_high(SERIES, 252).ready is True


def test_readiness_status_is_exposed_before_values_are_usable():
    result = ema([1.0, 2.0], 8)

    assert result.status is ReadinessStatus.NOT_READY
    assert result.ready is False
    assert result.value is None
    assert result.required_points == 8


def test_invalid_nan_inputs_are_rejected():
    result = rsi([1.0, 2.0, nan] + [3.0] * 20)

    assert result.status is ReadinessStatus.INVALID
    assert result.ready is False


def test_indicator_module_does_not_expose_strategy_classifications():
    import marketpilot.indicators as indicators

    text = indicators.__file__
    assert "BUY" not in text
    assert "WATCH" not in text
    assert "AVOID" not in text

