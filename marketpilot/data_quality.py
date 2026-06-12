"""Offline data-quality vocabulary for Phase 2 universe decisions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from math import isfinite
from typing import Iterable


class DataQualityStatus(str, Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class DataQualityIssue(str, Enum):
    BELOW_MIN_PRICE = "below_min_price"
    INSUFFICIENT_HISTORY = "insufficient_history"
    BELOW_MIN_VOLUME = "below_min_volume"
    BELOW_MIN_DOLLAR_VOLUME = "below_min_dollar_volume"
    BELOW_MIN_MARKET_CAP = "below_min_market_cap"
    ETF_EXCLUDED = "etf_excluded"
    ADR_EXCLUDED = "adr_excluded"
    OTC_EXCLUDED = "otc_excluded"
    PREFERRED_EXCLUDED = "preferred_share_excluded"
    WARRANT_EXCLUDED = "warrant_excluded"
    STALE_DATA = "stale_data"
    CRITICAL_MISSING_DATA = "critical_missing_data"
    UNSUPPORTED_SECURITY = "unsupported_security"
    INVALID_NUMERIC_VALUE = "invalid_numeric_value"


@dataclass(frozen=True)
class UniverseCandidate:
    symbol: str
    price: float | int | None
    history_bars: int | None
    average_volume_20: float | int | None
    average_dollar_volume_20: float | int | None
    market_cap: float | int | None = None
    sector: str | None = None
    is_common_equity: bool = True
    is_etf: bool = False
    is_adr: bool = False
    is_otc: bool = False
    is_preferred_share: bool = False
    is_warrant: bool = False
    is_stale: bool = False
    is_supported: bool = True
    missing_fields: tuple[str, ...] = field(default_factory=tuple)

    def normalized_symbol(self) -> str:
        return self.symbol.strip().upper()


@dataclass(frozen=True)
class UniverseDecision:
    symbol: str
    status: DataQualityStatus
    issues: tuple[DataQualityIssue, ...] = field(default_factory=tuple)
    sector: str | None = None

    @property
    def accepted(self) -> bool:
        return self.status is DataQualityStatus.ACCEPTED


@dataclass(frozen=True)
class UniverseSnapshot:
    update_time: datetime
    decisions: tuple[UniverseDecision, ...]
    additions: tuple[str, ...] = field(default_factory=tuple)
    removals: tuple[str, ...] = field(default_factory=tuple)
    sector_distribution: dict[str, int] = field(default_factory=dict)

    @property
    def accepted_symbols(self) -> tuple[str, ...]:
        return tuple(decision.symbol for decision in self.decisions if decision.accepted)

    @property
    def rejected_symbols(self) -> tuple[str, ...]:
        return tuple(decision.symbol for decision in self.decisions if not decision.accepted)

    @property
    def accepted_count(self) -> int:
        return len(self.accepted_symbols)

    @property
    def rejected_count(self) -> int:
        return len(self.rejected_symbols)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def has_finite_number(value: object) -> bool:
    return isinstance(value, (int, float)) and isfinite(float(value))


def unique_issues(issues: Iterable[DataQualityIssue]) -> tuple[DataQualityIssue, ...]:
    seen: set[DataQualityIssue] = set()
    ordered: list[DataQualityIssue] = []
    for issue in issues:
        if issue not in seen:
            seen.add(issue)
            ordered.append(issue)
    return tuple(ordered)

