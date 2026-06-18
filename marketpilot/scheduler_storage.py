from __future__ import annotations

"""Append-only scheduler run storage and idempotency helpers."""


import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping

from marketpilot.scheduler_jobs import SchedulerJobResult
from marketpilot.sync import atomic_jsonl_append


@dataclass(frozen=True)
class SchedulerLedgerRecord:
    record_type: str
    run_id: str
    idempotency_key: str
    timestamp: datetime
    payload: Mapping[str, object] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "record_type": self.record_type,
            "run_id": self.run_id,
            "idempotency_key": self.idempotency_key,
            "timestamp": self.timestamp.astimezone(timezone.utc).isoformat(),
            "payload": dict(self.payload),
        }


class JsonlSchedulerStorage:
    """Append-only local storage adapter ready to be swapped in Phase 16.1."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def append_record(self, record: SchedulerLedgerRecord) -> None:
        atomic_jsonl_append(self.path, record.to_json_dict())

    def append_run_started(self, *, run_id: str, scheduled_for: datetime, started_at: datetime) -> None:
        self.append_record(
            SchedulerLedgerRecord(
                record_type="run_started",
                run_id=run_id,
                idempotency_key=build_idempotency_key("run", run_id),
                timestamp=started_at,
                payload={
                    "scheduled_for": _utc_iso(scheduled_for),
                    "started_at": _utc_iso(started_at),
                    "paper_trading_only": True,
                },
            )
        )

    def append_job_result(self, *, run_id: str, result: SchedulerJobResult) -> None:
        self.append_record(
            SchedulerLedgerRecord(
                record_type="job_result",
                run_id=run_id,
                idempotency_key=build_idempotency_key("job", run_id, result.job_id.value),
                timestamp=result.ended_at,
                payload=result.to_json_dict(),
            )
        )

    def append_run_finished(
        self,
        *,
        run_id: str,
        scheduled_for: datetime,
        started_at: datetime,
        ended_at: datetime,
        status: str,
        payload: Mapping[str, object] | None = None,
    ) -> None:
        self.append_record(
            SchedulerLedgerRecord(
                record_type="run_finished",
                run_id=run_id,
                idempotency_key=build_idempotency_key("run-finished", run_id),
                timestamp=ended_at,
                payload={
                    "scheduled_for": _utc_iso(scheduled_for),
                    "started_at": _utc_iso(started_at),
                    "ended_at": _utc_iso(ended_at),
                    "status": status,
                    "paper_trading_only": True,
                }
                | dict(payload or {}),
            )
        )

    def append_missed_cycle(self, *, run_id: str, scheduled_for: datetime, observed_at: datetime, reason: str) -> None:
        self.append_record(
            SchedulerLedgerRecord(
                record_type="missed_cycle",
                run_id=run_id,
                idempotency_key=build_idempotency_key("missed", run_id),
                timestamp=observed_at,
                payload={
                    "scheduled_for": _utc_iso(scheduled_for),
                    "observed_at": _utc_iso(observed_at),
                    "reason": reason,
                    "order_creation_allowed": False,
                    "paper_trading_only": True,
                },
            )
        )

    def read_records(self) -> tuple[dict[str, object], ...]:
        return tuple(read_jsonl_records(self.path))

    def has_idempotency_key(self, key: str) -> bool:
        return any(record.get("idempotency_key") == key for record in self.read_records())


def build_run_id(scheduled_for: datetime) -> str:
    value = scheduled_for.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"mp-run-{value}"


def build_idempotency_key(*parts: object) -> str:
    normalized = "|".join(str(part).strip() for part in parts)
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:24]
    return f"scheduler-{digest}"


def read_jsonl_records(path: str | Path) -> Iterable[dict[str, object]]:
    file_path = Path(path)
    if not file_path.exists():
        return ()
    records: list[dict[str, object]] = []
    for line in file_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if isinstance(record, dict):
            records.append(record)
    return tuple(records)


def _utc_iso(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("scheduler timestamps must be timezone-aware")
    return value.astimezone(timezone.utc).isoformat()


__all__ = [
    "JsonlSchedulerStorage",
    "SchedulerLedgerRecord",
    "build_idempotency_key",
    "build_run_id",
    "read_jsonl_records",
]

