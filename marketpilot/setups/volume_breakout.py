"""Volume Breakout setup contract with no trading side effects."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import isfinite
from pathlib import Path
from typing import Mapping

import yaml

from marketpilot.indicators import IndicatorResult
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
