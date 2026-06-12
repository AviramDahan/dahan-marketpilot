"""Offline SPY/QQQ market-regime classifier for Phase 2."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite
from pathlib import Path
from typing import Iterable

import yaml


class MarketRegime(str, Enum):
    RISK_ON = "RISK_ON"
    NEUTRAL = "NEUTRAL"
    RISK_OFF = "RISK_OFF"


@dataclass(frozen=True)
class BenchmarkSnapshot:
    symbol: str
    price: float
    ema20: float
    ema50: float
    ema200: float
    slope20: float
    slope60: float
    return20: float
    return60: float
    ready: bool = True


@dataclass(frozen=True)
class RegimeResult:
    regime: MarketRegime
    future_entries_allowed: bool
    changed: bool
    previous_regime: MarketRegime | None
    reasons: tuple[str, ...]


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "regime.yaml"


def load_regime_config(path: str | Path = DEFAULT_CONFIG_PATH) -> dict:
    with Path(path).open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    config = loaded.get("regime", loaded)
    if not isinstance(config, dict):
        raise ValueError("regime config must be a mapping.")
    if config.get("paper_trading_only") is not True:
        raise ValueError("regime config requires paper_trading_only: true.")
    if config.get("entry_gate_only") is not True or config.get("override_exits") is not False:
        raise ValueError("regime config must remain entry-gate only.")
    return config


def classify_market_regime(
    snapshots: Iterable[BenchmarkSnapshot],
    config: dict | None = None,
    previous_regime: MarketRegime | None = None,
) -> RegimeResult:
    active_config = config or load_regime_config()
    benchmarks = tuple(snapshots)
    expected_symbols = set(active_config.get("benchmark_symbols", ()))
    present_symbols = {snapshot.symbol.upper() for snapshot in benchmarks}

    if expected_symbols - present_symbols:
        return _result(MarketRegime.NEUTRAL, False, previous_regime, ("missing_benchmark",))
    if any(not _snapshot_ready(snapshot) for snapshot in benchmarks):
        return _result(MarketRegime.NEUTRAL, False, previous_regime, ("unready_benchmark",))

    above_ema200 = sum(1 for snapshot in benchmarks if snapshot.price > snapshot.ema200)
    positive_20 = sum(1 for snapshot in benchmarks if snapshot.return20 > 0 and snapshot.slope20 > 0)
    positive_60 = sum(1 for snapshot in benchmarks if snapshot.return60 > 0 and snapshot.slope60 > 0)
    thresholds = active_config["thresholds"]

    if (
        above_ema200 >= thresholds["risk_on"]["min_benchmarks_above_ema200"]
        and positive_20 >= thresholds["risk_on"]["min_benchmarks_positive_20_day_return"]
        and positive_60 >= thresholds["risk_on"]["min_benchmarks_positive_60_day_return"]
    ):
        return _result(MarketRegime.RISK_ON, True, previous_regime, ("benchmarks_supportive",))

    if (
        above_ema200 <= thresholds["risk_off"]["max_benchmarks_above_ema200"]
        and positive_20 <= thresholds["risk_off"]["max_benchmarks_positive_20_day_return"]
        and positive_60 <= thresholds["risk_off"]["max_benchmarks_positive_60_day_return"]
    ):
        return _result(MarketRegime.RISK_OFF, False, previous_regime, ("benchmarks_defensive",))

    return _result(MarketRegime.NEUTRAL, True, previous_regime, ("mixed_benchmarks",))


def suppress_unchanged_transition(result: RegimeResult) -> RegimeResult:
    if result.previous_regime is result.regime:
        return RegimeResult(
            regime=result.regime,
            future_entries_allowed=result.future_entries_allowed,
            changed=False,
            previous_regime=result.previous_regime,
            reasons=result.reasons,
        )
    return result


def _result(
    regime: MarketRegime,
    future_entries_allowed: bool,
    previous_regime: MarketRegime | None,
    reasons: tuple[str, ...],
) -> RegimeResult:
    return suppress_unchanged_transition(
        RegimeResult(
            regime=regime,
            future_entries_allowed=future_entries_allowed,
            changed=previous_regime is not regime,
            previous_regime=previous_regime,
            reasons=reasons,
        )
    )


def _snapshot_ready(snapshot: BenchmarkSnapshot) -> bool:
    values = (
        snapshot.price,
        snapshot.ema20,
        snapshot.ema50,
        snapshot.ema200,
        snapshot.slope20,
        snapshot.slope60,
        snapshot.return20,
        snapshot.return60,
    )
    return snapshot.ready and all(isinstance(value, (int, float)) and isfinite(float(value)) for value in values)

