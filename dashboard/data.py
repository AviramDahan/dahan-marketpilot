"""Read-only dashboard data boundary for QuantConnect-sourced state."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Mapping

from .config import DashboardConfig
from .models import (
    DashboardAuthority,
    DashboardCollectionSection,
    DashboardFreshnessStatus,
    DashboardHolding,
    DashboardPortfolioSection,
    DashboardSectionError,
    DashboardSectionStatus,
    DashboardSnapshot,
    DashboardSourceMetadata,
)

_logger = logging.getLogger(__name__)


APPROVED_QUANTCONNECT_READ_ENDPOINTS = frozenset(
    {
        "/live/list",
        "/live/portfolio/read",
        "/live/orders/read",
        "/live/insights/read",
        "/live/logs/read",
        "/object/list",
        "/object/properties",
        "/object/get",
    }
)

OBJECT_STORE_EXPORT_KEYS = frozenset(
    {
        "dashboard/portfolio.json",
        "dashboard/positions.json",
        "dashboard/trades.json",
        "dashboard/signals.json",
        "dashboard/backtests.json",
        "dashboard/strategies.json",
        "dashboard/risk.json",
        "dashboard/notifications.json",
        "dashboard/activity.json",
        "dashboard/system.json",
    }
)


class EndpointAccessError(ValueError):
    """Raised when dashboard code attempts to use a non-read QuantConnect endpoint."""


def assert_read_only_endpoint(path: str) -> str:
    normalized = "/" + path.strip().lstrip("/")
    if normalized not in APPROVED_QUANTCONNECT_READ_ENDPOINTS:
        raise EndpointAccessError(f"QuantConnect dashboard endpoint is not approved read-only: {normalized}")
    return normalized


class DashboardDataClient:
    """Pure parsers and degraded-state builders for dashboard data."""

    @staticmethod
    def from_quantconnect_portfolio_fixture(
        payload: Mapping[str, object],
        *,
        cache_timestamp: datetime,
    ) -> DashboardSnapshot:
        fixture_label = str(payload.get("fixture_label") or "").strip()
        if not fixture_label:
            raise ValueError("fixture payloads must keep an explicit fixture label")

        source_timestamp = _parse_datetime(payload.get("source_timestamp"))
        portfolio_payload = _mapping(payload.get("portfolio"))
        holdings = tuple(_parse_holding(item) for item in _list_of_mappings(portfolio_payload.get("holdings")))
        portfolio = DashboardPortfolioSection(
            status=DashboardSectionStatus.AVAILABLE,
            cash=_decimal(portfolio_payload.get("cash")),
            equity=_decimal(portfolio_payload.get("equity")),
            currency=str(portfolio_payload.get("currency") or "USD").strip().upper(),
            holdings=holdings,
        )
        metadata = DashboardSourceMetadata(
            source="quantconnect",
            source_timestamp=source_timestamp,
            cache_timestamp=cache_timestamp,
            freshness_status=DashboardFreshnessStatus.FRESH,
            authority=DashboardAuthority.AUTHORITATIVE,
            fixture_label=fixture_label,
        )
        not_available = _collection(DashboardSectionStatus.NOT_AVAILABLE, "object_store_export_not_loaded")
        return DashboardSnapshot(
            source_metadata=metadata,
            portfolio=portfolio,
            positions=not_available,
            trades=not_available,
            signals=not_available,
            backtests=not_available,
            strategies=not_available,
            risk=not_available,
            notifications=not_available,
            activity=not_available,
            system=not_available,
        )

    @staticmethod
    def not_configured(*, missing: tuple[str, ...]) -> DashboardSnapshot:
        reasons = tuple(missing) or ("missing_quantconnect_configuration",)
        metadata = DashboardSourceMetadata(
            source="quantconnect",
            source_timestamp=None,
            cache_timestamp=None,
            freshness_status=DashboardFreshnessStatus.UNKNOWN,
            authority=DashboardAuthority.AUTHORITATIVE,
            reasons=reasons,
        )
        portfolio = DashboardPortfolioSection(
            status=DashboardSectionStatus.NOT_CONFIGURED,
            reasons=reasons,
        )
        section = _collection(DashboardSectionStatus.NOT_CONFIGURED, *reasons)
        return DashboardSnapshot(
            source_metadata=metadata,
            portfolio=portfolio,
            positions=section,
            trades=section,
            signals=section,
            backtests=section,
            strategies=section,
            risk=section,
            notifications=section,
            activity=section,
            system=section,
        )

    @staticmethod
    def missing_object_store_export(key: str) -> DashboardSnapshot:
        reason = f"missing_object_store_export:{key}"
        metadata = DashboardSourceMetadata(
            source="quantconnect_object_store",
            source_timestamp=None,
            cache_timestamp=None,
            freshness_status=DashboardFreshnessStatus.UNKNOWN,
            authority=DashboardAuthority.AUTHORITATIVE,
            reasons=(reason,),
        )
        section = _collection(DashboardSectionStatus.NOT_AVAILABLE, reason)
        return DashboardSnapshot(
            source_metadata=metadata,
            portfolio=DashboardPortfolioSection(
                status=DashboardSectionStatus.NOT_AVAILABLE,
                reasons=(reason,),
            ),
            positions=section,
            trades=section,
            signals=section,
            backtests=section,
            strategies=section,
            risk=section,
            notifications=section,
            activity=section,
            system=section,
        )


def load_dashboard_snapshot(config: DashboardConfig, *, now: datetime) -> DashboardSnapshot:
    """Load the configured read-only dashboard snapshot or return an honest degraded state."""

    if config.data_source_kind == "none":
        return DashboardDataClient.not_configured(missing=("dashboard_data_source",))

    if config.data_source_kind == "local_json":
        return _load_local_json_snapshot(config.data_source_path, cache_timestamp=now)

    if config.data_source_kind == "object_store":
        return _load_object_store_snapshot(config.data_source_path, cache_timestamp=now)

    if config.data_source_kind == "sync_jsonl":
        return _load_sync_jsonl_snapshot(config.data_source_path, config=config, cache_timestamp=now)

    return _source_error(
        code="dashboard_source_not_configured",
        message="Unsupported dashboard data source kind.",
        reason="dashboard_data_source",
    )


def _collection(status: DashboardSectionStatus, *reasons: str) -> DashboardCollectionSection:
    return DashboardCollectionSection(status=status, reasons=tuple(reasons))


def _load_local_json_snapshot(path_value: str | None, *, cache_timestamp: datetime) -> DashboardSnapshot:
    if not path_value:
        return DashboardDataClient.not_configured(missing=("dashboard_data_source",))
    path = Path(path_value)
    if not path.exists():
        return _source_error(
            code="dashboard_source_missing",
            message=f"Dashboard data source is not available: {path}",
            reason="missing_dashboard_data_source",
            status=DashboardSectionStatus.NOT_AVAILABLE,
        )
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if not isinstance(payload, Mapping):
            raise ValueError("dashboard source root must be a mapping")
        return DashboardDataClient.from_quantconnect_portfolio_fixture(
            payload,
            cache_timestamp=cache_timestamp,
        )
    except Exception as exc:
        return _source_error(
            code="dashboard_source_error",
            message=f"Dashboard data source read failed: {exc}",
            reason="dashboard_source_error",
            status=DashboardSectionStatus.ERROR,
        )


def _load_sync_jsonl_snapshot(
    path_value: str | None,
    *,
    config: DashboardConfig,
    cache_timestamp: datetime,
) -> DashboardSnapshot:
    if not path_value:
        return DashboardDataClient.not_configured(missing=("dashboard_data_source",))
    path = Path(path_value)
    if not path.exists() or path.stat().st_size == 0:
        return _sync_source_error(
            code="sync_no_data",
            message="No sync data available - run python -m marketpilot sync to start",
            reason="no_sync_data",
            status=DashboardSectionStatus.NOT_AVAILABLE,
        )

    try:
        record = _read_last_sync_jsonl_record(path)
    except Exception as exc:
        return _sync_source_error(
            code="sync_parse_error",
            message=f"Sync JSONL record parse failed: {exc}",
            reason="sync_parse_error",
            status=DashboardSectionStatus.ERROR,
        )
    if record is None:
        return _sync_source_error(
            code="sync_no_data",
            message="No sync data available - run python -m marketpilot sync to start",
            reason="no_sync_data",
            status=DashboardSectionStatus.NOT_AVAILABLE,
        )

    try:
        return _snapshot_from_sync_record(record, config=config, cache_timestamp=cache_timestamp)
    except Exception as exc:
        return _sync_source_error(
            code="sync_parse_error",
            message=f"Sync JSONL record processing failed: {exc}",
            reason="sync_parse_error",
            status=DashboardSectionStatus.ERROR,
        )


def _read_last_sync_jsonl_record(path: Path) -> Mapping[str, object] | None:
    with path.open("rb") as handle:
        handle.seek(0, 2)
        size = handle.tell()
        if size == 0:
            return None
        chunk_size = min(size, 4096)
        handle.seek(-chunk_size, 2)
        chunk = handle.read().decode("utf-8")
    lines = [line.strip() for line in chunk.splitlines() if line.strip()]
    if not lines:
        return None
    payload = json.loads(lines[-1])
    if not isinstance(payload, Mapping):
        raise ValueError("sync JSONL record root must be a mapping")
    return payload


def _snapshot_from_sync_record(
    record: Mapping[str, object],
    *,
    config: DashboardConfig,
    cache_timestamp: datetime,
) -> DashboardSnapshot:
    portfolio_payload = _mapping_or_raise(record.get("portfolio"), "portfolio")
    source_timestamp = _parse_utc_datetime(record.get("source_timestamp"))
    freshness = _evaluate_sync_freshness(
        source_timestamp,
        cache_timestamp,
        warning_seconds=config.stale_warning_seconds,
        error_seconds=config.stale_error_seconds,
    )
    reasons = _sync_metadata_reasons(record, freshness)
    portfolio = DashboardPortfolioSection(
        status=_portfolio_status_for_freshness(freshness),
        cash=_optional_decimal(portfolio_payload.get("cash")),
        equity=_optional_decimal(portfolio_payload.get("equity")),
        currency=str(portfolio_payload.get("currency") or "USD").strip().upper(),
        holdings=tuple(_parse_sync_holding(item) for item in _list_of_mappings(portfolio_payload.get("holdings"))),
        reasons=reasons,
    )
    metadata = DashboardSourceMetadata(
        source="quantconnect_sync_jsonl",
        source_timestamp=source_timestamp,
        cache_timestamp=_ensure_utc(cache_timestamp),
        freshness_status=freshness,
        authority=DashboardAuthority.AUTHORITATIVE,
        reasons=reasons,
    )
    not_available = _collection(DashboardSectionStatus.NOT_AVAILABLE, "sync_jsonl_section_not_loaded")
    return DashboardSnapshot(
        source_metadata=metadata,
        portfolio=portfolio,
        positions=not_available,
        trades=not_available,
        signals=not_available,
        backtests=not_available,
        strategies=not_available,
        risk=not_available,
        notifications=not_available,
        activity=not_available,
        system=not_available,
    )


def _sync_metadata_reasons(
    record: Mapping[str, object],
    freshness: DashboardFreshnessStatus,
) -> tuple[str, ...]:
    reasons: list[str] = []
    generation = record.get("generation")
    if not isinstance(generation, int) or generation <= 0:
        _logger.warning("sync_jsonl record is missing a positive generation counter")
        reasons.append("sync_generation_missing_or_zero")
    if freshness is DashboardFreshnessStatus.STALE:
        reasons.append("stale_source_timestamp")
    elif freshness is DashboardFreshnessStatus.ERROR:
        reasons.append("error_source_timestamp")
    elif freshness is DashboardFreshnessStatus.UNKNOWN:
        reasons.append("unknown_source_timestamp")
    return tuple(reasons)


def _portfolio_status_for_freshness(freshness: DashboardFreshnessStatus) -> DashboardSectionStatus:
    if freshness is DashboardFreshnessStatus.ERROR:
        return DashboardSectionStatus.ERROR
    if freshness is DashboardFreshnessStatus.STALE:
        return DashboardSectionStatus.STALE
    return DashboardSectionStatus.AVAILABLE


def _evaluate_sync_freshness(
    source_timestamp: datetime | None,
    cache_timestamp: datetime,
    *,
    warning_seconds: int,
    error_seconds: int,
) -> DashboardFreshnessStatus:
    if source_timestamp is None:
        return DashboardFreshnessStatus.UNKNOWN
    now = _ensure_utc(cache_timestamp)
    age_seconds = (now - source_timestamp).total_seconds()
    if age_seconds <= warning_seconds:
        return DashboardFreshnessStatus.FRESH
    if age_seconds <= error_seconds:
        return DashboardFreshnessStatus.STALE
    return DashboardFreshnessStatus.ERROR


def _parse_sync_holding(payload: Mapping[str, object]) -> DashboardHolding:
    symbol = str(payload.get("symbol") or "").strip()
    if not symbol:
        raise ValueError("sync holding symbol is required")
    return DashboardHolding(
        symbol=symbol,
        quantity=_required_int(payload.get("quantity"), "holding.quantity"),
        average_price=_required_decimal(payload.get("average_price"), "holding.average_price"),
        market_price=_required_decimal(payload.get("market_price"), "holding.market_price"),
    )


def _sync_source_error(
    *,
    code: str,
    message: str,
    reason: str,
    status: DashboardSectionStatus,
) -> DashboardSnapshot:
    error = DashboardSectionError(code=code, message=message)
    metadata = DashboardSourceMetadata(
        source="quantconnect_sync_jsonl",
        source_timestamp=None,
        cache_timestamp=None,
        freshness_status=DashboardFreshnessStatus.UNKNOWN,
        authority=DashboardAuthority.AUTHORITATIVE,
        reasons=(reason,),
    )
    portfolio = DashboardPortfolioSection(status=status, reasons=(reason,), errors=(error,))
    section = DashboardCollectionSection(status=status, reasons=(reason,), errors=(error,))
    return DashboardSnapshot(
        source_metadata=metadata,
        portfolio=portfolio,
        positions=section,
        trades=section,
        signals=section,
        backtests=section,
        strategies=section,
        risk=section,
        notifications=section,
        activity=section,
        system=section,
    )


def _source_error(
    *,
    code: str,
    message: str,
    reason: str,
    status: DashboardSectionStatus = DashboardSectionStatus.ERROR,
) -> DashboardSnapshot:
    error = DashboardSectionError(code=code, message=message)
    metadata = DashboardSourceMetadata(
        source="dashboard_runtime_source",
        source_timestamp=None,
        cache_timestamp=None,
        freshness_status=DashboardFreshnessStatus.UNKNOWN,
        authority=DashboardAuthority.AUTHORITATIVE,
        reasons=(reason,),
    )
    portfolio = DashboardPortfolioSection(status=status, reasons=(reason,), errors=(error,))
    section = DashboardCollectionSection(status=status, reasons=(reason,), errors=(error,))
    return DashboardSnapshot(
        source_metadata=metadata,
        portfolio=portfolio,
        positions=section,
        trades=section,
        signals=section,
        backtests=section,
        strategies=section,
        risk=section,
        notifications=section,
        activity=section,
        system=section,
    )


def _parse_holding(payload: Mapping[str, object]) -> DashboardHolding:
    return DashboardHolding(
        symbol=str(payload.get("symbol") or ""),
        quantity=int(payload.get("quantity") or 0),
        average_price=_decimal(payload.get("average_price")),
        market_price=_decimal(payload.get("market_price")),
    )


def _parse_datetime(value: object) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))


def _parse_utc_datetime(value: object) -> datetime | None:
    try:
        parsed = _parse_datetime(value)
    except (TypeError, ValueError):
        return None
    if parsed is None:
        return None
    return _ensure_utc(parsed)


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _decimal(value: object) -> Decimal:
    return Decimal(str(value or "0"))


def _optional_decimal(value: object) -> Decimal | None:
    if value in (None, ""):
        return None
    return Decimal(str(value))


def _required_decimal(value: object, field_name: str) -> Decimal:
    parsed = _optional_decimal(value)
    if parsed is None:
        raise ValueError(f"{field_name} is required")
    return parsed


def _required_int(value: object, field_name: str) -> int:
    if value in (None, ""):
        raise ValueError(f"{field_name} is required")
    return int(value)


def _load_object_store_snapshot(key: str | None, *, cache_timestamp: datetime) -> DashboardSnapshot:
    """Object Store source loader stub - requires external writer injection at runtime."""
    if not key:
        return _source_error(
            code="object_store_not_configured",
            message="Object Store source path not configured.",
            reason="object_store_not_configured",
            status=DashboardSectionStatus.NOT_AVAILABLE,
        )
    # Without an injected Object Store writer, degrade safely.
    # Real Object Store reads happen through ObjectStoreSourceLoader in
    # marketpilot.dashboard_export with a writer injected at runtime.
    return _source_error(
        code="object_store_not_configured",
        message="Object Store reader not configured at runtime.",
        reason="object_store_not_configured",
        status=DashboardSectionStatus.NOT_AVAILABLE,
    )


def _mapping(value: object) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return value
    return {}


def _mapping_or_raise(value: object, field_name: str) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return value
    raise ValueError(f"sync JSONL field '{field_name}' must be a mapping")


def _list_of_mappings(value: object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))
