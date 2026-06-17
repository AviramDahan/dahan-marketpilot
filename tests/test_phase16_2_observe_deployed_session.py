import json
from datetime import datetime, timezone
from unittest.mock import patch

from marketpilot.scheduler_health import SchedulerHeartbeatRecord, append_scheduler_heartbeat
from scripts import phase16_2_observe_deployed_session


def test_observer_blocks_when_required_shared_state_is_missing(tmp_path, capsys):
    heartbeat_path = tmp_path / "heartbeat.jsonl"
    append_scheduler_heartbeat(
        heartbeat_path,
        SchedulerHeartbeatRecord(
            run_id="run-1",
            timestamp=datetime(2026, 6, 17, 18, 0, tzinfo=timezone.utc),
            status="success",
        ),
    )

    with patch(
        "scripts.phase16_2_observe_deployed_session._check_dashboard_url",
        return_value={"status": "passed", "http_status": 200},
    ):
        result = phase16_2_observe_deployed_session.main(
            [
                "--heartbeat-path",
                str(heartbeat_path),
                "--require-shared-state",
            ]
        )

    output = json.loads(capsys.readouterr().out)
    assert result == 2
    assert output["status"] == "blocked_external_not_verified"
    assert output["checks"]["shared_state"]["status"] == "not_run"
    assert output["paper_trading_only"] is True


def test_observer_passes_when_required_checks_pass(tmp_path, capsys):
    heartbeat_path = tmp_path / "heartbeat.jsonl"
    append_scheduler_heartbeat(
        heartbeat_path,
        SchedulerHeartbeatRecord(
            run_id="run-1",
            timestamp=datetime.now(timezone.utc),
            status="success",
        ),
    )

    class FakeSnapshot:
        key = "dashboard:latest"
        payload = {
            "source": "quantconnect",
            "authority": "authoritative",
            "source_timestamp": "2026-06-17T18:00:00+00:00",
            "freshness_level": "fresh",
            "paper_trading_only": True,
        }

    with (
        patch(
            "scripts.phase16_2_observe_deployed_session._check_dashboard_url",
            return_value={"status": "passed", "http_status": 200},
        ),
        patch(
            "scripts.phase16_2_observe_deployed_session.load_dashboard_payload_from_env",
            return_value=FakeSnapshot(),
        ),
    ):
        result = phase16_2_observe_deployed_session.main(
            [
                "--heartbeat-path",
                str(heartbeat_path),
                "--require-shared-state",
                "--require-heartbeat",
            ]
        )

    output = json.loads(capsys.readouterr().out)
    assert result == 0
    assert output["status"] == "passed"
    assert output["checks"]["heartbeat"]["status"] == "passed"
    assert output["checks"]["shared_state"]["paper_trading_only"] is True


def test_observer_accepts_sanitized_remote_heartbeat(tmp_path, capsys):
    class FakeSnapshot:
        key = "dashboard:latest"
        payload = {
            "source": "quantconnect",
            "authority": "authoritative",
            "source_timestamp": "2026-06-17T18:00:00+00:00",
            "freshness_level": "fresh",
            "paper_trading_only": True,
        }

    with (
        patch(
            "scripts.phase16_2_observe_deployed_session._check_dashboard_url",
            return_value={"status": "passed", "http_status": 200},
        ),
        patch(
            "scripts.phase16_2_observe_deployed_session.load_dashboard_payload_from_env",
            return_value=FakeSnapshot(),
        ),
        patch(
            "scripts.phase16_2_observe_deployed_session._read_remote_heartbeat",
            return_value={
                "status": "ok",
                "latest_heartbeat_at": "2026-06-17T18:00:00+00:00",
                "age_seconds": 45,
                "worker_state": "attempted",
                "paper_trading_only": True,
                "monitor_only": True,
                "controls_scheduler": False,
                "controls_orders": False,
                "controls_recovery": False,
            },
        ),
    ):
        result = phase16_2_observe_deployed_session.main(
            [
                "--heartbeat-url",
                "https://example.test/heartbeat",
            ]
        )

    output = json.loads(capsys.readouterr().out)
    assert result == 0
    assert output["status"] == "passed"
    assert output["checks"]["heartbeat"]["status"] == "passed"
    assert output["checks"]["heartbeat"]["controls_scheduler"] is False
    assert output["checks"]["heartbeat"]["controls_orders"] is False


