"""Trades page view helpers."""

from __future__ import annotations

from dataclasses import dataclass

from dashboard.models import DashboardSectionStatus, DashboardSnapshot


@dataclass(frozen=True)
class TradesView:
    status: DashboardSectionStatus
    lines: tuple[str, ...]


def build_trades(snapshot: DashboardSnapshot) -> TradesView:
    lines = [
        "QuantConnect authority for trade, fill, and activity records.",
        f"Freshness: {snapshot.source_metadata.freshness_status.value}",
        f"Trades status: {snapshot.trades.status.value}",
    ]
    if snapshot.trades.status is not DashboardSectionStatus.AVAILABLE:
        lines.extend(snapshot.trades.reasons or snapshot.portfolio.reasons or ("not_available",))
    elif snapshot.trades.items:
        for item in snapshot.trades.items:
            lines.append(
                f"{item.get('record_type', 'record')}: {item.get('symbol', 'UNKNOWN')} "
                f"Quantity: {item.get('quantity', 'unknown')}"
            )
    else:
        lines.append("No trade records reported by the typed dashboard source.")
    return TradesView(status=snapshot.trades.status, lines=tuple(lines))
