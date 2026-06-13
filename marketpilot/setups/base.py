"""Shared setup result contracts with no trading side effects."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from marketpilot.timeframes import BarCompletionStatus, BarTimeframe, StrategyMode


class SetupStatus(str, Enum):
    VALID = "valid"
    REJECTED = "rejected"


class SetupRejectionReason(str, Enum):
    RISK_OFF = "risk_off"
    DATA_NOT_READY = "data_not_ready"
    EMA50_BREAK = "ema50_break"
    EXCESSIVE_ATR = "excessive_atr"
    WEAK_REWARD_RISK = "weak_reward_risk"
    INCOMPLETE_COMPLETED_BAR_DATA = "incomplete_completed_bar_data"
    PULLBACK_TOO_SHORT = "pullback_too_short"
    PULLBACK_TOO_LONG = "pullback_too_long"
    NO_EMA_PROXIMITY = "no_ema_proximity"
    BROKEN_TREND = "broken_trend"
    RECOVERY_NOT_CONFIRMED = "recovery_not_confirmed"
    RECOVERY_VOLUME_WEAK = "recovery_volume_weak"
    EARNINGS_SOURCE_UNVERIFIED = "earnings_source_unverified"
    INVALID_PRIOR_RESISTANCE = "invalid_prior_resistance"
    BREAKOUT_NOT_CONFIRMED = "breakout_not_confirmed"
    VOLUME_CONFIRMATION_WEAK = "volume_confirmation_weak"
    EMA20_EXTENSION_EXCESSIVE = "ema20_extension_excessive"
    INSUFFICIENT_DOLLAR_VOLUME = "insufficient_dollar_volume"
    EARNINGS_RISK_CONFLICT = "earnings_risk_conflict"
    PORTFOLIO_CONFLICT = "portfolio_conflict"
    WEAK_SPY_RELATIVE_STRENGTH = "weak_spy_relative_strength"
    EXCESSIVE_52_WEEK_HIGH_DISTANCE = "excessive_52_week_high_distance"


@dataclass(frozen=True)
class SetupTiming:
    signal_time: datetime
    timing_mode: str = "completed_daily_bar"
    uses_completed_daily_bar: bool = True
    intrabar_valid: bool = False
    strategy_mode: StrategyMode = StrategyMode.DAILY_ONLY
    signal_timeframe: BarTimeframe = BarTimeframe.DAILY
    bar_start: datetime | None = None
    bar_end: datetime | None = None
    completion_status: BarCompletionStatus = BarCompletionStatus.COMPLETE
    exchange_timezone: str = "America/New_York"
    regular_hours: bool = True
    partial_session: bool = False
    freshness: str = "fresh"
    source_resolution: str = "daily"
    later_valid_execution_required: bool = True


@dataclass(frozen=True)
class NumericEvidence:
    name: str
    value: float | int | str | bool | None
    threshold: float | int | str | bool | None = None
    passed: bool | None = None


@dataclass(frozen=True)
class SetupResult:
    setup_name: str
    symbol: str
    status: SetupStatus
    timing: SetupTiming
    evidence: tuple[NumericEvidence, ...] = field(default_factory=tuple)
    rejection_reasons: tuple[SetupRejectionReason, ...] = field(default_factory=tuple)
    explanation: tuple[str, ...] = field(default_factory=tuple)

    @property
    def valid(self) -> bool:
        return self.status is SetupStatus.VALID
