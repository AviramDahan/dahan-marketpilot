from __future__ import annotations

"""Lease-based local scheduler lock contract."""


import json
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Mapping


@dataclass(frozen=True)
class SchedulerLockLease:
    run_id: str
    owner: str
    acquired_at: datetime
    expires_at: datetime

    @classmethod
    def from_json_dict(cls, payload: Mapping[str, object]) -> "SchedulerLockLease":
        return cls(
            run_id=str(payload["run_id"]),
            owner=str(payload["owner"]),
            acquired_at=_parse_aware_utc(str(payload["acquired_at"])),
            expires_at=_parse_aware_utc(str(payload["expires_at"])),
        )

    def to_json_dict(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "owner": self.owner,
            "acquired_at": self.acquired_at.astimezone(timezone.utc).isoformat(),
            "expires_at": self.expires_at.astimezone(timezone.utc).isoformat(),
        }

    def expired(self, now: datetime) -> bool:
        return self.expires_at <= _aware_utc(now)


@dataclass(frozen=True)
class LockAcquireResult:
    acquired: bool
    lease: SchedulerLockLease | None
    reason: str | None = None


class FileLockStore:
    """A small lease lock adapter for local/Render-worker single instance use."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def inspect(self) -> SchedulerLockLease | None:
        if not self.path.exists():
            return None
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            return None
        return SchedulerLockLease.from_json_dict(payload)

    def acquire(
        self,
        *,
        run_id: str,
        owner: str,
        now: datetime,
        ttl_seconds: int,
    ) -> LockAcquireResult:
        current = self.inspect()
        observed = _aware_utc(now)
        if current is not None and not current.expired(observed):
            return LockAcquireResult(False, current, "lock_already_held")

        lease = SchedulerLockLease(
            run_id=run_id,
            owner=owner,
            acquired_at=observed,
            expires_at=observed + timedelta(seconds=ttl_seconds),
        )
        self._write(lease)
        return LockAcquireResult(True, lease)

    def renew(self, *, lease: SchedulerLockLease, now: datetime, ttl_seconds: int) -> bool:
        current = self.inspect()
        if current is None or current.run_id != lease.run_id or current.owner != lease.owner:
            return False
        renewed = SchedulerLockLease(
            run_id=lease.run_id,
            owner=lease.owner,
            acquired_at=lease.acquired_at,
            expires_at=_aware_utc(now) + timedelta(seconds=ttl_seconds),
        )
        self._write(renewed)
        return True

    def release(self, *, lease: SchedulerLockLease) -> bool:
        current = self.inspect()
        if current is None or current.run_id != lease.run_id or current.owner != lease.owner:
            return False
        self.path.unlink(missing_ok=True)
        return True

    def _write(self, lease: SchedulerLockLease) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(dir=self.path.parent, prefix=".scheduler_lock_", suffix=".tmp")
        tmp_name = str(tmp_path)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                fd = -1
                json.dump(lease.to_json_dict(), handle, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_name, self.path)
        finally:
            if fd >= 0:
                os.close(fd)
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("lock timestamps must be timezone-aware")
    return value.astimezone(timezone.utc)


def _parse_aware_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return _aware_utc(parsed)


__all__ = [
    "FileLockStore",
    "LockAcquireResult",
    "SchedulerLockLease",
]

