"""Pure dashboard cache and stale-state helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Mapping

from .redaction import redact_text


class CacheFreshnessLevel(str, Enum):
    FRESH = "fresh"
    STALE_WARNING = "stale_warning"
    STALE_ERROR = "stale_error"
    NOT_AVAILABLE = "not_available"


@dataclass(frozen=True)
class DashboardCacheConfig:
    cache_ttl_seconds: int = 60
    stale_warning_seconds: int = 600
    stale_error_seconds: int = 1800


@dataclass(frozen=True)
class CachedReadFailure:
    has_last_good: bool
    freshness: CacheFreshnessLevel
    source_timestamp: datetime | None
    cache_timestamp: datetime | None
    safe_error: str
    last_good: Mapping[str, object] | None = None


def classify_cache_freshness(
    source_timestamp: datetime | None,
    *,
    now: datetime,
    config: DashboardCacheConfig,
) -> CacheFreshnessLevel:
    if source_timestamp is None:
        return CacheFreshnessLevel.NOT_AVAILABLE
    age_seconds = (now - source_timestamp).total_seconds()
    if age_seconds >= config.stale_error_seconds:
        return CacheFreshnessLevel.STALE_ERROR
    if age_seconds >= config.stale_warning_seconds:
        return CacheFreshnessLevel.STALE_WARNING
    return CacheFreshnessLevel.FRESH


def manual_refresh_actions() -> tuple[str, ...]:
    return ("clear_display_cache", "retry_read")


def handle_source_read_failure(
    *,
    last_good: Mapping[str, object] | None,
    source_timestamp: datetime | None,
    cache_timestamp: datetime | None,
    now: datetime,
    error_message: str,
    config: DashboardCacheConfig | None = None,
) -> CachedReadFailure:
    current_config = config or DashboardCacheConfig()
    freshness = (
        classify_cache_freshness(source_timestamp, now=now, config=current_config)
        if last_good is not None
        else CacheFreshnessLevel.NOT_AVAILABLE
    )
    return CachedReadFailure(
        has_last_good=last_good is not None,
        freshness=freshness,
        source_timestamp=source_timestamp,
        cache_timestamp=cache_timestamp,
        safe_error=redact_text(error_message),
        last_good=last_good,
    )
