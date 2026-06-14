"""Append-only JSONL audit journal contracts."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping


@dataclass(frozen=True)
class AuditJournalRecord:
    event_type: str
    timestamp: datetime
    correlation_id: str
    payload: Mapping[str, object]
    config_version: str = "unverified-local-config"
    strategy_version: str = "unverified-local-strategy"

    def to_json_dict(self) -> dict[str, object]:
        if not self.event_type.strip():
            raise ValueError("event_type is required.")
        if not self.correlation_id.strip():
            raise ValueError("correlation_id is required.")
        data = asdict(self)
        data["timestamp"] = self.timestamp.astimezone(timezone.utc).isoformat()
        data["payload"] = _sanitize_payload(self.payload)
        return data


class AppendOnlyJsonlAuditJournal:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def append(self, record: AuditJournalRecord) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(record.to_json_dict(), sort_keys=True) + "\n")

    def read_records(self) -> tuple[dict[str, object], ...]:
        if not self.path.exists():
            return ()
        records = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    records.append(json.loads(line))
        return tuple(records)


def _sanitize_payload(payload: Mapping[str, object]) -> dict[str, object]:
    sanitized: dict[str, object] = {}
    for key, value in payload.items():
        if any(marker in key.lower() for marker in ("secret", "token", "password", "credential", "api_key")):
            sanitized[key] = "[redacted]"
        else:
            sanitized[key] = value
    return sanitized
