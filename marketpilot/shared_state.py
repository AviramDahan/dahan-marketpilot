"""Shared production state adapters for Render-hosted worker/dashboard flows."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Mapping, Protocol

from marketpilot.scheduler_lock import LockAcquireResult, SchedulerLockLease


DEFAULT_REDIS_URL_ENV_VAR = "REDIS_URL"
DEFAULT_NAMESPACE = "marketpilot:v1.1"
DEFAULT_DASHBOARD_KEY = "dashboard:latest"
DEFAULT_ACTIVITY_KEY = "activity"
DEFAULT_LOCK_KEY = "scheduler:lock"


class SharedStateStore(Protocol):
    """JSON-compatible shared store used by Render worker and dashboard."""

    def set_json(self, key: str, payload: Mapping[str, object]) -> None:
        ...

    def get_json(self, key: str) -> dict[str, object] | None:
        ...

    def append_activity(self, payload: Mapping[str, object]) -> None:
        ...

    def read_activity(self, *, limit: int = 50) -> tuple[dict[str, object], ...]:
        ...


@dataclass(frozen=True)
class SharedStateSnapshot:
    key: str
    payload: Mapping[str, object]
    loaded_at: datetime

    def to_json_dict(self) -> dict[str, object]:
        return {
            "key": self.key,
            "payload": dict(self.payload),
            "loaded_at": self.loaded_at.astimezone(timezone.utc).isoformat(),
            "paper_trading_only": True,
        }


class InMemorySharedStateStore:
    """Deterministic shared-store fake for tests and local contract checks."""

    def __init__(self) -> None:
        self.records: dict[str, str] = {}
        self.activity: list[str] = []

    def set_json(self, key: str, payload: Mapping[str, object]) -> None:
        self.records[_normalize_key(key)] = _json_dumps(payload)

    def get_json(self, key: str) -> dict[str, object] | None:
        raw = self.records.get(_normalize_key(key))
        if raw is None:
            return None
        loaded = json.loads(raw)
        if not isinstance(loaded, dict):
            raise ValueError("shared-state payload root must be a mapping")
        return loaded

    def append_activity(self, payload: Mapping[str, object]) -> None:
        self.activity.append(_json_dumps(payload))

    def read_activity(self, *, limit: int = 50) -> tuple[dict[str, object], ...]:
        if limit <= 0:
            return ()
        values = self.activity[-limit:]
        return tuple(json.loads(value) for value in values)

    def publish(self, payload_json: str) -> None:
        payload = _loads_mapping(payload_json)
        self.set_json(DEFAULT_DASHBOARD_KEY, payload)
        self.append_activity(
            {
                "event": "dashboard_export_published",
                "source_timestamp": payload.get("source_timestamp"),
                "paper_trading_only": True,
            }
        )

    def inspect(self) -> SchedulerLockLease | None:
        payload = self.get_json(DEFAULT_LOCK_KEY)
        if payload is None:
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
        self.set_json(DEFAULT_LOCK_KEY, lease.to_json_dict())
        return LockAcquireResult(True, lease)

    def release(self, *, lease: SchedulerLockLease) -> bool:
        current = self.inspect()
        if current is None or current.run_id != lease.run_id or current.owner != lease.owner:
            return False
        self.records.pop(DEFAULT_LOCK_KEY, None)
        return True


class RenderKeyValueStore:
    """Redis/Valkey adapter for Render Key Value."""

    def __init__(self, client: object, *, namespace: str = DEFAULT_NAMESPACE) -> None:
        self._client = client
        self._namespace = _normalize_namespace(namespace)

    @classmethod
    def from_env(cls, *, env: Mapping[str, str] | None = None, namespace: str = DEFAULT_NAMESPACE) -> "RenderKeyValueStore":
        source = env if env is not None else os.environ
        redis_url = str(source.get(DEFAULT_REDIS_URL_ENV_VAR) or "").strip()
        if not redis_url:
            raise ValueError(f"{DEFAULT_REDIS_URL_ENV_VAR} is required for Render Key Value shared state.")
        try:
            import redis
        except ImportError as exc:  # pragma: no cover - dependency presence varies by install target
            raise RuntimeError("redis package is required for Render Key Value shared state.") from exc
        return cls(redis.Redis.from_url(redis_url, decode_responses=True), namespace=namespace)

    def set_json(self, key: str, payload: Mapping[str, object]) -> None:
        self._client.set(self._key(key), _json_dumps(payload))

    def get_json(self, key: str) -> dict[str, object] | None:
        raw = self._client.get(self._key(key))
        if raw is None:
            return None
        loaded = json.loads(str(raw))
        if not isinstance(loaded, dict):
            raise ValueError("shared-state payload root must be a mapping")
        return loaded

    def append_activity(self, payload: Mapping[str, object]) -> None:
        self._client.rpush(self._key(DEFAULT_ACTIVITY_KEY), _json_dumps(payload))

    def read_activity(self, *, limit: int = 50) -> tuple[dict[str, object], ...]:
        if limit <= 0:
            return ()
        values = self._client.lrange(self._key(DEFAULT_ACTIVITY_KEY), -limit, -1)
        return tuple(_loads_mapping(str(value)) for value in values)

    def publish(self, payload_json: str) -> None:
        payload = _loads_mapping(payload_json)
        self.set_json(DEFAULT_DASHBOARD_KEY, payload)
        self.append_activity(
            {
                "event": "dashboard_export_published",
                "source_timestamp": payload.get("source_timestamp"),
                "paper_trading_only": True,
            }
        )

    def inspect(self) -> SchedulerLockLease | None:
        payload = self.get_json(DEFAULT_LOCK_KEY)
        if payload is None:
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
        observed = _aware_utc(now)
        lease = SchedulerLockLease(
            run_id=run_id,
            owner=owner,
            acquired_at=observed,
            expires_at=observed + timedelta(seconds=ttl_seconds),
        )
        stored = self._client.set(self._key(DEFAULT_LOCK_KEY), _json_dumps(lease.to_json_dict()), nx=True, ex=ttl_seconds)
        if stored:
            return LockAcquireResult(True, lease)
        current = self.inspect()
        if current is not None and current.expired(observed):
            self._client.delete(self._key(DEFAULT_LOCK_KEY))
            stored = self._client.set(
                self._key(DEFAULT_LOCK_KEY),
                _json_dumps(lease.to_json_dict()),
                nx=True,
                ex=ttl_seconds,
            )
            if stored:
                return LockAcquireResult(True, lease)
            current = self.inspect()
        return LockAcquireResult(False, current, "lock_already_held")

    def release(self, *, lease: SchedulerLockLease) -> bool:
        current = self.inspect()
        if current is None or current.run_id != lease.run_id or current.owner != lease.owner:
            return False
        self._client.delete(self._key(DEFAULT_LOCK_KEY))
        return True

    def _key(self, key: str) -> str:
        return f"{self._namespace}:{_normalize_key(key)}"


def load_dashboard_payload_from_env(*, env: Mapping[str, str] | None = None) -> SharedStateSnapshot | None:
    """Load the latest dashboard mirror from Render Key Value when configured."""

    source = env if env is not None else os.environ
    if not str(source.get(DEFAULT_REDIS_URL_ENV_VAR) or "").strip():
        return None
    store = RenderKeyValueStore.from_env(env=source)
    payload = store.get_json(DEFAULT_DASHBOARD_KEY)
    if payload is None:
        return None
    return SharedStateSnapshot(
        key=DEFAULT_DASHBOARD_KEY,
        payload=payload,
        loaded_at=datetime.now(timezone.utc),
    )


def _normalize_key(key: str) -> str:
    normalized = str(key).strip().replace("\\", "/").strip("/")
    if not normalized or ".." in normalized.split("/"):
        raise ValueError("shared-state key must be a non-empty relative key.")
    if any(token in normalized.lower() for token in ("token", "password", "secret", "credential")):
        raise ValueError("shared-state key must not contain secret-like names.")
    return normalized


def _normalize_namespace(namespace: str) -> str:
    normalized = str(namespace).strip().strip(":")
    if not normalized:
        raise ValueError("shared-state namespace is required.")
    return normalized


def _loads_mapping(value: str) -> dict[str, object]:
    loaded = json.loads(value)
    if not isinstance(loaded, dict):
        raise ValueError("shared-state JSON payload root must be a mapping.")
    return loaded


def _json_dumps(payload: Mapping[str, object]) -> str:
    return json.dumps(dict(payload), sort_keys=True, default=_json_default)


def _json_default(value: object) -> object:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("shared-state timestamps must be timezone-aware")
    return value.astimezone(timezone.utc)


__all__ = [
    "DEFAULT_ACTIVITY_KEY",
    "DEFAULT_DASHBOARD_KEY",
    "DEFAULT_NAMESPACE",
    "DEFAULT_REDIS_URL_ENV_VAR",
    "InMemorySharedStateStore",
    "RenderKeyValueStore",
    "SharedStateSnapshot",
    "SharedStateStore",
    "load_dashboard_payload_from_env",
]
