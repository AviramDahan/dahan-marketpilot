from __future__ import annotations

"""Scheduler-bound runner for the simulation-only scanner MVP."""

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Mapping, Protocol

from marketpilot.constants import PAPER_TRADING_ONLY
from marketpilot.product_modes import assert_simulation_only_safety
from marketpilot.scheduler_config import SchedulerConfig
from marketpilot.scheduler_health import SchedulerHeartbeatRecord, append_scheduler_heartbeat
from marketpilot.scheduler_jobs import SchedulerJobId, SchedulerJobResult, SchedulerJobStatus, run_dependency_aware_jobs
from marketpilot.scheduler_lock import FileLockStore, SchedulerLockLease
from marketpilot.scheduler_storage import JsonlSchedulerStorage, build_run_id


class SimulationDashboardSink(Protocol):
    def publish(self, payload_json: str) -> object:
        ...


class SimulationNotificationSink(Protocol):
    def emit(self, event: object) -> bool:
        ...


class SimulationLockStore(Protocol):
    def acquire(self, *, run_id: str, owner: str, now: datetime, ttl_seconds: int) -> object:
        ...

    def release(self, *, lease: SchedulerLockLease) -> bool:
        ...


SimulationScanCallable = Callable[[str, datetime], Mapping[str, object]]


@dataclass(frozen=True)
class SimulationRunnerDependencies:
    scan_func: SimulationScanCallable
    dashboard_sink: SimulationDashboardSink | None = None
    notification_sink: SimulationNotificationSink | None = None
    lock_store: SimulationLockStore | None = None


@dataclass(frozen=True)
class SimulationRuntimeResult:
    run_id: str
    correlation_id: str
    status: str
    started_at: datetime
    ended_at: datetime
    job_results: tuple[SchedulerJobResult, ...]
    paper_trading_only: bool = True
    product_mode: str = "simulation_only"

    def to_json_dict(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "correlation_id": self.correlation_id,
            "status": self.status,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat(),
            "paper_trading_only": self.paper_trading_only,
            "product_mode": self.product_mode,
            "job_results": [result.to_json_dict() for result in self.job_results],
        }


def run_simulation_cycle(
    config: SchedulerConfig,
    *,
    dependencies: SimulationRunnerDependencies,
    now: datetime | None = None,
    owner: str = "simulation-worker",
) -> SimulationRuntimeResult:
    """Run one scheduler-bound simulation-only scan cycle."""

    assert_simulation_only_safety()
    if PAPER_TRADING_ONLY is not True:
        raise RuntimeError("PAPER_TRADING_ONLY must remain true for simulation runner.")

    started_at = _aware_utc(now or datetime.now(timezone.utc), "now")
    run_id = build_run_id(started_at)
    context: dict[str, object] = {"scan_payload": None}
    storage = JsonlSchedulerStorage(config.scheduler_ledger_path)
    lock_store = dependencies.lock_store or FileLockStore(config.lock_path)
    acquire = lock_store.acquire(run_id=run_id, owner=owner, now=started_at, ttl_seconds=config.lock_ttl_seconds)
    if not acquire.acquired or acquire.lease is None:
        ended_at = datetime.now(timezone.utc)
        return SimulationRuntimeResult(
            run_id=run_id,
            correlation_id=run_id,
            status="skipped_overlap",
            started_at=started_at,
            ended_at=ended_at,
            job_results=(
                SchedulerJobResult.skipped(
                    SchedulerJobId.MARKET_GUARD,
                    started_at=started_at,
                    ended_at=ended_at,
                    reason="overlapping_run_prevented",
                ),
            ),
        )

    storage.append_run_started(run_id=run_id, scheduled_for=started_at, started_at=started_at)
    try:
        jobs = run_dependency_aware_jobs(
            job_order=(
                SchedulerJobId.RUNTIME_EVALUATION,
                SchedulerJobId.DASHBOARD_EXPORT,
                SchedulerJobId.NOTIFICATION_EMISSION,
                SchedulerJobId.HEARTBEAT,
            ),
            dependencies={
                SchedulerJobId.RUNTIME_EVALUATION: (),
                SchedulerJobId.DASHBOARD_EXPORT: (SchedulerJobId.RUNTIME_EVALUATION,),
                SchedulerJobId.NOTIFICATION_EMISSION: (SchedulerJobId.RUNTIME_EVALUATION,),
                SchedulerJobId.HEARTBEAT: (),
            },
            job_factories={
                SchedulerJobId.RUNTIME_EVALUATION: lambda: _scan_job(dependencies, run_id, started_at, context),
                SchedulerJobId.DASHBOARD_EXPORT: lambda: _dashboard_job(dependencies, started_at, context),
                SchedulerJobId.NOTIFICATION_EMISSION: lambda: _notification_job(dependencies, started_at, context),
                SchedulerJobId.HEARTBEAT: lambda: _heartbeat_job(config, run_id, started_at),
            },
        )
        ended_at = datetime.now(timezone.utc)
        status = "failed" if any(job.status is SchedulerJobStatus.FAILED for job in jobs) else "completed"
        for job in jobs:
            storage.append_job_result(run_id=run_id, result=job)
        storage.append_run_finished(
            run_id=run_id,
            scheduled_for=started_at,
            started_at=started_at,
            ended_at=ended_at,
            status=status,
            payload={"product_mode": "simulation_only"},
        )
        return SimulationRuntimeResult(run_id, run_id, status, started_at, ended_at, jobs)
    finally:
        lock_store.release(lease=acquire.lease)


