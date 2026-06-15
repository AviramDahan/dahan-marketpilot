"""Display-only USD/NIS helpers for dashboard values."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum


class FxDisplayStatus(str, Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    STALE = "stale"


@dataclass(frozen=True)
class FxDisplay:
    status: FxDisplayStatus
    usd_text: str
    nis_text: str
    fx_source: str | None
    fx_timestamp: datetime | None
    reason: str | None = None


def render_usd_nis(
    usd_amount: Decimal,
    *,
    fx_rate: Decimal | None,
    fx_source: str | None,
    fx_timestamp: datetime | None,
    now: datetime,
    stale_after_seconds: int = 86400,
) -> FxDisplay:
    usd_text = f"USD {_money(usd_amount)}"
    if fx_rate is None or fx_source is None or fx_timestamp is None:
        return FxDisplay(
            status=FxDisplayStatus.UNAVAILABLE,
            usd_text=usd_text,
            nis_text="NIS unavailable",
            fx_source=fx_source,
            fx_timestamp=fx_timestamp,
            reason="missing_fx_metadata",
        )

    if (now - fx_timestamp).total_seconds() >= stale_after_seconds:
        return FxDisplay(
            status=FxDisplayStatus.STALE,
            usd_text=usd_text,
            nis_text="NIS stale",
            fx_source=fx_source,
            fx_timestamp=fx_timestamp,
            reason="stale_fx_metadata",
        )

    nis_amount = usd_amount * fx_rate
    return FxDisplay(
        status=FxDisplayStatus.AVAILABLE,
        usd_text=usd_text,
        nis_text=f"NIS {_money(nis_amount)}",
        fx_source=fx_source,
        fx_timestamp=fx_timestamp,
    )


def _money(value: Decimal) -> str:
    return str(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
