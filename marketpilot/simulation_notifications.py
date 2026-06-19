from __future__ import annotations

"""Simulation-only notification builders."""

from datetime import date, datetime
from typing import Mapping

from marketpilot.notification_events import NotificationDomainEvent, event_for_alert_family


def simulation_candidate_event(
    *,
    correlation_id: str,
    candidate: Mapping[str, object],
    timestamp: datetime | None = None,
) -> NotificationDomainEvent:
    payload = _simulation_payload(candidate, artifact="scanner_candidate")
    return event_for_alert_family("buy_candidate", correlation_id, payload, timestamp=timestamp)


def simulation_entry_event(
    *,
    correlation_id: str,
    position: Mapping[str, object],
    timestamp: datetime | None = None,
) -> NotificationDomainEvent:
    payload = _simulation_payload(position, artifact="simulated_entry")
    return event_for_alert_family("paper_buy", correlation_id, payload, timestamp=timestamp)


def simulation_exit_event(
    *,
    correlation_id: str,
    trade: Mapping[str, object],
    exit_reason: str,
    timestamp: datetime | None = None,
) -> NotificationDomainEvent:
    family = "target" if exit_reason == "target" else "stop" if exit_reason == "stop" else "full_close"
    payload = _simulation_payload(trade, artifact="simulated_exit", exit_reason=exit_reason)
    return event_for_alert_family(family, correlation_id, payload, timestamp=timestamp)


def simulation_system_event(
    *,
    correlation_id: str,
    status: str,
    detail: str,
    timestamp: datetime | None = None,
) -> NotificationDomainEvent:
    payload = _simulation_payload({"system_health": status, "detail": detail}, artifact="simulation_system")
    return event_for_alert_family("system", correlation_id, payload, timestamp=timestamp)


def simulation_daily_summary_event(
    *,
    correlation_id: str,
    summary_date: date,
    new_candidates: int,
    entries: int,
    exits: int,
    open_positions: int,
    warnings: tuple[str, ...] = (),
    timestamp: datetime | None = None,
) -> NotificationDomainEvent:
    payload = _simulation_payload(
        {
            "summary_date": summary_date.isoformat(),
            "new_candidates": new_candidates,
            "entries": entries,
            "exits": exits,
            "open_positions": open_positions,
            "system_warnings": warnings,
        },
        artifact="simulation_daily_summary",
    )
    return event_for_alert_family("daily_summary", correlation_id, payload, timestamp=timestamp)


def _simulation_payload(payload: Mapping[str, object], **extra: object) -> dict[str, object]:
    return {
        "product_mode": "simulation_only",
        "simulation_only": True,
        "paper_trading_only": True,
        "not_financial_advice": True,
        "real_order": False,
        "quantconnect_order": False,
        "controls_safety_logic": False,
        "delivery_required_for_safety": False,
        **extra,
        **dict(payload),
    }


__all__ = [
    "simulation_candidate_event",
    "simulation_daily_summary_event",
    "simulation_entry_event",
    "simulation_exit_event",
    "simulation_system_event",
]
