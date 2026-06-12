"""Trend Pullback setup contracts and offline evaluator."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Mapping

import yaml

from marketpilot.indicators import IndicatorResult
from marketpilot.regime import RegimeResult
from marketpilot.setups.base import NumericEvidence, SetupRejectionReason, SetupResult, SetupStatus, SetupTiming
from marketpilot.symbol_data import SymbolData


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

