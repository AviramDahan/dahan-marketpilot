"""Read-only dashboard data boundary for QuantConnect-sourced state."""

from __future__ import annotations

import json
from datetime import datetime
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


def _decimal(value: object) -> Decimal:
    return Decimal(str(value or "0"))


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


def _list_of_mappings(value: object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))
