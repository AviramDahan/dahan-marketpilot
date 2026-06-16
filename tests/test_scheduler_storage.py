from datetime import datetime, timedelta, timezone

from marketpilot.scheduler_jobs import SchedulerJobId, SchedulerJobResult
from marketpilot.scheduler_storage import JsonlSchedulerStorage, build_idempotency_key, build_run_id


def test_run_id_and_idempotency_keys_are_stable():
    scheduled_for = datetime(2026, 6, 16, 14, 5, tzinfo=timezone.utc)

    assert build_run_id(scheduled_for) == "mp-run-20260616T140500Z"
    assert build_idempotency_key("run", "same") == build_idempotency_key("run", "same")
    assert build_idempotency_key("run", "same") != build_idempotency_key("run", "different")


def test_scheduler_storage_appends_run_and_job_records(tmp_path):
    path = tmp_path / "scheduler_runs.jsonl"
    storage = JsonlSchedulerStorage(path)
    started = datetime(2026, 6, 16, 14, 0, tzinfo=timezone.utc)
    ended = started + timedelta(seconds=1)

    storage.append_run_started(run_id="run-1", scheduled_for=started, started_at=started)
    storage.append_job_result(
        run_id="run-1",
        result=SchedulerJobResult.success(
            SchedulerJobId.MARKET_GUARD,
            started_at=started,
            ended_at=ended,
        ),
    )
    storage.append_run_finished(
        run_id="run-1",
        scheduled_for=started,
        started_at=started,
        ended_at=ended,
        status="completed",
    )

    records = storage.read_records()

    assert [record["record_type"] for record in records] == ["run_started", "job_result", "run_finished"]
    assert records[1]["payload"]["job_id"] == "market_guard"
    assert storage.has_idempotency_key(records[0]["idempotency_key"]) is True


def test_missed_cycle_records_no_order_creation(tmp_path):
    path = tmp_path / "scheduler_runs.jsonl"
    storage = JsonlSchedulerStorage(path)
    scheduled = datetime(2026, 6, 16, 14, 0, tzinfo=timezone.utc)
    observed = scheduled + timedelta(minutes=30)

    storage.append_missed_cycle(run_id="run-stale", scheduled_for=scheduled, observed_at=observed, reason="stale")

    record = storage.read_records()[0]

    assert record["record_type"] == "missed_cycle"
    assert record["payload"]["order_creation_allowed"] is False

