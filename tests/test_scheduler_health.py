from datetime import datetime, timedelta, timezone

from marketpilot.scheduler_health import (
    SchedulerHealthStatus,
    SchedulerHeartbeatRecord,
    append_scheduler_heartbeat,
    evaluate_scheduler_heartbeat,
    event_for_scheduler_health,
    read_latest_heartbeat,
)
from marketpilot.heartbeat_health_server import build_dashboard_state_health, build_heartbeat_health
from scripts.check_scheduler_heartbeat import _annotate_monitor_window, _remote_heartbeat_ok, _sanitize_remote_payload


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


def test_remote_heartbeat_payload_is_sanitized_and_monitor_only():
    payload = _sanitize_remote_payload(
        {
            "status": "ok",
            "checked_at": "2026-06-17T18:56:00+00:00",
            "latest_heartbeat_at": "2026-06-17T18:55:00+00:00",
            "age_seconds": 60,
            "paper_trading_only": True,
            "monitor_only": True,
            "controls_scheduler": False,
            "controls_orders": False,
            "controls_recovery": False,
            "redis_url": "redis://should-not-appear",
            "token": "should-not-appear",
        }
    )

    assert _remote_heartbeat_ok(payload) is True
    assert "redis_url" not in payload
    assert "token" not in payload


def test_remote_stale_heartbeat_is_allowed_after_market_close():
    payload = _sanitize_remote_payload(
        {
            "status": "stale",
            "reason": "heartbeat_stale",
            "latest_heartbeat_at": "2026-06-17T20:55:00+00:00",
            "age_seconds": 3684,
            "paper_trading_only": True,
            "monitor_only": True,
            "controls_scheduler": False,
            "controls_orders": False,
            "controls_recovery": False,
        }
    )
    now = datetime(2026, 6, 17, 22, 6, tzinfo=timezone.utc)

    annotated = _annotate_monitor_window(payload, now=now)

    assert annotated["market_window_status"] == "closed"
    assert annotated["heartbeat_required_now"] is False
    assert _remote_heartbeat_ok(annotated, now=now) is True


def test_remote_stale_heartbeat_fails_during_market_hours():
    payload = _sanitize_remote_payload(
        {
            "status": "stale",
            "reason": "heartbeat_stale",
            "latest_heartbeat_at": "2026-06-17T14:00:00+00:00",
            "age_seconds": 3600,
            "paper_trading_only": True,
            "monitor_only": True,
            "controls_scheduler": False,
            "controls_orders": False,
            "controls_recovery": False,
        }
    )
    now = datetime(2026, 6, 17, 15, 0, tzinfo=timezone.utc)

    annotated = _annotate_monitor_window(payload, now=now)

    assert annotated["market_window_status"] == "open"
    assert annotated["heartbeat_required_now"] is True
    assert _remote_heartbeat_ok(annotated, now=now) is False


def test_deployed_heartbeat_health_reports_shared_state_heartbeat(monkeypatch):
    class FakeSnapshot:
        payload = {
            "system_health": {
                "timestamp": "2026-06-17T18:55:00+00:00",
                "status": "attempted",
                "paper_trading_only": True,
            }
        }

    monkeypatch.setattr("marketpilot.heartbeat_health_server.load_dashboard_payload_from_env", lambda: FakeSnapshot())

    health = build_heartbeat_health(
        now=datetime(2026, 6, 17, 18, 56, tzinfo=timezone.utc),
        max_age_seconds=900,
    )

    assert health["status"] == "ok"
    assert health["age_seconds"] == 60
    assert health["worker_state"] == "attempted"
    assert health["paper_trading_only"] is True
    assert health["controls_scheduler"] is False
    assert health["controls_orders"] is False


def test_deployed_dashboard_state_health_is_sanitized(monkeypatch):
    class FakeSnapshot:
        payload = {
            "source": "quantconnect",
            "authority": "authoritative",
            "source_timestamp": "2026-06-17T18:55:00+00:00",
            "freshness_level": "fresh",
            "read_only_dashboard": True,
            "paper_trading_only": True,
            "redis_url": "redis://should-not-appear",
            "token": "should-not-appear",
        }

    monkeypatch.setattr("marketpilot.heartbeat_health_server.load_dashboard_payload_from_env", lambda: FakeSnapshot())

    health = build_dashboard_state_health(
        now=datetime(2026, 6, 17, 18, 56, tzinfo=timezone.utc),
        max_age_seconds=900,
    )

    assert health["status"] == "ok"
    assert health["source"] == "quantconnect"
    assert health["authority"] == "authoritative"
    assert health["source_timestamp"] == "2026-06-17T18:55:00+00:00"
    assert health["age_seconds"] == 60
    assert health["read_only_dashboard"] is True
    assert health["paper_trading_only"] is True
    assert health["controls_scheduler"] is False
    assert health["controls_orders"] is False
    assert "redis_url" not in health
    assert "token" not in health


def test_deployed_dashboard_state_health_reports_stale(monkeypatch):
    class FakeSnapshot:
        payload = {
            "source": "quantconnect",
            "authority": "authoritative",
            "source_timestamp": "2026-06-17T18:00:00+00:00",
            "freshness_level": "stale",
            "read_only_dashboard": True,
            "paper_trading_only": True,
        }

    monkeypatch.setattr("marketpilot.heartbeat_health_server.load_dashboard_payload_from_env", lambda: FakeSnapshot())

    health = build_dashboard_state_health(
        now=datetime(2026, 6, 17, 18, 30, tzinfo=timezone.utc),
        max_age_seconds=900,
    )

    assert health["status"] == "stale"
    assert health["reason"] == "dashboard_state_stale"
    assert health["age_seconds"] == 1800
