from datetime import datetime, timedelta, timezone

from marketpilot.scheduler_lock import FileLockStore


def test_file_lock_acquire_blocks_overlap_and_releases(tmp_path):
    store = FileLockStore(tmp_path / "scheduler.lock.json")
    now = datetime(2026, 6, 16, 14, 0, tzinfo=timezone.utc)

    first = store.acquire(run_id="run-1", owner="worker-a", now=now, ttl_seconds=60)
    second = store.acquire(run_id="run-2", owner="worker-b", now=now + timedelta(seconds=10), ttl_seconds=60)

    assert first.acquired is True
    assert first.lease is not None
    assert second.acquired is False
    assert second.reason == "lock_already_held"
    assert second.lease.run_id == "run-1"

    assert store.release(lease=first.lease) is True
    assert store.inspect() is None


def test_expired_lock_can_be_reacquired(tmp_path):
    store = FileLockStore(tmp_path / "scheduler.lock.json")
    now = datetime(2026, 6, 16, 14, 0, tzinfo=timezone.utc)

    first = store.acquire(run_id="run-1", owner="worker-a", now=now, ttl_seconds=60)
    second = store.acquire(run_id="run-2", owner="worker-b", now=now + timedelta(seconds=61), ttl_seconds=60)

    assert first.acquired is True
    assert second.acquired is True
    assert second.lease.run_id == "run-2"


def test_lock_renew_extends_same_owner_lease(tmp_path):
    store = FileLockStore(tmp_path / "scheduler.lock.json")
    now = datetime(2026, 6, 16, 14, 0, tzinfo=timezone.utc)
    acquired = store.acquire(run_id="run-1", owner="worker-a", now=now, ttl_seconds=60)

    assert store.renew(lease=acquired.lease, now=now + timedelta(seconds=30), ttl_seconds=120) is True

    renewed = store.inspect()
    assert renewed.expires_at == now + timedelta(seconds=150)

