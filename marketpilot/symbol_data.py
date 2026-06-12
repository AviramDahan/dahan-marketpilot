"""SymbolData lifecycle and readiness contracts for Phase 2."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from math import isfinite

from marketpilot.data_quality import DataQualityStatus
from marketpilot.indicators import IndicatorResult, ReadinessStatus


class SymbolLifecycleState(str, Enum):
    ACTIVE = "active"
    REMOVED = "removed"


class IndicatorReadiness(str, Enum):
    READY = "ready"
    MISSING = "missing"
    UNREADY = "unready"
    INVALID = "invalid"
    STALE = "stale"
    DATA_QUALITY_REJECTED = "data_quality_rejected"
    CLEANED_UP = "cleaned_up"


@dataclass
class SymbolData:
    symbol: str
    sector: str | None
    data_quality_status: DataQualityStatus
    indicators: dict[str, IndicatorResult] = field(default_factory=dict)
    last_update: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    lifecycle_state: SymbolLifecycleState = SymbolLifecycleState.ACTIVE
    cleanup_complete: bool = False

    def mark_removed(self) -> None:
        self.lifecycle_state = SymbolLifecycleState.REMOVED
        self.cleanup_complete = True
        self.indicators.clear()

    def missing_indicators(self, required: list[str] | tuple[str, ...]) -> tuple[str, ...]:
        return tuple(name for name in required if name not in self.indicators)

    def readiness_for(self, required: list[str] | tuple[str, ...], stale: bool = False) -> IndicatorReadiness:
        if self.lifecycle_state is SymbolLifecycleState.REMOVED:
            return IndicatorReadiness.CLEANED_UP
        if self.data_quality_status is not DataQualityStatus.ACCEPTED:
            return IndicatorReadiness.DATA_QUALITY_REJECTED
        if stale:
            return IndicatorReadiness.STALE
        if self.missing_indicators(required):
            return IndicatorReadiness.MISSING
        for name in required:
            result = self.indicators[name]
            if result.status is ReadinessStatus.NOT_READY:
                return IndicatorReadiness.UNREADY
            if result.status is ReadinessStatus.INVALID:
                return IndicatorReadiness.INVALID
            if result.value is None or not isfinite(float(result.value)):
                return IndicatorReadiness.INVALID
        return IndicatorReadiness.READY

    def future_signal_ready(self, required: list[str] | tuple[str, ...], stale: bool = False) -> bool:
        return self.readiness_for(required, stale=stale) is IndicatorReadiness.READY

