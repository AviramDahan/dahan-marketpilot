"""Trend Pullback setup contracts and offline evaluator."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import isfinite
from pathlib import Path
from typing import Mapping

import yaml

from marketpilot.indicators import IndicatorResult
from marketpilot.indicators import ReadinessStatus
from marketpilot.regime import MarketRegime, RegimeResult
from marketpilot.setups.base import NumericEvidence, SetupRejectionReason, SetupResult, SetupStatus, SetupTiming
from marketpilot.symbol_data import SymbolData
from marketpilot.timeframes import BarTimeframe, StrategyMode, timeframe_allowed_for_strategy_mode


SETUP_NAME = "trend_pullback"
DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "trend_pullback.yaml"


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
class TrendPullbackInput:
    symbol_data: SymbolData
    regime: RegimeResult
    bars: tuple[CompletedDailyBar, ...]
    indicators: Mapping[str, IndicatorResult]
    average_volume: float
    atr_pct: float
    reward_risk_proxy: float
    earnings_source_verified: bool = False
    strategy_mode: StrategyMode = StrategyMode.DAILY_ONLY
    signal_timeframe: BarTimeframe = BarTimeframe.DAILY
    one_hour_confirmation_available: bool | None = None


REQUIRED_INDICATORS = ("EMA20", "EMA50", "EMA200", "RSI14", "MACD", "ATR14")


def load_trend_pullback_config(path: str | Path = DEFAULT_CONFIG_PATH) -> dict:
    with Path(path).open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    config = loaded.get("trend_pullback", loaded)
    if not isinstance(config, dict):
        raise ValueError("trend_pullback config must be a mapping.")
    if config.get("paper_trading_only") is not True:
        raise ValueError("trend_pullback config requires paper_trading_only: true.")
    disabled = config.get("disabled_behaviors", {})
    if disabled.get("intrabar_validity") is not False:
        raise ValueError("Trend Pullback must use completed daily bars only.")
    return config


def evaluate_trend_pullback(
    setup_input: TrendPullbackInput,
    config: dict | None = None,
) -> SetupResult:
    active_config = config or load_trend_pullback_config()
    bars = setup_input.bars
    signal_time = bars[-1].time if bars else datetime.min
    evidence: list[NumericEvidence] = []
    reasons: list[SetupRejectionReason] = []

    if len(bars) < 2 or any(not bar.complete for bar in bars):
        reasons.append(SetupRejectionReason.INCOMPLETE_COMPLETED_BAR_DATA)
    if not setup_input.symbol_data.future_signal_ready(REQUIRED_INDICATORS):
        reasons.append(SetupRejectionReason.DATA_NOT_READY)
    if setup_input.regime.regime is MarketRegime.RISK_OFF or not setup_input.regime.future_entries_allowed:
        reasons.append(SetupRejectionReason.RISK_OFF)
    if not timeframe_allowed_for_strategy_mode(setup_input.strategy_mode, setup_input.signal_timeframe):
        reasons.append(SetupRejectionReason.DATA_NOT_READY)

    indicator_reasons = _validate_indicators(setup_input.indicators)
    reasons.extend(indicator_reasons)

    evidence.extend(_timeframe_evidence(setup_input))

    if not bars or reasons:
        return _build_result(setup_input, signal_time, evidence, reasons)

    latest = bars[-1]
    prior = bars[-2]
    ema20 = float(setup_input.indicators["EMA20"].value)
    ema50 = float(setup_input.indicators["EMA50"].value)
    ema200 = float(setup_input.indicators["EMA200"].value)
    atr_pct = float(setup_input.atr_pct)
    reward_risk = float(setup_input.reward_risk_proxy)

    trend_config = active_config["trend"]
    if trend_config.get("require_price_above_ema200", True) and latest.close <= ema200:
        reasons.append(SetupRejectionReason.BROKEN_TREND)
    if trend_config.get("require_ema20_above_ema50", True) and ema20 <= ema50:
        reasons.append(SetupRejectionReason.BROKEN_TREND)
    if trend_config.get("require_ema50_above_ema200", True) and ema50 <= ema200:
        reasons.append(SetupRejectionReason.BROKEN_TREND)
    if trend_config.get("reject_close_below_ema50", True) and any(bar.close < ema50 for bar in bars):
        reasons.append(SetupRejectionReason.EMA50_BREAK)

    pullback_bars = _count_pullback_bars(bars)
    evidence.append(NumericEvidence("pullback_bars", pullback_bars, f"{active_config['min_pullback_bars']}-{active_config['max_pullback_bars']}", True))
    if pullback_bars < int(active_config["min_pullback_bars"]):
        reasons.append(SetupRejectionReason.PULLBACK_TOO_SHORT)
    if pullback_bars > int(active_config["max_pullback_bars"]):
        reasons.append(SetupRejectionReason.PULLBACK_TOO_LONG)

    proximity = active_config["proximity"]
    ema20_distance = _distance_pct(latest.close, ema20)
    ema50_distance = _distance_pct(latest.close, ema50)
    close_to_ema20 = ema20_distance <= float(proximity["ema20_max_distance_pct"])
    close_to_ema50 = ema50_distance <= float(proximity["ema50_max_distance_pct"])
    evidence.extend(
        [
            NumericEvidence("ema20_distance_pct", round(ema20_distance, 4), proximity["ema20_max_distance_pct"], close_to_ema20),
            NumericEvidence("ema50_distance_pct", round(ema50_distance, 4), proximity["ema50_max_distance_pct"], close_to_ema50),
        ]
    )
    if not close_to_ema20 and not close_to_ema50:
        reasons.append(SetupRejectionReason.NO_EMA_PROXIMITY)

    recovered = latest.close > prior.high
    evidence.append(NumericEvidence("close_above_prior_high", latest.close, prior.high, recovered))
    if active_config["recovery"].get("require_close_above_prior_high", True) and not recovered:
        reasons.append(SetupRejectionReason.RECOVERY_NOT_CONFIRMED)

    volume_ratio = latest.volume / float(setup_input.average_volume) if _positive(setup_input.average_volume) else 0.0
    volume_threshold = float(active_config["recovery"]["min_recovery_volume_ratio"])
    evidence.append(NumericEvidence("recovery_volume_ratio", round(volume_ratio, 4), volume_threshold, volume_ratio >= volume_threshold))
    if volume_ratio < volume_threshold:
        reasons.append(SetupRejectionReason.RECOVERY_VOLUME_WEAK)

    atr_threshold = float(active_config["risk"]["max_atr_pct"])
    evidence.append(NumericEvidence("atr_pct", atr_pct, atr_threshold, atr_pct <= atr_threshold))
    if not _positive(atr_pct) or atr_pct > atr_threshold:
        reasons.append(SetupRejectionReason.EXCESSIVE_ATR)

    rr_threshold = float(active_config["risk"]["min_reward_risk_proxy"])
    evidence.append(NumericEvidence("reward_risk_proxy", reward_risk, rr_threshold, reward_risk >= rr_threshold))
    if not _positive(reward_risk) or reward_risk < rr_threshold:
        reasons.append(SetupRejectionReason.WEAK_REWARD_RISK)

    evidence.extend(
        [
            NumericEvidence("rsi14", setup_input.indicators["RSI14"].value, "supporting_evidence", None),
            NumericEvidence("macd", setup_input.indicators["MACD"].value, "supporting_evidence", None),
            NumericEvidence("regime", setup_input.regime.regime.value, "entry_allowed", setup_input.regime.future_entries_allowed),
            NumericEvidence("earnings_source_verified", setup_input.earnings_source_verified, "deferred_gate", None),
        ]
    )

    return _build_result(setup_input, signal_time, evidence, reasons)


def contract_result(symbol: str, signal_time: datetime) -> SetupResult:
    return SetupResult(
        setup_name=SETUP_NAME,
        symbol=symbol.strip().upper(),
        status=SetupStatus.REJECTED,
        timing=SetupTiming(signal_time=signal_time),
        evidence=(NumericEvidence("contract_only", True, True, True),),
        rejection_reasons=(SetupRejectionReason.INCOMPLETE_COMPLETED_BAR_DATA,),
        explanation=("Trend Pullback contract exists; detection is implemented in a later plan.",),
    )


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


def _build_result(
    setup_input: TrendPullbackInput,
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
        return ("Trend Pullback is valid on completed daily-bar evidence.",)
    return tuple(f"Rejected: {reason.value}." for reason in reasons)


def _timeframe_evidence(setup_input: TrendPullbackInput) -> list[NumericEvidence]:
    return [
        NumericEvidence("strategy_mode", setup_input.strategy_mode.value, "config", True),
        NumericEvidence("signal_timeframe", setup_input.signal_timeframe.value, "setup_signal", True),
        NumericEvidence(
            "one_hour_confirmation_available",
            setup_input.one_hour_confirmation_available,
            "optional_confirmation_only",
            None,
        ),
    ]


def _count_pullback_bars(bars: tuple[CompletedDailyBar, ...]) -> int:
    if len(bars) < 2:
        return 0
    count = 0
    for previous, current in zip(bars, bars[1:]):
        if current.close <= previous.close:
            count += 1
        else:
            break
    return max(count, len(bars) - 1)


def _distance_pct(price: float, average_value: float) -> float:
    if average_value == 0:
        return float("inf")
    return abs((price - average_value) / average_value) * 100


def _positive(value: object) -> bool:
    return isinstance(value, (int, float)) and isfinite(float(value)) and float(value) > 0
