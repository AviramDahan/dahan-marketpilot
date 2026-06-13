"""Timeframe and completed-bar contracts for setup evidence."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from math import isfinite


class StrategyMode(str, Enum):
    DAILY_ONLY = "daily_only"
    DAILY_FILTER_4H_SETUP = "daily_filter_4h_setup"
    DAILY_FILTER_4H_SETUP_1H_OPTIONAL = "daily_filter_4h_setup_1h_optional"


class BarTimeframe(str, Enum):
    DAILY = "daily"
    FOUR_HOUR = "four_hour"
    ONE_HOUR = "one_hour"

    @property
    def timing_mode(self) -> str:
        return {
            BarTimeframe.DAILY: "completed_daily_bar",
            BarTimeframe.FOUR_HOUR: "completed_four_hour_bar",
            BarTimeframe.ONE_HOUR: "completed_one_hour_bar",
        }[self]


class BarCompletionStatus(str, Enum):
    COMPLETE = "complete"
    INCOMPLETE = "incomplete"
    PARTIAL_SESSION = "partial_session"


class TimeframeReadinessStatus(str, Enum):
    READY = "ready"
    NOT_READY = "not_ready"
    OPTIONAL_MISSING = "optional_missing"


@dataclass(frozen=True)
class BarSessionMetadata:
    exchange_timezone: str = "America/New_York"
    regular_hours: bool = True
    partial_session: bool = False
    source_resolution: str = "daily"


@dataclass(frozen=True)
class CompletedBar:
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    timeframe: BarTimeframe = BarTimeframe.DAILY
    completion_status: BarCompletionStatus = BarCompletionStatus.COMPLETE
    session: BarSessionMetadata = BarSessionMetadata()

    @property
    def complete(self) -> bool:
        return self.completion_status is BarCompletionStatus.COMPLETE

    def valid_for_signal(self) -> bool:
        values = (self.open, self.high, self.low, self.close, self.volume)
        return (
            self.complete
            and self.session.regular_hours
            and not self.session.partial_session
            and all(isinstance(value, (int, float)) and isfinite(float(value)) for value in values)
            and self.high > 0
            and self.low > 0
            and self.close > 0
            and self.volume >= 0
        )


@dataclass(frozen=True)
class TimeframeReadiness:
    timeframe: BarTimeframe
    status: TimeframeReadinessStatus
    mandatory: bool
    reason: str | None = None

    @property
    def ready(self) -> bool:
        return self.status is TimeframeReadinessStatus.READY

    @property
    def rejects_signal(self) -> bool:
        return self.mandatory and not self.ready


def parse_strategy_mode(value: object) -> StrategyMode:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("strategy.mode must be one of the supported StrategyMode values.")
    normalized = value.strip()
    try:
        return StrategyMode(normalized)
    except ValueError as exc:
        allowed = ", ".join(mode.value for mode in StrategyMode)
        raise ValueError(f"strategy.mode must be one of: {allowed}.") from exc


def parse_bar_timeframe(value: object) -> BarTimeframe:
    if isinstance(value, BarTimeframe):
        return value
    if not isinstance(value, str) or not value.strip():
        raise ValueError("signal timeframe is required.")
    try:
        return BarTimeframe(value.strip())
    except ValueError as exc:
        allowed = ", ".join(timeframe.value for timeframe in BarTimeframe)
        raise ValueError(f"signal timeframe must be one of: {allowed}.") from exc


def timeframe_allowed_for_strategy_mode(strategy_mode: StrategyMode, timeframe: BarTimeframe) -> bool:
    if strategy_mode is StrategyMode.DAILY_ONLY:
        return timeframe is BarTimeframe.DAILY
    if strategy_mode is StrategyMode.DAILY_FILTER_4H_SETUP:
        return timeframe is BarTimeframe.FOUR_HOUR
    if strategy_mode is StrategyMode.DAILY_FILTER_4H_SETUP_1H_OPTIONAL:
        return timeframe in {BarTimeframe.FOUR_HOUR, BarTimeframe.ONE_HOUR}
    return False
