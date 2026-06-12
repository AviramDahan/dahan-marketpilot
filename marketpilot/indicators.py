"""Deterministic offline indicator helpers for Phase 2 readiness checks."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite
from statistics import fmean
from typing import Sequence


class ReadinessStatus(str, Enum):
    READY = "ready"
    NOT_READY = "not_ready"
    INVALID = "invalid"


@dataclass(frozen=True)
class IndicatorResult:
    name: str
    status: ReadinessStatus
    value: float | None = None
    required_points: int = 0
    available_points: int = 0
    reason: str | None = None

    @property
    def ready(self) -> bool:
        return self.status is ReadinessStatus.READY


def ema(values: Sequence[float], period: int, name: str | None = None) -> IndicatorResult:
    checked = _validate_series(values, period)
    indicator_name = name or f"EMA{period}"
    if isinstance(checked, IndicatorResult):
        return _rename(checked, indicator_name)
    multiplier = 2 / (period + 1)
    current = fmean(checked[:period])
    for value in checked[period:]:
        current = (value - current) * multiplier + current
    return IndicatorResult(indicator_name, ReadinessStatus.READY, current, period, len(checked))


def rsi(values: Sequence[float], period: int = 14) -> IndicatorResult:
    checked = _validate_series(values, period + 1)
    if isinstance(checked, IndicatorResult):
        return _rename(checked, f"RSI{period}")
    gains: list[float] = []
    losses: list[float] = []
    for previous, current in zip(checked[-period - 1 : -1], checked[-period:]):
        change = current - previous
        gains.append(max(change, 0))
        losses.append(abs(min(change, 0)))
    average_gain = fmean(gains)
    average_loss = fmean(losses)
    if average_loss == 0:
        value = 100.0
    else:
        value = 100 - (100 / (1 + (average_gain / average_loss)))
    return IndicatorResult(f"RSI{period}", ReadinessStatus.READY, value, period + 1, len(checked))


def macd(values: Sequence[float], fast: int = 12, slow: int = 26, signal: int = 9) -> IndicatorResult:
    required = slow + signal
    checked = _validate_series(values, required)
    if isinstance(checked, IndicatorResult):
        return _rename(checked, "MACD")
    fast_value = ema(checked, fast).value
    slow_value = ema(checked, slow).value
    if fast_value is None or slow_value is None:
        return IndicatorResult("MACD", ReadinessStatus.NOT_READY, required_points=required, available_points=len(checked))
    return IndicatorResult("MACD", ReadinessStatus.READY, fast_value - slow_value, required, len(checked))


def roc(values: Sequence[float], period: int) -> IndicatorResult:
    checked = _validate_series(values, period + 1)
    if isinstance(checked, IndicatorResult):
        return _rename(checked, f"ROC{period}")
    base = checked[-period - 1]
    if base == 0:
        return IndicatorResult(f"ROC{period}", ReadinessStatus.INVALID, required_points=period + 1, available_points=len(checked), reason="zero_base")
    value = ((checked[-1] - base) / base) * 100
    return IndicatorResult(f"ROC{period}", ReadinessStatus.READY, value, period + 1, len(checked))


def atr(highs: Sequence[float], lows: Sequence[float], closes: Sequence[float], period: int = 14) -> IndicatorResult:
    if not (len(highs) == len(lows) == len(closes)):
        return IndicatorResult("ATR14", ReadinessStatus.INVALID, required_points=period + 1, reason="length_mismatch")
    high_values = _validate_series(highs, period + 1)
    low_values = _validate_series(lows, period + 1)
    close_values = _validate_series(closes, period + 1)
    if isinstance(high_values, IndicatorResult) or isinstance(low_values, IndicatorResult) or isinstance(close_values, IndicatorResult):
        return IndicatorResult("ATR14", ReadinessStatus.INVALID, required_points=period + 1, available_points=len(closes), reason="invalid_series")
    ranges = []
    for index in range(1, len(close_values)):
        ranges.append(
            max(
                high_values[index] - low_values[index],
                abs(high_values[index] - close_values[index - 1]),
                abs(low_values[index] - close_values[index - 1]),
            )
        )
    return IndicatorResult("ATR14", ReadinessStatus.READY, fmean(ranges[-period:]), period + 1, len(close_values))


def average(values: Sequence[float], period: int, name: str) -> IndicatorResult:
    checked = _validate_series(values, period)
    if isinstance(checked, IndicatorResult):
        return _rename(checked, name)
    return IndicatorResult(name, ReadinessStatus.READY, fmean(checked[-period:]), period, len(checked))


def relative_strength(symbol_returns: Sequence[float], benchmark_returns: Sequence[float], period: int) -> IndicatorResult:
    symbol = _validate_series(symbol_returns, period)
    benchmark = _validate_series(benchmark_returns, period)
    name = f"RS{period}"
    if isinstance(symbol, IndicatorResult) or isinstance(benchmark, IndicatorResult):
        return IndicatorResult(name, ReadinessStatus.NOT_READY, required_points=period, available_points=min(len(symbol_returns), len(benchmark_returns)))
    value = fmean(symbol[-period:]) - fmean(benchmark[-period:])
    return IndicatorResult(name, ReadinessStatus.READY, value, period, min(len(symbol), len(benchmark)))


def distance_from_high(values: Sequence[float], period: int = 252) -> IndicatorResult:
    checked = _validate_series(values, period)
    if isinstance(checked, IndicatorResult):
        return _rename(checked, "52W_HIGH_DISTANCE")
    highest = max(checked[-period:])
    if highest == 0:
        return IndicatorResult("52W_HIGH_DISTANCE", ReadinessStatus.INVALID, required_points=period, available_points=len(checked), reason="zero_high")
    value = ((checked[-1] - highest) / highest) * 100
    return IndicatorResult("52W_HIGH_DISTANCE", ReadinessStatus.READY, value, period, len(checked))


def _validate_series(values: Sequence[float], required: int) -> list[float] | IndicatorResult:
    numeric = list(values)
    if len(numeric) < required:
        return IndicatorResult("", ReadinessStatus.NOT_READY, required_points=required, available_points=len(numeric), reason="insufficient_history")
    if any(not isinstance(value, (int, float)) or not isfinite(float(value)) for value in numeric):
        return IndicatorResult("", ReadinessStatus.INVALID, required_points=required, available_points=len(numeric), reason="invalid_numeric")
    return [float(value) for value in numeric]


def _rename(result: IndicatorResult, name: str) -> IndicatorResult:
    return IndicatorResult(
        name=name,
        status=result.status,
        value=result.value,
        required_points=result.required_points,
        available_points=result.available_points,
        reason=result.reason,
    )

