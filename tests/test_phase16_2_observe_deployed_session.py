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

