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
    earnings_source_verified: bool = False
    earnings_risk_conflict: bool = False
    portfolio_conflict: bool | None = None


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
    lookback_bars = int(resistance_config["lookback_bars"])
    breakout_buffer_pct = float(resistance_config["breakout_buffer_pct"])

    if len(bars) < lookback_bars + 1 or any(not bar.complete for bar in bars):
        reasons.append(SetupRejectionReason.INCOMPLETE_COMPLETED_BAR_DATA)
    if not setup_input.symbol_data.future_signal_ready(REQUIRED_INDICATORS):
        reasons.append(SetupRejectionReason.DATA_NOT_READY)
    if setup_input.regime.regime is MarketRegime.RISK_OFF or not setup_input.regime.future_entries_allowed:
        reasons.append(SetupRejectionReason.RISK_OFF)
    reasons.extend(_validate_indicators(setup_input.indicators))

    if not bars:
        return _build_result(setup_input, signal_time, evidence, reasons)

    latest = bars[-1]
    prior_resistance: float | None = None
    try:
        prior_resistance = calculate_prior_resistance(bars, lookback_bars)
    except ValueError:
        reasons.append(SetupRejectionReason.INVALID_PRIOR_RESISTANCE)

    evidence.append(NumericEvidence("resistance_lookback_bars", lookback_bars, lookback_bars, prior_resistance is not None))
    evidence.append(NumericEvidence("breakout_buffer_pct", breakout_buffer_pct, "config", True))

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
        timing=SetupTiming(signal_time=signal_time),
        evidence=tuple(evidence),
        rejection_reasons=unique_reasons,
        explanation=_explain(status, unique_reasons),
    )


def _explain(status: SetupStatus, reasons: tuple[SetupRejectionReason, ...]) -> tuple[str, ...]:
    if status is SetupStatus.VALID:
        return ("Volume Breakout is valid on completed daily-bar evidence.",)
    return tuple(f"Rejected: {reason.value}." for reason in reasons)


def _positive(value: object) -> bool:
    return isinstance(value, (int, float)) and isfinite(float(value)) and float(value) > 0
