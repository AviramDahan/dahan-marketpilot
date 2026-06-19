import json
from datetime import datetime, timezone

from marketpilot.scheduler_config import SchedulerConfig
from marketpilot.scheduler_health import read_latest_heartbeat
from marketpilot.scheduler_jobs import SchedulerJobId, SchedulerJobStatus
from marketpilot.simulation_notifications import simulation_candidate_event
from marketpilot.simulation_runner import SimulationRunnerDependencies, run_simulation_cycle


class FakeDashboardSink:
    def __init__(self) -> None:
        self.payloads: list[str] = []

    def publish(self, payload_json: str) -> None:
        self.payloads.append(payload_json)


class FakeNotificationSink:
    def __init__(self) -> None:
        self.events: list[object] = []

    def emit(self, event: object) -> bool:
        self.events.append(event)
        return True


def _config(tmp_path) -> SchedulerConfig:
    return SchedulerConfig(
        project_id=123,
        deploy_id="L-paper",
        data_dir=tmp_path,
        sync_jsonl_path=tmp_path / "portfolio_sync.jsonl",
        signal_ledger_path=tmp_path / "paper_signal_ledger.jsonl",
        audit_journal_path=tmp_path / "paper_order_audit.jsonl",
        scheduler_ledger_path=tmp_path / "scheduler_runs.jsonl",
        heartbeat_path=tmp_path / "scheduler_heartbeat.jsonl",
        lock_path=tmp_path / "scheduler.lock.json",
    )


def test_simulation_cycle_runs_on_scheduler_boundary_without_qc(tmp_path):
    dashboard = FakeDashboardSink()
    notifications = FakeNotificationSink()
    now = datetime(2026, 6, 19, 14, 30, tzinfo=timezone.utc)

    def scan(correlation_id: str, _now: datetime):
        return {
            "product_mode": "simulation_only",
            "paper_trading_only": True,
            "real_orders": False,
            "portfolio": {"cash": "10000", "equity": "10000"},
            "candidates": [{"symbol": "MSFT"}],
            "rejected_candidates": [],
            "notification_events": [
                simulation_candidate_event(correlation_id=correlation_id, candidate={"symbol": "MSFT"})
            ],
        }

    result = run_simulation_cycle(
        _config(tmp_path),
        dependencies=SimulationRunnerDependencies(
            scan_func=scan,
            dashboard_sink=dashboard,
            notification_sink=notifications,
        ),
        now=now,
    )

    jobs = {job.job_id: job for job in result.job_results}
    assert result.status == "completed"
    assert jobs[SchedulerJobId.RUNTIME_EVALUATION].status is SchedulerJobStatus.SUCCESS
    assert jobs[SchedulerJobId.DASHBOARD_EXPORT].details["dashboard_published"] is True
    assert jobs[SchedulerJobId.NOTIFICATION_EMISSION].details["emitted"] == 1
    assert json.loads(dashboard.payloads[0])["real_orders"] is False
    assert notifications.events[0].payload["simulation_only"] is True
    assert read_latest_heartbeat(tmp_path / "scheduler_heartbeat.jsonl")["dependency_health"]["product_mode"] == "simulation_only"


def test_simulation_cycle_prevents_overlap(tmp_path):
    from marketpilot.scheduler_lock import FileLockStore

    config = _config(tmp_path)
    now = datetime(2026, 6, 19, 14, 30, tzinfo=timezone.utc)
    lock = FileLockStore(config.lock_path)
    lock.acquire(run_id="existing", owner="worker-a", now=now, ttl_seconds=600)

    result = run_simulation_cycle(
        config,
        dependencies=SimulationRunnerDependencies(scan_func=lambda *_args: {}),
        now=now,
        owner="worker-b",
    )

    assert result.status == "skipped_overlap"
    assert result.job_results[0].status is SchedulerJobStatus.SKIPPED
