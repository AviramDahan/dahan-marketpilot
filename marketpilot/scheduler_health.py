"""Scheduler heartbeat and system-health records."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Mapping

from marketpilot.notification_events import NotificationDomainEvent
from marketpilot.scheduler_storage import read_jsonl_records
from marketpilot.sync import atomic_jsonl_append


class SchedulerHealthStatus(str, Enum):
    OK = "ok"
    STALE = "stale"
    MISSING = "missing"


@dataclass(frozen=True)
class SchedulerHeartbeatRecord:
    run_id: str
    timestamp: datetime
    status: str
    last_successful_run_id: str | None = None
    last_attempted_run_id: str | None = None
    missed_run_count: int = 0
    error_summary: str | None = None
    dependency_health: Mapping[str, object] = field(default_factory=dict)
    paper_trading_only: bool = True

    def to_json_dict(self) -> dict[str, object]:
        return {
            "record_type": "scheduler_heartbeat",
            "run_id": self.run_id,
            "timestamp": self.timestamp.astimezone(timezone.utc).isoformat(),
            "status": self.status,
            "last_successful_run_id": self.last_successful_run_id,
            "last_attempted_run_id": self.last_attempted_run_id,
            "missed_run_count": self.missed_run_count,
            "error_summary": self.error_summary,
            "dependency_health": dict(self.dependency_health),
            "paper_trading_only": self.paper_trading_only,
        }


@dataclass(frozen=True)
class SchedulerHealthCheck:
    status: SchedulerHealthStatus
    checked_at: datetime
    latest_heartbeat_at: datetime | None
    age_seconds: int | None
    reason: str | None = None
    latest_record: Mapping[str, object] | None = None

    def to_json_dict(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "checked_at": self.checked_at.astimezone(timezone.utc).isoformat(),
            "latest_heartbeat_at": self.latest_heartbeat_at.astimezone(timezone.utc).isoformat()
            if self.latest_heartbeat_at
            else None,
            "age_seconds": self.age_seconds,
            "reason": self.reason,
            "latest_record": dict(self.latest_record or {}),
        }


def append_scheduler_heartbeat(path: str | Path, record: SchedulerHeartbeatRecord) -> None:
    atomic_jsonl_append(Path(path), record.to_json_dict())


def read_latest_heartbeat(path: str | Path) -> dict[str, object] | None:
    records = [record for record in read_jsonl_records(path) if record.get("record_type") == "scheduler_heartbeat"]
    if not records:
        return None
    return records[-1]


def evaluate_scheduler_heartbeat(
    path: str | Path,
    *,
    now: datetime | None = None,
    max_age_seconds: int = 900,
) -> SchedulerHealthCheck:
    checked_at = _aware_utc(now or datetime.now(timezone.utc))
    latest = read_latest_heartbeat(path)
    if latest is None:
        return SchedulerHealthCheck(
            status=SchedulerHealthStatus.MISSING,
            checked_at=checked_at,
            latest_heartbeat_at=None,
            age_seconds=None,
            reason="heartbeat_missing",
        )

    latest_at = _parse_aware_utc(str(latest["timestamp"]))
    age_seconds = max(0, int((checked_at - latest_at).total_seconds()))
    if age_seconds > max_age_seconds:
        return SchedulerHealthCheck(
            status=SchedulerHealthStatus.STALE,
            checked_at=checked_at,
            latest_heartbeat_at=latest_at,
            age_seconds=age_seconds,
            reason="heartbeat_stale",
            latest_record=latest,
        )
    return SchedulerHealthCheck(
        status=SchedulerHealthStatus.OK,
        checked_at=checked_at,
        latest_heartbeat_at=latest_at,
        age_seconds=age_seconds,
        latest_record=latest,
    )


def event_for_scheduler_health(check: SchedulerHealthCheck, *, correlation_id: str) -> NotificationDomainEvent:
    severity = "warning" if check.status is not SchedulerHealthStatus.OK else "info"
    return NotificationDomainEvent.create(
        "system",
        correlation_id,
        {
            "system_health": "scheduler",
            "status": check.status.value,
            "reason": check.reason,
            "age_seconds": check.age_seconds,
            "controls_safety_logic": False,
            "delivery_required_for_safety": False,
        },
        severity=severity,
        timestamp=check.checked_at,
    )


def _parse_aware_utc(value: str) -> datetime:
    return _aware_utc(datetime.fromisoformat(value.replace("Z", "+00:00")))


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("heartbeat timestamps must be timezone-aware")
    return value.astimezone(timezone.utc)


__all__ = [
    "SchedulerHealthCheck",
    "SchedulerHealthStatus",
    "SchedulerHeartbeatRecord",
    "append_scheduler_heartbeat",
    "evaluate_scheduler_heartbeat",
    "event_for_scheduler_health",
    "read_latest_heartbeat",
]