def _scan_job(
    dependencies: SimulationRunnerDependencies,
    correlation_id: str,
    now: datetime,
    context: dict[str, object],
) -> SchedulerJobResult:
    payload = dict(dependencies.scan_func(correlation_id, now))
    payload.setdefault("product_mode", "simulation_only")
    payload.setdefault("paper_trading_only", True)
    payload.setdefault("real_orders", False)
    context["scan_payload"] = payload
    return SchedulerJobResult.success(
        SchedulerJobId.RUNTIME_EVALUATION,
        started_at=now,
        ended_at=datetime.now(timezone.utc),
        details={
            "product_mode": payload.get("product_mode"),
            "candidate_count": _count(payload.get("candidates")),
            "rejected_count": _count(payload.get("rejected_candidates")),
            "real_orders": payload.get("real_orders") is True,
        },
    )


def _dashboard_job(
    dependencies: SimulationRunnerDependencies,
    now: datetime,
    context: Mapping[str, object],
) -> SchedulerJobResult:
    payload = context.get("scan_payload")
    if dependencies.dashboard_sink is not None and isinstance(payload, Mapping):
        import json

        dependencies.dashboard_sink.publish(json.dumps(payload, default=str))
    return SchedulerJobResult.success(
        SchedulerJobId.DASHBOARD_EXPORT,
        started_at=now,
        ended_at=datetime.now(timezone.utc),
        details={"dashboard_published": dependencies.dashboard_sink is not None},
    )


def _notification_job(
    dependencies: SimulationRunnerDependencies,
    now: datetime,
    context: Mapping[str, object],
) -> SchedulerJobResult:
    payload = context.get("scan_payload")
    events = []
    if isinstance(payload, Mapping):
        raw_events = payload.get("notification_events")
        if isinstance(raw_events, list):
            events = raw_events
    emitted = 0
    if dependencies.notification_sink is not None:
        for event in events:
            if dependencies.notification_sink.emit(event):
                emitted += 1
    return SchedulerJobResult.success(
        SchedulerJobId.NOTIFICATION_EMISSION,
        started_at=now,
        ended_at=datetime.now(timezone.utc),
        details={"notification_count": len(events), "emitted": emitted},
    )


def _heartbeat_job(config: SchedulerConfig, run_id: str, now: datetime) -> SchedulerJobResult:
    record = SchedulerHeartbeatRecord(
        run_id=run_id,
        timestamp=datetime.now(timezone.utc),
        status="completed",
        paper_trading_only=True,
        dependency_health={"product_mode": "simulation_only"},
    )
    append_scheduler_heartbeat(Path(config.heartbeat_path), record)
    return SchedulerJobResult.success(
        SchedulerJobId.HEARTBEAT,
        started_at=now,
        ended_at=datetime.now(timezone.utc),
        details={"product_mode": "simulation_only"},
    )


def _count(value: object) -> int:
    return len(value) if isinstance(value, list) else 0


def _aware_utc(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(timezone.utc)


__all__ = [
    "SimulationRunnerDependencies",
    "SimulationRuntimeResult",
    "run_simulation_cycle",
]
