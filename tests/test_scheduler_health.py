from datetime import datetime, timedelta, timezone

from marketpilot.scheduler_health import (
    SchedulerHealthStatus,
    SchedulerHeartbeatRecord,
    append_scheduler_heartbeat,
    evaluate_scheduler_heartbeat,
    event_for_scheduler_health,
    read_latest_heartbeat,
)


def test_heartbeat_missing_is_monitor_failure(tmp_path):
    check = evaluate_scheduler_heartbeat(
        tmp_path / "missing.jsonl",
        now=datetime(2026, 6, 16, 14, 0, tzinfo=timezone.utc),
    )

    assert check.status is SchedulerHealthStatus.MISSING
    assert check.reason == "heartbeat_missing"


def test_heartbeat_ok_and_stale_threshold(tmp_path):
    path = tmp_path / "scheduler_heartbeat.jsonl"
    heartbeat_at = datetime(2026, 6, 16, 14, 0, tzinfo=timezone.utc)
    append_scheduler_heartbeat(
        path,
        SchedulerHeartbeatRecord(run_id="run-1", timestamp=heartbeat_at, status="completed"),
    )

    latest = read_latest_heartbeat(path)
    ok = evaluate_scheduler_heartbeat(path, now=heartbeat_at + timedelta(minutes=10), max_age_seconds=900)
    stale = evaluate_scheduler_heartbeat(path, now=heartbeat_at + timedelta(minutes=20), max_age_seconds=900)

    assert latest["run_id"] == "run-1"
    assert ok.status is SchedulerHealthStatus.OK
    assert stale.status is SchedulerHealthStatus.STALE
    assert stale.reason == "heartbeat_stale"


def test_scheduler_health_event_is_not_safety_control(tmp_path):
    check = evaluate_scheduler_heartbeat(
        tmp_path / "missing.jsonl",
        now=datetime(2026, 6, 16, 14, 0, tzinfo=timezone.utc),
    )

    event = event_for_scheduler_health(check, correlation_id="heartbeat-check")

    assert event.event_type == "system"
    assert event.severity == "warning"
    assert event.payload["controls_safety_logic"] is False
    assert event.payload["delivery_required_for_safety"] is False

