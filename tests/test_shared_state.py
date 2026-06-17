from datetime import datetime, timedelta, timezone

import pytest

from marketpilot.shared_state import DEFAULT_DASHBOARD_KEY, InMemorySharedStateStore, RenderKeyValueStore


class FakeRedis:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.lists: dict[str, list[str]] = {}
        self.calls: list[tuple[str, tuple[object, ...], dict[str, object]]] = []

    def set(self, key, value, nx=False, ex=None):
        self.calls.append(("set", (key, value), {"nx": nx, "ex": ex}))
        if nx and key in self.values:
            return False
        self.values[key] = value
        return True

    def get(self, key):
        return self.values.get(key)

    def delete(self, key):
        self.values.pop(key, None)

    def rpush(self, key, value):
        self.lists.setdefault(key, []).append(value)

    def lrange(self, key, start, end):
        values = self.lists.get(key, [])
        if start < 0:
            start = max(0, len(values) + start)
        if end == -1:
            return values[start:]
        return values[start : end + 1]


def _payload() -> dict[str, object]:
    return {
        "fixture_label": "scheduler-production-cycle",
        "source_timestamp": "2026-06-16T14:00:00+00:00",
        "portfolio": {"cash": "100000.00", "equity": "100000.00", "currency": "USD", "holdings": []},
        "paper_trading_only": True,
    }


def test_in_memory_shared_state_publishes_dashboard_payload_and_activity():
    store = InMemorySharedStateStore()

    store.publish('{"fixture_label":"scheduler-production-cycle","paper_trading_only":true}')

    assert store.get_json(DEFAULT_DASHBOARD_KEY)["fixture_label"] == "scheduler-production-cycle"
    assert store.read_activity(limit=1)[0]["event"] == "dashboard_export_published"


def test_render_key_value_store_namespaces_json_and_activity_without_logging_url():
    redis = FakeRedis()
    store = RenderKeyValueStore(redis, namespace="marketpilot:test")

    store.set_json("dashboard/portfolio", _payload())
    store.append_activity({"event": "published", "paper_trading_only": True})

    assert redis.get("marketpilot:test:dashboard/portfolio") is not None
    assert store.get_json("dashboard/portfolio")["paper_trading_only"] is True
    assert store.read_activity(limit=1)[0]["event"] == "published"
    assert "redis://" not in repr(redis.calls)


def test_shared_state_lock_prevents_overlap_and_allows_release():
    store = RenderKeyValueStore(FakeRedis(), namespace="marketpilot:test")
    now = datetime(2026, 6, 16, 14, 0, tzinfo=timezone.utc)

    first = store.acquire(run_id="run-1", owner="worker-a", now=now, ttl_seconds=60)
    second = store.acquire(run_id="run-2", owner="worker-b", now=now + timedelta(seconds=10), ttl_seconds=60)

    assert first.acquired is True
    assert second.acquired is False
    assert second.lease.run_id == "run-1"
    assert store.release(lease=first.lease) is True


def test_shared_state_rejects_secret_like_keys():
    store = InMemorySharedStateStore()

    with pytest.raises(ValueError):
        store.set_json("dashboard/token", {"value": "redacted"})
