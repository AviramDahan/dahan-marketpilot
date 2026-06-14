"""Dashboard state and read-only data contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Mapping

from marketpilot.constants import DISCLAIMER

from .redaction import redact_mapping, redact_text


@dataclass(frozen=True)
class DashboardSafetyState:
    title: str = "Dahan MarketPilot"
    disclaimer: str = DISCLAIMER
    paper_only_status: str = "Paper-only safety mode"
    read_only_status: str = "Read-only dashboard shell"
    data_status: str = "No live data connected"
    scope_note: str = "Phase 1 displays safety state only."


def default_safety_state() -> DashboardSafetyState:
    return DashboardSafetyState()


class DashboardAuthority(str, Enum):
    AUTHORITATIVE = "authoritative"
    DISPLAY_ONLY = "display_only"


class DashboardFreshnessStatus(str, Enum):
    FRESH = "fresh"
    STALE = "stale"
    UNKNOWN = "unknown"


class DashboardSectionStatus(str, Enum):
    AVAILABLE = "available"
    NOT_CONFIGURED = "not_configured"
    NOT_AVAILABLE = "not_available"
    STALE = "stale"
    ERROR = "error"


@dataclass(frozen=True)
class DashboardSourceMetadata:
    source: str
    source_timestamp: datetime | None
    cache_timestamp: datetime | None
    freshness_status: DashboardFreshnessStatus
    authority: DashboardAuthority
    fixture_label: str | None = None
    reasons: tuple[str, ...] = field(default_factory=tuple)

    @property
    def is_fixture(self) -> bool:
        return self.fixture_label is not None

    def to_safe_dict(self) -> dict[str, object]:
        return {
            "source": self.source,
            "source_timestamp": self.source_timestamp.isoformat() if self.source_timestamp else None,
            "cache_timestamp": self.cache_timestamp.isoformat() if self.cache_timestamp else None,
            "freshness_status": self.freshness_status.value,
            "authority": self.authority.value,
            "fixture_label": self.fixture_label,
            "reasons": self.reasons,
        }


@dataclass(frozen=True)
class DashboardSectionError:
    code: str
    message: str
    detail: Mapping[str, object] = field(default_factory=dict)
    secret_values: tuple[str, ...] = field(default_factory=tuple, repr=False)

    def to_safe_dict(self) -> dict[str, object]:
        return {
            "code": self.code,
            "message": redact_text(self.message, secret_values=self.secret_values),
            "detail": redact_mapping(self.detail),
        }


@dataclass(frozen=True)
class DashboardHolding:
    symbol: str
    quantity: int
    average_price: Decimal
    market_price: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(self, "symbol", self.symbol.strip().upper())


@dataclass(frozen=True)
class DashboardPortfolioSection:
    status: DashboardSectionStatus
    cash: Decimal | None = None
    equity: Decimal | None = None
    currency: str = "USD"
    holdings: tuple[DashboardHolding, ...] = field(default_factory=tuple)
    reasons: tuple[str, ...] = field(default_factory=tuple)
    errors: tuple[DashboardSectionError, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class DashboardCollectionSection:
    status: DashboardSectionStatus
    items: tuple[Mapping[str, object], ...] = field(default_factory=tuple)
    reasons: tuple[str, ...] = field(default_factory=tuple)
    errors: tuple[DashboardSectionError, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class DashboardSnapshot:
    source_metadata: DashboardSourceMetadata
    portfolio: DashboardPortfolioSection
    positions: DashboardCollectionSection = field(
        default_factory=lambda: DashboardCollectionSection(DashboardSectionStatus.NOT_AVAILABLE)
    )
    trades: DashboardCollectionSection = field(
        default_factory=lambda: DashboardCollectionSection(DashboardSectionStatus.NOT_AVAILABLE)
    )
    signals: DashboardCollectionSection = field(
        default_factory=lambda: DashboardCollectionSection(DashboardSectionStatus.NOT_AVAILABLE)
    )
    backtests: DashboardCollectionSection = field(
        default_factory=lambda: DashboardCollectionSection(DashboardSectionStatus.NOT_AVAILABLE)
    )
    strategies: DashboardCollectionSection = field(
        default_factory=lambda: DashboardCollectionSection(DashboardSectionStatus.NOT_AVAILABLE)
    )
    risk: DashboardCollectionSection = field(
        default_factory=lambda: DashboardCollectionSection(DashboardSectionStatus.NOT_AVAILABLE)
    )
    notifications: DashboardCollectionSection = field(
        default_factory=lambda: DashboardCollectionSection(DashboardSectionStatus.NOT_AVAILABLE)
    )
    activity: DashboardCollectionSection = field(
        default_factory=lambda: DashboardCollectionSection(DashboardSectionStatus.NOT_AVAILABLE)
    )
    system: DashboardCollectionSection = field(
        default_factory=lambda: DashboardCollectionSection(DashboardSectionStatus.NOT_AVAILABLE)
    )

    def sections(self) -> tuple[DashboardPortfolioSection | DashboardCollectionSection, ...]:
        return (
            self.portfolio,
            self.positions,
            self.trades,
            self.signals,
            self.backtests,
            self.strategies,
            self.risk,
            self.notifications,
            self.activity,
            self.system,
        )
