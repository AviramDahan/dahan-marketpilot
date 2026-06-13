"""Volume Breakout setup contract with no trading side effects."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import isfinite
from pathlib import Path
from typing import Mapping

import yaml

from marketpilot.indicators import IndicatorResult
from marketpilot.indicators import ReadinessStatus
from marketpilot.regime import MarketRegime
from marketpilot.regime import RegimeResult
from marketpilot.setups.base import NumericEvidence, SetupRejectionReason, SetupResult, SetupStatus, SetupTiming
from marketpilot.symbol_data import SymbolData
from marketpilot.timeframes import BarTimeframe, StrategyMode, timeframe_allowed_for_strategy_mode


SETUP_NAME = "volume_breakout"
DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "volume_breakout.yaml"


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
class VolumeBreakoutInput:
    symbol_data: SymbolData
    regime: RegimeResult
    bars: tuple[CompletedDailyBar, ...]
    indicators: Mapping[str, IndicatorResult]
    average_volume: float
    average_dollar_volume: float
    atr_pct: float
    projected_target: float
    symbol_data_stale: bool = False
    earnings_source_verified: bool = False
    earnings_risk_conflict: bool = False
    portfolio_conflict: bool | None = None
    strategy_mode: StrategyMode = StrategyMode.DAILY_ONLY
    signal_timeframe: BarTimeframe = BarTimeframe.DAILY
    one_hour_confirmation_available: bool | None = None


REQUIRED_INDICATORS = ("EMA20", "ATR14")


def load_volume_breakout_config(path: str | Path = DEFAULT_CONFIG_PATH) -> dict:
    with Path(path).open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    config = loaded.get("volume_breakout", loaded)
    if not isinstance(config, dict):
        raise ValueError("volume_breakout config must be a mapping.")
    if config.get("paper_trading_only") is not True:
        raise ValueError("volume_breakout config requires paper_trading_only: true.")
    if config.get("timing_mode") != "completed_daily_bar":
        raise ValueError("Volume Breakout must use completed_daily_bar timing.")
    disabled = config.get("disabled_behaviors", {})
    if disabled.get("intrabar_validity") is not False:
        raise ValueError("Volume Breakout must use completed daily bars only.")
    return config


def calculate_prior_resistance(bars: tuple[CompletedDailyBar, ...], lookback_bars: int) -> float:
    if lookback_bars <= 0:
        raise ValueError("lookback_bars must be positive.")
    if len(bars) < lookback_bars + 1:
        raise ValueError("insufficient completed bars for prior resistance.")

    signal_bar = bars[-1]
    prior_bars = bars[-lookback_bars - 1 : -1]
    if not signal_bar.complete or any(not bar.complete for bar in prior_bars):
        raise ValueError("prior resistance requires complete daily bars.")

    highs = [float(bar.high) for bar in prior_bars]
    if any(not isfinite(high) or high <= 0 for high in highs):
        raise ValueError("prior resistance requires finite positive high values.")
    return max(highs)


def evaluate_volume_breakout(
    setup_input: VolumeBreakoutInput,
    config: dict | None = None,
) -> SetupResult:
    active_config = config or load_volume_breakout_config()
    bars = setup_input.bars
    signal_time = bars[-1].time if bars else datetime.min
    evidence: list[NumericEvidence] = []
    reasons: list[SetupRejectionReason] = []

    resistance_config = active_config["resistance"]
    volume_config = active_config["volume"]
    risk_config = active_config["risk"]
    lookback_bars = int(resistance_config["lookback_bars"])
    breakout_buffer_pct = float(resistance_config["breakout_buffer_pct"])

    if len(bars) < lookback_bars + 1 or any(not bar.complete for bar in bars) or any(not _valid_bar_values(bar) for bar in bars):
        reasons.append(SetupRejectionReason.INCOMPLETE_COMPLETED_BAR_DATA)
    symbol_data_ready = setup_input.symbol_data.future_signal_ready(REQUIRED_INDICATORS, stale=setup_input.symbol_data_stale)
    evidence.append(
        NumericEvidence(
            "symbol_data_stale",
            setup_input.symbol_data_stale,
            False,
            not setup_input.symbol_data_stale,
        )
    )
    if not symbol_data_ready:
        reasons.append(SetupRejectionReason.DATA_NOT_READY)
    if setup_input.regime.regime is MarketRegime.RISK_OFF or not setup_input.regime.future_entries_allowed:
        reasons.append(SetupRejectionReason.RISK_OFF)
    if not timeframe_allowed_for_strategy_mode(setup_input.strategy_mode, setup_input.signal_timeframe):
        reasons.append(SetupRejectionReason.DATA_NOT_READY)
    reasons.extend(_validate_indicators(setup_input.indicators))

    evidence.extend(_timeframe_evidence(setup_input))
    evidence.append(NumericEvidence("resistance_lookback_bars", lookback_bars, lookback_bars, len(bars) >= lookback_bars + 1))
    evidence.append(NumericEvidence("breakout_buffer_pct", breakout_buffer_pct, "config", True))
    evidence.append(NumericEvidence("regime", setup_input.regime.regime.value, "entry_allowed", setup_input.regime.future_entries_allowed))

    if not bars:
        return _build_result(setup_input, signal_time, evidence, reasons)

    latest = bars[-1]
    prior_resistance: float | None = None
    try:
        prior_resistance = calculate_prior_resistance(bars, lookback_bars)
    except ValueError:
        reasons.append(SetupRejectionReason.INVALID_PRIOR_RESISTANCE)

    if prior_resistance is None:
        return _build_result(setup_input, signal_time, evidence, reasons)

    buffered_resistance = prior_resistance * (1 + breakout_buffer_pct / 100)
    close_breaks_out = latest.close > buffered_resistance
    evidence.extend(
        [
            NumericEvidence("prior_resistance", round(prior_resistance, 4), "previous_completed_highs", True),
            NumericEvidence("buffered_resistance", round(buffered_resistance, 4), "prior_resistance_plus_buffer", True),
            NumericEvidence("breakout_close", latest.close, round(buffered_resistance, 4), close_breaks_out),
            NumericEvidence("average_volume", setup_input.average_volume, "setup_input", _positive(setup_input.average_volume)),
            NumericEvidence("volume_average_period", int(volume_config["average_volume_period"]), "config", True),
        ]
    )
    if resistance_config.get("require_close_above_buffered_resistance", True) and not close_breaks_out:
        reasons.append(SetupRejectionReason.BREAKOUT_NOT_CONFIRMED)

    volume_ratio = latest.volume / float(setup_input.average_volume) if _positive(setup_input.average_volume) else 0.0
    volume_threshold = float(volume_config["min_volume_ratio"])
    evidence.append(NumericEvidence("volume_ratio", round(volume_ratio, 4), volume_threshold, volume_ratio >= volume_threshold))
    if volume_ratio < volume_threshold:
        reasons.append(SetupRejectionReason.VOLUME_CONFIRMATION_WEAK)

    ema20 = _indicator_value(setup_input.indicators, "EMA20")
    max_ema20_extension_pct = float(risk_config["max_ema20_extension_pct"])
    ema20_extension_pct = ((latest.close - ema20) / ema20) * 100 if _positive(ema20) else float("inf")
    evidence.append(
        NumericEvidence(
            "ema20_extension_pct",
            round(ema20_extension_pct, 4) if isfinite(ema20_extension_pct) else "invalid",
            max_ema20_extension_pct,
            isfinite(ema20_extension_pct) and ema20_extension_pct <= max_ema20_extension_pct,
        )
    )
    if not isfinite(ema20_extension_pct) or ema20_extension_pct > max_ema20_extension_pct:
        reasons.append(SetupRejectionReason.EMA20_EXTENSION_EXCESSIVE)

    atr_pct = float(setup_input.atr_pct) if _numeric(setup_input.atr_pct) else float("inf")
    max_atr_pct = float(risk_config["max_atr_pct"])
    evidence.append(
        NumericEvidence(
            "atr_pct",
            round(atr_pct, 4) if isfinite(atr_pct) else "invalid",
            max_atr_pct,
            isfinite(atr_pct) and 0 < atr_pct <= max_atr_pct,
        )
    )
    if not isfinite(atr_pct) or atr_pct <= 0 or atr_pct > max_atr_pct:
        reasons.append(SetupRejectionReason.EXCESSIVE_ATR)

    min_dollar_volume = float(volume_config["min_dollar_volume"])
    average_dollar_volume_ok = _positive(setup_input.average_dollar_volume) and float(setup_input.average_dollar_volume) >= min_dollar_volume
    evidence.append(
        NumericEvidence(
            "average_dollar_volume",
            setup_input.average_dollar_volume,
            min_dollar_volume,
            average_dollar_volume_ok,
        )
    )
    if not average_dollar_volume_ok:
        reasons.append(SetupRejectionReason.INSUFFICIENT_DOLLAR_VOLUME)

    projected_target = float(setup_input.projected_target) if _numeric(setup_input.projected_target) else float("nan")
    evidence.append(
        NumericEvidence(
            "projected_target",
            round(projected_target, 4) if isfinite(projected_target) else "invalid",
            "setup_evidence",
            isfinite(projected_target) and projected_target > latest.close,
        )
    )
    epsilon_config = risk_config.get("reward_risk_epsilon", 0.01)
    epsilon = max(float(epsilon_config), 0.01) if _positive(epsilon_config) else 0.01
    risk_per_share_proxy = max(latest.close - prior_resistance, epsilon)
    reward_per_share_proxy = max(projected_target - latest.close, 0.0) if isfinite(projected_target) else 0.0
    reward_risk_proxy = reward_per_share_proxy / risk_per_share_proxy
    min_reward_risk_proxy = float(risk_config["min_reward_risk_proxy"])
    evidence.extend(
        [
            NumericEvidence("risk_per_share_proxy", round(risk_per_share_proxy, 4), "latest.close - prior_resistance", True),
            NumericEvidence("reward_per_share_proxy", round(reward_per_share_proxy, 4), "projected_target - latest.close", reward_per_share_proxy > 0),
            NumericEvidence("reward_risk_proxy", round(reward_risk_proxy, 4), min_reward_risk_proxy, reward_risk_proxy >= min_reward_risk_proxy),
        ]
    )
    if reward_risk_proxy < min_reward_risk_proxy:
        reasons.append(SetupRejectionReason.WEAK_REWARD_RISK)

    evidence.extend(
        [
            NumericEvidence("earnings_source_verified", setup_input.earnings_source_verified, "deferred_gate", None),
            NumericEvidence("earnings_risk_conflict", setup_input.earnings_risk_conflict, "verified_explicit_input", not setup_input.earnings_risk_conflict),
            NumericEvidence("portfolio_conflict", setup_input.portfolio_conflict, "explicit_input_only", setup_input.portfolio_conflict is not True),
        ]
    )
    if setup_input.earnings_source_verified and setup_input.earnings_risk_conflict:
        reasons.append(SetupRejectionReason.EARNINGS_RISK_CONFLICT)
    if setup_input.portfolio_conflict is True:
        reasons.append(SetupRejectionReason.PORTFOLIO_CONFLICT)

    return _build_result(setup_input, signal_time, evidence, reasons)


def contract_result(symbol: str, signal_time: datetime) -> SetupResult:
    return SetupResult(
        setup_name=SETUP_NAME,
        symbol=symbol.strip().upper(),
        status=SetupStatus.REJECTED,
        timing=SetupTiming(signal_time=signal_time),
        evidence=(NumericEvidence("contract_only", True, True, True),),
        rejection_reasons=(SetupRejectionReason.INCOMPLETE_COMPLETED_BAR_DATA,),
        explanation=("Volume Breakout contract exists; detection is implemented in a later plan.",),
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
    setup_input: VolumeBreakoutInput,
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
        return ("Volume Breakout is valid on completed daily-bar breakout evidence.",)
    return tuple(f"Rejected: {reason.value}." for reason in reasons)


def _timeframe_evidence(setup_input: VolumeBreakoutInput) -> list[NumericEvidence]:
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


def _positive(value: object) -> bool:
    return isinstance(value, (int, float)) and isfinite(float(value)) and float(value) > 0


def _numeric(value: object) -> bool:
    return isinstance(value, (int, float)) and isfinite(float(value))


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
