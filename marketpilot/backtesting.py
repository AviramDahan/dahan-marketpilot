"""Backtesting contracts and deterministic safety checks."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Mapping, Sequence

import yaml

from marketpilot.timeframes import BarTimeframe, StrategyMode, parse_bar_timeframe, parse_strategy_mode


class BacktestRunStatus(str, Enum):
    NOT_RUN = "not_run"
    REAL_QUANTCONNECT = "real_quantconnect"
    FIXTURE = "fixture"
    SCHEMA = "schema"
    EXAMPLE = "example"


class FillTiming(str, Enum):
    NEXT_VALID_OPEN = "next_valid_open"
    NEXT_VALID_PRICE = "next_valid_price"


class FillModel(str, Enum):
    CONSERVATIVE_NEXT_BAR = "conservative_next_bar"


class AmbiguityStatus(str, Enum):
    NONE = "none"
    SAME_BAR_AMBIGUOUS = "same_bar_ambiguous"


class HarnessCheckStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"


@dataclass(frozen=True)
class BacktestExecutionConfig:
    paper_trading_only: bool
    official_authority: str
    local_harness_enabled: bool
    fee_per_order_usd: float
    slippage_bps: float
    fill_model: FillModel
    fill_timing: FillTiming
    partial_fills: str
    disabled_behaviors: Mapping[str, bool]

    @property
    def conservative_assumptions_present(self) -> bool:
        return (
            self.paper_trading_only
            and self.official_authority == "quantconnect_cloud_lean"
            and self.local_harness_enabled
            and self.fee_per_order_usd >= 0
            and self.slippage_bps >= 0
            and self.fill_model is FillModel.CONSERVATIVE_NEXT_BAR
            and self.fill_timing in {FillTiming.NEXT_VALID_OPEN, FillTiming.NEXT_VALID_PRICE}
            and all(value is False for value in self.disabled_behaviors.values())
        )


@dataclass(frozen=True)
class BacktestEvent:
    status: BacktestRunStatus
    source: str
    message: str
    command: str | None = None
    metrics: Mapping[str, float] = field(default_factory=dict)

    @property
    def contains_performance_results(self) -> bool:
        return bool(self.metrics)


@dataclass(frozen=True)
class NoLookaheadValidation:
    status: HarnessCheckStatus
    reasons: tuple[str, ...]
    signal_time: datetime
    fill_time: datetime
    strategy_mode: StrategyMode
    signal_timeframe: BarTimeframe

    @property
    def passed(self) -> bool:
        return self.status is HarnessCheckStatus.PASS


@dataclass(frozen=True)
class SameBarAmbiguity:
    status: AmbiguityStatus
    reason: str | None = None

    @property
    def fail_closed(self) -> bool:
        return self.status is AmbiguityStatus.SAME_BAR_AMBIGUOUS


DEFAULT_BACKTESTING_CONFIG = Path(__file__).resolve().parents[1] / "config" / "backtesting.yaml"


def load_backtesting_config(path: str | Path = DEFAULT_BACKTESTING_CONFIG) -> BacktestExecutionConfig:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("backtesting configuration must be a mapping.")

    config = BacktestExecutionConfig(
        paper_trading_only=bool(data.get("paper_trading_only")),
        official_authority=str(data.get("official_authority", "")),
        local_harness_enabled=bool(data.get("local_harness_enabled")),
        fee_per_order_usd=float(data.get("fee_per_order_usd", -1)),
        slippage_bps=float(data.get("slippage_bps", -1)),
        fill_model=FillModel(str(data.get("fill_model", ""))),
        fill_timing=FillTiming(str(data.get("fill_timing", ""))),
        partial_fills=str(data.get("partial_fills", "")),
        disabled_behaviors=dict(data.get("disabled_behaviors") or {}),
    )
    if not config.conservative_assumptions_present:
        raise ValueError("backtesting configuration must fail closed with conservative assumptions.")
    return config


def validate_no_lookahead(
    *,
    signal_time: datetime,
    fill_time: datetime,
    available_bar_times: Sequence[datetime],
    current_bar_time: datetime | None = None,
    stale_data: bool = False,
    strategy_mode: StrategyMode | str = StrategyMode.DAILY_ONLY,
    signal_timeframe: BarTimeframe | str = BarTimeframe.DAILY,
) -> NoLookaheadValidation:
    mode = parse_strategy_mode(strategy_mode.value if isinstance(strategy_mode, StrategyMode) else strategy_mode)
    timeframe = parse_bar_timeframe(signal_timeframe)
    reasons: list[str] = []
    available = set(available_bar_times)

    if stale_data:
        reasons.append("stale_data")
    if signal_time not in available:
        reasons.append("signal_bar_not_available")
    if current_bar_time is not None and signal_time >= current_bar_time:
        reasons.append("current_bar_excluded")
    if fill_time <= signal_time:
        reasons.append("fill_must_be_after_signal_bar")
    if not all(bar_time <= signal_time for bar_time in available):
        reasons.append("future_bar_detected")
    if not _timeframe_allowed_for_backtest_mode(mode, timeframe):
        reasons.append("strategy_mode_timeframe_mismatch")

    status = HarnessCheckStatus.FAIL if reasons else HarnessCheckStatus.PASS
    return NoLookaheadValidation(
        status=status,
        reasons=tuple(reasons),
        signal_time=signal_time,
        fill_time=fill_time,
        strategy_mode=mode,
        signal_timeframe=timeframe,
    )


def classify_same_bar_ambiguity(entry_bar_time: datetime, exit_bar_time: datetime) -> SameBarAmbiguity:
    if entry_bar_time == exit_bar_time:
        return SameBarAmbiguity(AmbiguityStatus.SAME_BAR_AMBIGUOUS, "entry_and_exit_on_same_bar")
    return SameBarAmbiguity(AmbiguityStatus.NONE)


def record_quantconnect_not_run(reason: str, command: str) -> BacktestEvent:
    if not reason.strip() or not command.strip():
        raise ValueError("not-run records require a reason and the attempted/documented command.")
    return BacktestEvent(
        status=BacktestRunStatus.NOT_RUN,
        source="quantconnect_cloud_lean",
        message=reason,
        command=command,
        metrics={},
    )


def _timeframe_allowed_for_backtest_mode(strategy_mode: StrategyMode, timeframe: BarTimeframe) -> bool:
    if strategy_mode is StrategyMode.DAILY_ONLY:
        return timeframe is BarTimeframe.DAILY
    if strategy_mode is StrategyMode.DAILY_FILTER_4H_SETUP:
        return timeframe is BarTimeframe.FOUR_HOUR
    if strategy_mode is StrategyMode.DAILY_FILTER_4H_SETUP_1H_OPTIONAL:
        return timeframe in {BarTimeframe.FOUR_HOUR, BarTimeframe.ONE_HOUR}
    return False
