"""Positions page view helpers."""

from __future__ import annotations

from dataclasses import dataclass

from dashboard.models import DashboardSectionStatus, DashboardSnapshot


@dataclass(frozen=True)
class PositionsView:
    status: DashboardSectionStatus
    lines: tuple[str, ...]


def build_positions(snapshot: DashboardSnapshot) -> PositionsView:
    lines = [
        f"Authority: {snapshot.source_metadata.authority.value}",
        f"Freshness: {snapshot.source_metadata.freshness_status.value}",
        f"Positions status: {snapshot.positions.status.value}",
        f"Portfolio status: {snapshot.portfolio.status.value}",
    ]
    if snapshot.positions.status is not DashboardSectionStatus.AVAILABLE:
        lines.extend(snapshot.positions.reasons or snapshot.portfolio.reasons or ("not_available",))
    elif snapshot.positions.items:
        for item in snapshot.positions.items:
            quantity = item.get("quantity")
            suffix = f" Quantity: {quantity}" if quantity is not None else ""
            lines.append(f"{item.get('symbol', 'UNKNOWN')}: {item.get('state', 'unknown')}{suffix}")
    elif snapshot.portfolio.holdings:
        for holding in snapshot.portfolio.holdings:
            lines.append(f"{holding.symbol} Quantity: {holding.quantity}")
    else:
        lines.append("No open positions reported by the typed dashboard source.")
    return PositionsView(status=snapshot.positions.status, lines=tuple(lines))