def test_observer_accepts_sanitized_remote_shared_state(tmp_path, capsys):
    heartbeat_path = tmp_path / "heartbeat.jsonl"
    append_scheduler_heartbeat(
        heartbeat_path,
        SchedulerHeartbeatRecord(
            run_id="run-1",
            timestamp=datetime.now(timezone.utc),
            status="success",
        ),
    )

    with (
        patch(
            "scripts.phase16_2_observe_deployed_session._check_dashboard_url",
            return_value={"status": "passed", "http_status": 200},
        ),
        patch(
            "scripts.phase16_2_observe_deployed_session._read_remote_shared_state",
            return_value={
                "status": "ok",
                "source": "quantconnect",
                "authority": "authoritative",
                "source_timestamp": "2026-06-17T18:55:00+00:00",
                "age_seconds": 60,
                "freshness_level": "fresh",
                "read_only_dashboard": True,
                "paper_trading_only": True,
                "monitor_only": True,
                "controls_scheduler": False,
                "controls_orders": False,
                "controls_recovery": False,
            },
        ),
    ):
        result = phase16_2_observe_deployed_session.main(
            [
                "--heartbeat-path",
                str(heartbeat_path),
                "--shared-state-url",
                "https://example.test/dashboard-state",
            ]
        )

    output = json.loads(capsys.readouterr().out)
    assert result == 0
    assert output["status"] == "passed"
    assert output["checks"]["shared_state"]["status"] == "passed"
    assert output["checks"]["shared_state"]["read_only_dashboard"] is True


def test_remote_shared_state_payload_is_sanitized():
    payload = phase16_2_observe_deployed_session._sanitize_remote_shared_state(
        {
            "status": "ok",
            "source": "quantconnect",
            "authority": "authoritative",
            "source_timestamp": "2026-06-17T18:55:00+00:00",
            "age_seconds": 60,
            "freshness_level": "fresh",
            "read_only_dashboard": True,
            "paper_trading_only": True,
            "monitor_only": True,
            "controls_scheduler": False,
            "controls_orders": False,
            "controls_recovery": False,
            "redis_url": "redis://should-not-appear",
            "token": "should-not-appear",
        }
    )

    assert phase16_2_observe_deployed_session._remote_shared_state_ok(payload) is True
    assert "redis_url" not in payload
    assert "token" not in payload


def test_observer_fails_when_remote_heartbeat_is_not_monitor_only(tmp_path, capsys):
    class FakeSnapshot:
        key = "dashboard:latest"
        payload = {
            "source": "quantconnect",
            "authority": "authoritative",
            "source_timestamp": "2026-06-17T18:00:00+00:00",
            "freshness_level": "fresh",
            "paper_trading_only": True,
        }

    with (
        patch(
            "scripts.phase16_2_observe_deployed_session._check_dashboard_url",
            return_value={"status": "passed", "http_status": 200},
        ),
        patch(
            "scripts.phase16_2_observe_deployed_session.load_dashboard_payload_from_env",
            return_value=FakeSnapshot(),
        ),
        patch(
            "scripts.phase16_2_observe_deployed_session._read_remote_heartbeat",
            return_value={
                "status": "ok",
                "paper_trading_only": True,
                "monitor_only": False,
                "controls_scheduler": False,
                "controls_orders": False,
                "controls_recovery": False,
            },
        ),
    ):
        result = phase16_2_observe_deployed_session.main(
            [
                "--heartbeat-url",
                "https://example.test/heartbeat",
            ]
        )

    output = json.loads(capsys.readouterr().out)
    assert result == 2
    assert output["status"] == "blocked_external_not_verified"
    assert output["checks"]["heartbeat"]["status"] == "ok"
