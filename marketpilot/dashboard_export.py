"""Dashboard export payload builder and Object Store producer/loader."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Mapping

from dashboard.data import (
    OBJECT_STORE_EXPORT_KEYS,
    DashboardDataClient,
)
from dashboard.models import (
    DashboardAuthority,
    DashboardFreshnessStatus,
    DashboardSectionError,
    DashboardSectionStatus,
    DashboardSnapshot,
    DashboardSourceMetadata,
    DashboardCollectionSection,
    DashboardPortfolioSection,
)


APPROVED_OBJECT_STORE_PRODUCER_KEYS = OBJECT_STORE_EXPORT_KEYS


@dataclass(frozen=True)
class DashboardExportPayload:
    """Serializable QuantConnect-authoritative dashboard export payload."""

    source: str = "quantconnect"
    authority: str = "authoritative"
    paper_trading_only: bool = True
    read_only_dashboard: bool = True
    source_timestamp: datetime | None = None
    fixture_label: str = "runtime-export"
    portfolio: Mapping[str, object] = field(default_factory=dict)
    runtime_evidence: Mapping[str, object] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(self._to_dict(), default=_json_default)

    def _to_dict(self) -> dict[str, object]:
        return {
            "source": self.source,
            "authority": self.authority,
            "paper_trading_only": self.paper_trading_only,
            "read_only_dashboard": self.read_only_dashboard,
            "source_timestamp": self.source_timestamp.isoformat() if self.source_timestamp else None,
            "fixture_label": self.fixture_label,
            "portfolio": dict(self.portfolio),
            "runtime_evidence": dict(self.runtime_evidence),
        }


def build_dashboard_export_payload(
    *,
    portfolio: Mapping[str, object],
    runtime_evidence: Mapping[str, object],
    source_timestamp: datetime,
    fixture_label: str = "runtime-export",
) -> DashboardExportPayload:
    """Build a dashboard export payload from QuantConnect-authoritative data."""
    return DashboardExportPayload(
        source="quantconnect",
        authority="authoritative",
        paper_trading_only=True,
        read_only_dashboard=True,
        source_timestamp=source_timestamp,
        fixture_label=fixture_label,
        portfolio=portfolio,
        runtime_evidence=runtime_evidence,
    )


class FakeObjectStoreWriter:
    """Testable Object Store writer that only accepts approved dashboard keys."""

    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    def write(self, key: str, content: str) -> None:
        _assert_approved_key(key)
        self.store[key] = content

    def read(self, key: str) -> str | None:
        _assert_approved_key(key)
        return self.store.get(key)

    def exists(self, key: str) -> bool:
        _assert_approved_key(key)
        return key in self.store


class ObjectStoreSourceLoader:
    """Read-only Object Store source loader for dashboard snapshots."""

    def __init__(
        self,
        writer: FakeObjectStoreWriter,
        *,
        stale_threshold_seconds: int = 1800,
    ) -> None:
        self._store = writer
        self._stale_threshold_seconds = stale_threshold_seconds

    def load_snapshot(
        self,
        *,
        key: str,
        cache_timestamp: datetime,
    ) -> DashboardSnapshot:
        _assert_approved_key(key)

        content = self._store.read(key)
        if content is None:
            return DashboardDataClient.missing_object_store_export(key)

        try:
            payload = json.loads(content)
            if not isinstance(payload, dict):
                raise ValueError("Object Store payload root must be a mapping")
        except Exception as exc:
            return _object_store_error(
                key=key,
                code="object_store_parse_error",
                message=f"Object Store payload parse failed: {exc}",
            )

        try:
            fixture_label = str(payload.get("fixture_label") or "").strip()
            if not fixture_label:
                fixture_label = "object-store-export"

            source_timestamp = _parse_timestamp(payload.get("source_timestamp"))
            freshness = self._evaluate_freshness(source_timestamp, cache_timestamp)

            portfolio_data = payload.get("portfolio") or {}
            if not isinstance(portfolio_data, dict):
                portfolio_data = {}

            # Use the existing DashboardDataClient to parse the full payload
            snapshot = DashboardDataClient.from_quantconnect_portfolio_fixture(
                {
                    "fixture_label": fixture_label,
                    "source_timestamp": payload.get("source_timestamp"),
                    "portfolio": portfolio_data,
                },
                cache_timestamp=cache_timestamp,
            )

            # Override freshness if stale
            if freshness is DashboardFreshnessStatus.STALE:
                metadata = DashboardSourceMetadata(
                    source=snapshot.source_metadata.source,
                    source_timestamp=snapshot.source_metadata.source_timestamp,
                    cache_timestamp=cache_timestamp,
                    freshness_status=DashboardFreshnessStatus.STALE,
                    authority=snapshot.source_metadata.authority,
                    fixture_label=snapshot.source_metadata.fixture_label,
                    reasons=("stale_source_timestamp",),
                )
                snapshot = DashboardSnapshot(
                    source_metadata=metadata,
                    portfolio=snapshot.portfolio,
                    positions=snapshot.positions,
                    trades=snapshot.trades,
                    signals=snapshot.signals,
                    backtests=snapshot.backtests,
                    strategies=snapshot.strategies,
                    risk=snapshot.risk,
                    notifications=snapshot.notifications,
                    activity=snapshot.activity,
                    system=snapshot.system,
                )

            return snapshot

        except Exception as exc:
            return _object_store_error(
                key=key,
                code="object_store_parse_error",
                message=f"Object Store payload processing failed: {exc}",
            )

    def _evaluate_freshness(
        self,
        source_timestamp: datetime | None,
        cache_timestamp: datetime,
    ) -> DashboardFreshnessStatus:
        if source_timestamp is None:
            return DashboardFreshnessStatus.UNKNOWN
        age = (cache_timestamp - source_timestamp).total_seconds()
        if age > self._stale_threshold_seconds:
            return DashboardFreshnessStatus.STALE
        return DashboardFreshnessStatus.FRESH


def _assert_approved_key(key: str) -> None:
    if key not in APPROVED_OBJECT_STORE_PRODUCER_KEYS:
        raise ValueError(f"Key '{key}' is not an approved Object Store dashboard key.")


def _object_store_error(
    *,
    key: str,
    code: str,
    message: str,
) -> DashboardSnapshot:
    error = DashboardSectionError(code=code, message=message)
    reason = f"object_store_error:{key}"
    metadata = DashboardSourceMetadata(
        source="quantconnect_object_store",
        source_timestamp=None,
        cache_timestamp=None,
        freshness_status=DashboardFreshnessStatus.UNKNOWN,
        authority=DashboardAuthority.AUTHORITATIVE,
        reasons=(reason,),
    )
    portfolio = DashboardPortfolioSection(
        status=DashboardSectionStatus.ERROR,
        reasons=(reason,),
        errors=(error,),
    )
    section = DashboardCollectionSection(
        status=DashboardSectionStatus.ERROR,
        reasons=(reason,),
        errors=(error,),
    )
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


def _parse_timestamp(value: object) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))


def _json_default(obj: object) -> object:
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


__all__ = [
    "APPROVED_OBJECT_STORE_PRODUCER_KEYS",
    "DashboardExportPayload",
    "FakeObjectStoreWriter",
    "ObjectStoreSourceLoader",
    "build_dashboard_export_payload",
]
