"""Relative Strength Leader setup evaluator with no trading side effects."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import isfinite
from pathlib import Path
from typing import Mapping, Sequence

import yaml

from marketpilot.indicators import IndicatorResult, ReadinessStatus, distance_from_high, relative_strength
from marketpilot.regime import MarketRegime, RegimeResult
from marketpilot.setups.base import NumericEvidence, SetupRejectionReason, SetupResult, SetupStatus, SetupTiming
from marketpilot.symbol_data import SymbolData
from marketpilot.timeframes import BarTimeframe, StrategyMode, timeframe_allowed_for_strategy_mode


SETUP_NAME = "relative_strength_leader"
DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "relative_strength.yaml"
REQUIRED_INDICATORS = ("EMA20", "EMA50", "EMA200", "ATR14")


@dataclass(frozen=True)
class CompletedDailyBar:
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    complete: bool = True


@dataclass(frozen=True)
class RelativeStrengthInput:
    symbol_data: SymbolData
    regime: RegimeResult
    bars: tuple[CompletedDailyBar, ...]
    indicators: Mapping[str, IndicatorResult]
    symbol_returns: Sequence[float]
    spy_returns: Sequence[float]
    qqq_returns: Sequence[float]
    average_dollar_volume: float
    atr_pct: float
    ema20_extension_pct: float
    symbol_data_stale: bool = False
    strategy_mode: StrategyMode = StrategyMode.DAILY_ONLY
    signal_timeframe: BarTimeframe = BarTimeframe.DAILY
    one_hour_confirmation_available: bool | None = None


def load_relative_strength_config(path: str | Path = DEFAULT_CONFIG_PATH) -> dict:
    with Path(path).open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    config = loaded.get("relative_strength", loaded)
    if not isinstance(config, dict):
        raise ValueError("relative_strength config must be a mapping.")
    if config.get("paper_trading_only") is not True:
        raise ValueError("relative_strength config requires paper_trading_only: true.")
    if config.get("timing_mode") != "completed_daily_bar":
        raise ValueError("Relative Strength Leader must use completed_daily_bar timing.")
    disabled = config.get("disabled_behaviors", {})
    required_disabled = (
        "intrabar_validity",
        "create_orders",
        "portfolio_sizing",
        "buy_watch_avoid_classifications",
        "backtest_result_creation",
        "telegram_delivery",
        "paper_deployment",
        "live_deployment",
    )
    for key in required_disabled:
        if disabled.get(key) is not False:
            raise ValueError(f"Relative Strength Leader requires disabled {key}.")
    return config


def contract_result(symbol: str, signal_time: datetime) -> SetupResult:
    return SetupResult(
        setup_name=SETUP_NAME,
        symbol=symbol.strip().upper(),
        status=SetupStatus.REJECTED,
        timing=SetupTiming(signal_time=signal_time),
        evidence=(NumericEvidence("contract_only", True, True, True),),
        rejection_reasons=(SetupRejectionReason.INCOMPLETE_COMPLETED_BAR_DATA,),
        explanation=("Relative Strength Leader contract exists; evaluator is setup evidence only.",),
    )


def evaluate_relative_strength_leader(
    setup_input: RelativeStrengthInput,
    config: dict | None = None,
) -> SetupResult:
    active_config = config or load_relative_strength_config()
    bars = setup_input.bars
    signal_time = bars[-1].time if bars else datetime.min
    evidence: list[NumericEvidence] = _timeframe_evidence(setup_input)
    reasons: list[SetupRejectionReason] = []

    if len(bars) < 2 or any(not bar.complete for bar in bars) or any(not _valid_bar_values(bar) for bar in bars):
        reasons.append(SetupRejectionReason.INCOMPLETE_COMPLETED_BAR_DATA)
    evidence.append(NumericEvidence("symbol_data_stale", setup_input.symbol_data_stale, False, not setup_input.symbol_data_stale))
    if not setup_input.symbol_data.future_signal_ready(REQUIRED_INDICATORS, stale=setup_input.symbol_data_stale):
        reasons.append(SetupRejectionReason.DATA_NOT_READY)
    if setup_input.regime.regime is MarketRegime.RISK_OFF or not setup_input.regime.future_entries_allowed:
        reasons.append(SetupRejectionReason.RISK_OFF)
    if not timeframe_allowed_for_strategy_mode(setup_input.strategy_mode, setup_input.signal_timeframe):
        reasons.append(SetupRejectionReason.DATA_NOT_READY)
    reasons.extend(_validate_indicators(setup_input.indicators))

    if not bars:
        return _build_result(setup_input, signal_time, evidence, reasons)

    latest = bars[-1]
    ema20 = _indicator_value(setup_input.indicators, "EMA20")
    ema50 = _indicator_value(setup_input.indicators, "EMA50")
    ema200 = _indicator_value(setup_input.indicators, "EMA200")

    trend_config = active_config["trend"]
    close_above_ema50 = _numeric(ema50) and latest.close > float(ema50)
    close_above_ema200 = _numeric(ema200) and latest.close > float(ema200)
    ema50_above_ema200 = _numeric(ema50) and _numeric(ema200) and float(ema50) > float(ema200)
    evidence.extend(
        [
            NumericEvidence("close_above_ema50", close_above_ema50, True, close_above_ema50),
            NumericEvidence("close_above_ema200", close_above_ema200, True, close_above_ema200),
            NumericEvidence("ema50_above_ema200", ema50_above_ema200, True, ema50_above_ema200),
        ]
    )
    if trend_config.get("require_close_above_ema50", True) and not close_above_ema50:
        reasons.append(SetupRejectionReason.BROKEN_TREND)
    if trend_config.get("require_close_above_ema200", True) and not close_above_ema200:
        reasons.append(SetupRejectionReason.BROKEN_TREND)
    if trend_config.get("require_ema50_above_ema200", True) and not ema50_above_ema200:
        reasons.append(SetupRejectionReason.BROKEN_TREND)

    for window in active_config["benchmark"]["required_windows"]:
        spy_rs = relative_strength(setup_input.symbol_returns, setup_input.spy_returns, int(window))
        qqq_rs = relative_strength(setup_input.symbol_returns, setup_input.qqq_returns, int(window))
        spy_value = spy_rs.value if spy_rs.status is ReadinessStatus.READY else None
        qqq_value = qqq_rs.value if qqq_rs.status is ReadinessStatus.READY else None
        spy_passed = _positive(spy_value)
        evidence.append(NumericEvidence(f"spy_rs{window}", _rounded_or_none(spy_value), "> 0", spy_passed))
        evidence.append(NumericEvidence(f"qqq_rs{window}", _rounded_or_none(qqq_value), "evidence_only", None))
        if not spy_passed:
            reasons.append(SetupRejectionReason.WEAK_SPY_RELATIVE_STRENGTH)

    risk_config = active_config["risk"]
    liquidity_config = active_config["liquidity"]
    atr_threshold = float(risk_config["max_atr_pct"])
    atr_pct = float(setup_input.atr_pct) if _numeric(setup_input.atr_pct) else float("inf")
    evidence.append(NumericEvidence("atr_pct", _rounded_or_invalid(atr_pct), atr_threshold, isfinite(atr_pct) and 0 < atr_pct <= atr_threshold))
    if not isfinite(atr_pct) or atr_pct <= 0 or atr_pct > atr_threshold:
        reasons.append(SetupRejectionReason.EXCESSIVE_ATR)

    max_extension = float(risk_config["max_ema20_extension_pct"])
    extension = float(setup_input.ema20_extension_pct) if _numeric(setup_input.ema20_extension_pct) else float("inf")
    evidence.append(NumericEvidence("ema20_extension_pct", _rounded_or_invalid(extension), max_extension, isfinite(extension) and extension <= max_extension))
    if not isfinite(extension) or extension > max_extension:
        reasons.append(SetupRejectionReason.EMA20_EXTENSION_EXCESSIVE)

    min_dollar_volume = float(liquidity_config["min_average_dollar_volume"])
    dollar_volume_ok = _positive(setup_input.average_dollar_volume) and float(setup_input.average_dollar_volume) >= min_dollar_volume
    evidence.append(NumericEvidence("average_dollar_volume", setup_input.average_dollar_volume, min_dollar_volume, dollar_volume_ok))
    if not dollar_volume_ok:
        reasons.append(SetupRejectionReason.INSUFFICIENT_DOLLAR_VOLUME)

    high_distance = distance_from_high(tuple(bar.close for bar in bars), period=min(252, len(bars)))
    high_distance_value = high_distance.value if high_distance.status is ReadinessStatus.READY else None
    max_high_distance = float(risk_config["max_52_week_high_distance_pct"])
    high_distance_passed = _numeric(high_distance_value) and float(high_distance_value) >= -max_high_distance
    evidence.append(NumericEvidence("52_week_high_distance_pct", _rounded_or_none(high_distance_value), f">= -{max_high_distance}", high_distance_passed))
    if not high_distance_passed:
        reasons.append(SetupRejectionReason.EXCESSIVE_52_WEEK_HIGH_DISTANCE)

    evidence.append(NumericEvidence("regime", setup_input.regime.regime.value, "entry_allowed", setup_input.regime.future_entries_allowed))
    return _build_result(setup_input, signal_time, evidence, reasons)


def _build_result(
    setup_input: RelativeStrengthInput,
    signal_time: datetime,
    evidence: list[NumericEvidence],
    reasons: list[SetupRejectionReason],
) -> SetupResult:
    unique_reasons = tuple(dict.fromkeys(reasons))
    status = SetupStatus.REJECTED if unique_reasons else SetupStatus.VALID
    return SetupResult(
        setup_name=SETUP_NAME,
        symbol=setup_input.symbol_data.symbol.strip().upper(),
        status=status,
        timing=SetupTiming(
            signal_time=signal_time,
            timing_mode=setup_input.signal_timeframe.timing_mode,
            uses_completed_daily_bar=setup_input.signal_timeframe is BarTimeframe.DAILY,
            strategy_mode=setup_input.strategy_mode,
            signal_timeframe=setup_input.signal_timeframe,
            bar_end=signal_time,
            source_resolution=setup_input.signal_timeframe.value,
        ),
        evidence=tuple(evidence),
        rejection_reasons=unique_reasons,
        explanation=_explain(status, unique_reasons),
    )


def _explain(status: SetupStatus, reasons: tuple[SetupRejectionReason, ...]) -> tuple[str, ...]:
    if status is SetupStatus.VALID:
        return ("Relative Strength Leader is valid on completed-bar SPY relative-strength evidence.",)
    return tuple(f"Rejected: {reason.value}." for reason in reasons)


def _timeframe_evidence(setup_input: RelativeStrengthInput) -> list[NumericEvidence]:
    return [
        NumericEvidence("strategy_mode", setup_input.strategy_mode.value, "config", True),
        NumericEvidence("signal_timeframe", setup_input.signal_timeframe.value, "setup_signal", True),
        NumericEvidence("one_hour_confirmation_available", setup_input.one_hour_confirmation_available, "optional_confirmation_only", None),
    ]


def _validate_indicators(indicators: Mapping[str, IndicatorResult]) -> list[SetupRejectionReason]:
    reasons: list[SetupRejectionReason] = []
    for name in REQUIRED_INDICATORS:
        result = indicators.get(name)
        if result is None or result.status is not ReadinessStatus.READY or result.value is None:
            reasons.append(SetupRejectionReason.DATA_NOT_READY)
            continue
        if isinstance(result.value, (int, float)) and not isfinite(float(result.value)):
            reasons.append(SetupRejectionReason.DATA_NOT_READY)
    return reasons


def _indicator_value(indicators: Mapping[str, IndicatorResult], name: str) -> float | None:
    result = indicators.get(name)
    if result is None or result.status is not ReadinessStatus.READY or result.value is None:
        return None
    if not _numeric(result.value):
        return None
    return float(result.value)


def _valid_bar_values(bar: CompletedDailyBar) -> bool:
    values = (bar.open, bar.high, bar.low, bar.close, bar.volume)
    return all(_numeric(value) for value in values) and bar.high > 0 and bar.low > 0 and bar.close > 0 and bar.volume >= 0


def _positive(value: object) -> bool:
    return isinstance(value, (int, float)) and isfinite(float(value)) and float(value) > 0


def _numeric(value: object) -> bool:
    return isinstance(value, (int, float)) and isfinite(float(value))


def _rounded_or_none(value: object) -> float | None:
    return round(float(value), 6) if _numeric(value) else None


def _rounded_or_invalid(value: float) -> float | str:
    return round(value, 4) if isfinite(value) else "invalid"
