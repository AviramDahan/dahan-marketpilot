"""Strict offline universe filtering for Phase 2."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable

import yaml

from marketpilot.data_quality import (
    DataQualityIssue,
    DataQualityStatus,
    UniverseCandidate,
    UniverseDecision,
    UniverseSnapshot,
    has_finite_number,
    unique_issues,
    utc_now,
)


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "universe.yaml"


def load_universe_config(path: str | Path = DEFAULT_CONFIG_PATH) -> dict:
    with Path(path).open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    config = loaded.get("universe", loaded)
    if not isinstance(config, dict):
        raise ValueError("universe config must be a mapping.")
    if config.get("paper_trading_only") is not True:
        raise ValueError("universe config requires paper_trading_only: true.")
    return config


def evaluate_candidate(candidate: UniverseCandidate, config: dict) -> UniverseDecision:
    symbol = candidate.normalized_symbol()
    issues: list[DataQualityIssue] = []

    if not symbol:
        issues.append(DataQualityIssue.CRITICAL_MISSING_DATA)
    if candidate.missing_fields:
        issues.append(DataQualityIssue.CRITICAL_MISSING_DATA)
    if config.get("common_equity_only", True) and not candidate.is_common_equity:
        issues.append(DataQualityIssue.UNSUPPORTED_SECURITY)
    if candidate.is_etf:
        issues.append(DataQualityIssue.ETF_EXCLUDED)
    if candidate.is_adr:
        issues.append(DataQualityIssue.ADR_EXCLUDED)
    if candidate.is_otc:
        issues.append(DataQualityIssue.OTC_EXCLUDED)
    if candidate.is_preferred_share:
        issues.append(DataQualityIssue.PREFERRED_EXCLUDED)
    if candidate.is_warrant:
        issues.append(DataQualityIssue.WARRANT_EXCLUDED)
    if candidate.is_stale:
        issues.append(DataQualityIssue.STALE_DATA)
    if not candidate.is_supported:
        issues.append(DataQualityIssue.UNSUPPORTED_SECURITY)

    _check_minimum(candidate.price, config["min_price_usd"], DataQualityIssue.BELOW_MIN_PRICE, issues)
    _check_minimum(
        candidate.history_bars,
        config["min_history_bars"],
        DataQualityIssue.INSUFFICIENT_HISTORY,
        issues,
    )
    _check_minimum(
        candidate.average_volume_20,
        config["min_average_volume_20"],
        DataQualityIssue.BELOW_MIN_VOLUME,
        issues,
    )
    _check_minimum(
        candidate.average_dollar_volume_20,
        config["min_average_dollar_volume_20"],
        DataQualityIssue.BELOW_MIN_DOLLAR_VOLUME,
        issues,
    )
    if candidate.market_cap is not None:
        _check_minimum(
            candidate.market_cap,
            config.get("min_market_cap_usd", 0),
            DataQualityIssue.BELOW_MIN_MARKET_CAP,
            issues,
        )

    ordered_issues = unique_issues(issues)
    status = DataQualityStatus.REJECTED if ordered_issues else DataQualityStatus.ACCEPTED
    return UniverseDecision(symbol=symbol, status=status, issues=ordered_issues, sector=candidate.sector)


def build_universe_snapshot(
    candidates: Iterable[UniverseCandidate],
    config: dict | None = None,
    previous_accepted: Iterable[str] = (),
    update_time: datetime | None = None,
) -> UniverseSnapshot:
    active_config = config or load_universe_config()
    decisions = tuple(evaluate_candidate(candidate, active_config) for candidate in candidates)
    accepted = {decision.symbol for decision in decisions if decision.accepted}
    previous = {symbol.strip().upper() for symbol in previous_accepted}
    sector_distribution: dict[str, int] = {}

    for decision in decisions:
        if decision.accepted and decision.sector:
            sector_distribution[decision.sector] = sector_distribution.get(decision.sector, 0) + 1

    return UniverseSnapshot(
        update_time=update_time or utc_now(),
        decisions=decisions,
        additions=tuple(sorted(accepted - previous)),
        removals=tuple(sorted(previous - accepted)),
        sector_distribution=sector_distribution,
    )


def _check_minimum(
    value: float | int | None,
    minimum: float | int,
    issue: DataQualityIssue,
    issues: list[DataQualityIssue],
) -> None:
    if value is None or not has_finite_number(value):
        issues.append(DataQualityIssue.CRITICAL_MISSING_DATA)
        return
    if float(value) < float(minimum):
        issues.append(issue)

