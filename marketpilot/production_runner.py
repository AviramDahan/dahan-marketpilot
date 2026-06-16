"""Production scheduler runner for one autonomous Paper Trading cycle."""

from __future__ import annotations

import argparse
import json
import logging
import os
import socket
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Iterable, Mapping, Protocol

from marketpilot.constants import PAPER_TRADING_ONLY
from marketpilot.dashboard_export import build_dashboard_export_payload
from marketpilot.notification_events import NotificationDomainEvent
from marketpilot.paper_order_flow import poll_quantconnect_order_updates, submit_signal_command
from marketpilot.qc_api import QCApiClient
from marketpilot.runtime_orchestrator import (
    RuntimeOrchestrationInput,
    RuntimeOrchestrationResult,
    RuntimeOrchestrationStatus,
    run_runtime_pipeline,
)
from marketpilot.scheduler_calendar import MarketSessionDecision, evaluate_market_session
from marketpilot.scheduler_config import SchedulerConfig, build_apscheduler_cron_kwargs, load_scheduler_config_from_env
from marketpilot.scheduler_health import SchedulerHeartbeatRecord, append_scheduler_heartbeat
from marketpilot.scheduler_jobs import (
    SchedulerJobId,
    SchedulerJobResult,
    SchedulerJobStatus,
    SchedulerSkipReason,
    run_dependency_aware_jobs,
)
from marketpilot.scheduler_lock import FileLockStore, SchedulerLockLease
from marketpilot.scheduler_storage import JsonlSchedulerStorage, build_run_id
from marketpilot.sync import SyncResult, read_last_sync_record, sync_portfolio


_logger = logging.getLogger("marketpilot.production_runner")


class DashboardExportSink(Protocol):
    def publish(self, payload_json: str) -> object:
        ...


class NotificationSink(Protocol):
    def emit(self, event: NotificationDomainEvent) -> bool:
        ...


SyncCallable = Callable[..., SyncResult]
RuntimeInputFactory = Callable[[str], RuntimeOrchestrationInput | None]
SubmitSignalCallable = Callable[..., object]
PollOrdersCallable = Callable[..., object]


@dataclass(frozen=True)
class ProductionRunnerDependencies:
    client: QCApiClient | None = None
    sync_func: SyncCallable = sync_portfolio
    runtime_input_factory: RuntimeInputFactory | None = None
    submit_signal_func: SubmitSignalCallable = submit_signal_command
    poll_orders_func: PollOrdersCallable = poll_quantconnect_order_updates
    dashboard_export_sink: DashboardExportSink | None = None
    notification_sink: NotificationSink | None = None


@dataclass(frozen=True)
class ProductionRuntimeResult:
    run_id: str
    correlation_id: str
    scheduled_for: datetime
    started_at: datetime
    ended_at: datetime
    status: str
    job_results: tuple[SchedulerJobResult, ...]
    runtime_status: str | None = None
    order_intent_count: int = 0
    delivered_signal_count: int = 0
    observed_order_count: int = 0
    notification_count: int = 0
    paper_trading_only: bool = True

    def to_json_dict(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "correlation_id": self.correlation_id,
            "scheduled_for": self.scheduled_for.astimezone(timezone.utc).isoformat(),
            "started_at": self.started_at.astimezone(timezone.utc).isoformat(),
            "ended_at": self.ended_at.astimezone(timezone.utc).isoformat(),
            "status": self.status,
            "runtime_status": self.runtime_status,
            "order_intent_count": self.order_intent_count,
            "delivered_signal_count": self.delivered_signal_count,
            "observed_order_count": self.observed_order_count,
            "notification_count": self.notification_count,
            "paper_trading_only": self.paper_trading_only,
            "job_results": [result.to_json_dict() for result in self.job_results],
        }


def run_production_cycle(
    config: SchedulerConfig,
    *,
    dependencies: ProductionRunnerDependencies | None = None,
    now: datetime | None = None,
    scheduled_for: datetime | None = None,
    owner: str | None = None,
) -> ProductionRuntimeResult:
    """Run one dependency-aware, paper-only production scheduler cycle."""

    if PAPER_TRADING_ONLY is not True:
        raise RuntimeError("PAPER_TRADING_ONLY must be True for production runner.")

    deps = dependencies or ProductionRunnerDependencies()
    started_at = _aware_utc(now or datetime.now(timezone.utc), "now")
    scheduled_at = _aware_utc(scheduled_for or started_at, "scheduled_for")
    run_id = build_run_id(scheduled_at)
    correlation_id = run_id
    storage = JsonlSchedulerStorage(config.scheduler_ledger_path)
    lock_store = FileLockStore(config.lock_path)
    lock_owner = owner or _default_owner()

    acquire = lock_store.acquire(
        run_id=run_id,
        owner=lock_owner,
        now=started_at,
        ttl_seconds=config.lock_ttl_seconds,
    )
    if not acquire.acquired or acquire.lease is None:
        ended_at = datetime.now(timezone.utc)
        result = SchedulerJobResult.skipped(
            SchedulerJobId.MARKET_GUARD,
            started_at=started_at,
            ended_at=ended_at,
            reason="overlapping_run_prevented",
            details={"lock_owner": acquire.lease.owner if acquire.lease else None, "locked_run_id": acquire.lease.run_id if acquire.lease else None},
        )
        return ProductionRuntimeResult(
            run_id=run_id,
            correlation_id=correlation_id,
            scheduled_for=scheduled_at,
            started_at=started_at,
            ended_at=ended_at,
            status="skipped_overlap",
            job_results=(result,),
        )

    context: dict[str, object] = {
        "notifications": [],
        "runtime_result": None,
        "delivered_signal_count": 0,
        "observed_order_count": 0,
        "market_decision": None,
    }
    storage.append_run_started(run_id=run_id, scheduled_for=scheduled_at, started_at=started_at)
    try:
        jobs = run_dependency_aware_jobs(
            job_order=(
                SchedulerJobId.MARKET_GUARD,
                SchedulerJobId.QC_SYNC,
                SchedulerJobId.RUNTIME_EVALUATION,
                SchedulerJobId.PAPER_DELIVERY_GATE,
                SchedulerJobId.ORDER_AUTHORITY_POLL,
                SchedulerJobId.DASHBOARD_EXPORT,
                SchedulerJobId.NOTIFICATION_EMISSION,
                SchedulerJobId.HEARTBEAT,
            ),
            job_factories={
                SchedulerJobId.MARKET_GUARD: lambda: _market_guard_job(
                    config=config,
                    now=started_at,
                    scheduled_for=scheduled_at,
                    context=context,
                ),
                SchedulerJobId.QC_SYNC: lambda: _sync_job(config=config, deps=deps),
                SchedulerJobId.RUNTIME_EVALUATION: lambda: _runtime_job(
                    run_id=run_id,
                    deps=deps,
                    context=context,
                ),
                SchedulerJobId.PAPER_DELIVERY_GATE: lambda: _paper_delivery_job(
                    config=config,
                    deps=deps,
                    context=context,
                    correlation_id=correlation_id,
                    now=started_at,
                ),
                SchedulerJobId.ORDER_AUTHORITY_POLL: lambda: _order_poll_job(
                    config=config,
                    deps=deps,
                    context=context,
                    correlation_id=correlation_id,
                    now=started_at,
                ),
                SchedulerJobId.DASHBOARD_EXPORT: lambda: _dashboard_export_job(
                    config=config,
                    deps=deps,
                    context=context,
                    source_timestamp=started_at,
                ),
                SchedulerJobId.NOTIFICATION_EMISSION: lambda: _notification_job(deps=deps, context=context),
                SchedulerJobId.HEARTBEAT: lambda: _heartbeat_job(
                    config=config,
                    run_id=run_id,
                    context=context,
                    now=datetime.now(timezone.utc),
                ),
            },
        )
        for job in jobs:
            storage.append_job_result(run_id=run_id, result=job)
        ended_at = datetime.now(timezone.utc)
        status = _run_status(jobs)
        runtime_result = context.get("runtime_result")
        runtime_status = runtime_result.status.value if isinstance(runtime_result, RuntimeOrchestrationResult) else None
        result = ProductionRuntimeResult(
            run_id=run_id,
            correlation_id=correlation_id,
            scheduled_for=scheduled_at,
            started_at=started_at,
            ended_at=ended_at,
            status=status,
            job_results=jobs,
            runtime_status=runtime_status,
            order_intent_count=_order_intent_count(runtime_result),
            delivered_signal_count=int(context["delivered_signal_count"]),
            observed_order_count=int(context["observed_order_count"]),
            notification_count=len(_notifications(context)),
        )
        storage.append_run_finished(
            run_id=run_id,
            scheduled_for=scheduled_at,
            started_at=started_at,
            ended_at=ended_at,
            status=status,
            payload=result.to_json_dict(),
        )
        return result
    finally:
        _release_lock(lock_store, acquire.lease)


def _market_guard_job(
    *,
    config: SchedulerConfig,
    now: datetime,
    scheduled_for: datetime,
    context: dict[str, object],
) -> SchedulerJobResult:
    started = datetime.now(timezone.utc)
    decision = evaluate_market_session(
        now=now,
        scheduled_for=scheduled_for,
        stale_after_seconds=config.stale_after_seconds,
    )
    context["market_decision"] = decision
    ended = datetime.now(timezone.utc)
    if not decision.eligible_for_orders:
        return SchedulerJobResult.skipped(
            SchedulerJobId.MARKET_GUARD,
            started_at=started,
            ended_at=ended,
            reason=decision.reason.value if decision.reason else SchedulerSkipReason.MARKET_CLOSED,
            details=decision.to_json_dict(),
        )
    return SchedulerJobResult.success(
        SchedulerJobId.MARKET_GUARD,
        started_at=started,
        ended_at=ended,
        details=decision.to_json_dict(),
    )


def _sync_job(*, config: SchedulerConfig, deps: ProductionRunnerDependencies) -> SchedulerJobResult:
    started = datetime.now(timezone.utc)
    result = deps.sync_func(
        project_id=config.project_id,
        deploy_id=config.deploy_id,
        jsonl_path=config.sync_jsonl_path,
        client=deps.client,
    )
    ended = datetime.now(timezone.utc)
    details = {"status": result.status, "generation": result.generation, "alert_emitted": result.alert_emitted}
    if result.status != "success":
        return SchedulerJobResult.failed(SchedulerJobId.QC_SYNC, started_at=started, ended_at=ended, error=result.error or result.status, details=details)
    return SchedulerJobResult.success(SchedulerJobId.QC_SYNC, started_at=started, ended_at=ended, details=details)


def _runtime_job(
    *,
    run_id: str,
    deps: ProductionRunnerDependencies,
    context: dict[str, object],
) -> SchedulerJobResult:
    started = datetime.now(timezone.utc)
    if deps.runtime_input_factory is None:
        return SchedulerJobResult.skipped(
            SchedulerJobId.RUNTIME_EVALUATION,
            started_at=started,
            ended_at=datetime.now(timezone.utc),
            reason=SchedulerSkipReason.RUNTIME_INPUT_MISSING,
            details={"run_id": run_id},
        )
    runtime_input = deps.runtime_input_factory(run_id)
    if runtime_input is None:
        return SchedulerJobResult.skipped(
            SchedulerJobId.RUNTIME_EVALUATION,
            started_at=started,
            ended_at=datetime.now(timezone.utc),
            reason=SchedulerSkipReason.RUNTIME_INPUT_MISSING,
            details={"run_id": run_id},
        )
    runtime_result = run_runtime_pipeline(runtime_input)
    context["runtime_result"] = runtime_result
    context["notifications"] = list(runtime_result.notification_events)
    return SchedulerJobResult.success(
        SchedulerJobId.RUNTIME_EVALUATION,
        started_at=started,
        ended_at=datetime.now(timezone.utc),
        details={
            "runtime_status": runtime_result.status.value,
            "order_intent_count": len(runtime_result.order_intents),
            "skipped_reasons": [reason.value for reason in runtime_result.skipped_reasons],
        },
    )


def _paper_delivery_job(
    *,
    config: SchedulerConfig,
    deps: ProductionRunnerDependencies,
    context: dict[str, object],
    correlation_id: str,
    now: datetime,
) -> SchedulerJobResult:
    started = datetime.now(timezone.utc)
    runtime_result = context.get("runtime_result")
    if not isinstance(runtime_result, RuntimeOrchestrationResult) or runtime_result.status is not RuntimeOrchestrationStatus.PAPER_INTENT_READY:
        return SchedulerJobResult.skipped(
            SchedulerJobId.PAPER_DELIVERY_GATE,
            started_at=started,
            ended_at=datetime.now(timezone.utc),
            reason=SchedulerSkipReason.NO_ORDER_INTENT,
            details={"runtime_status": getattr(getattr(runtime_result, "status", None), "value", None)},
        )

    delivered = 0
    statuses: list[str] = []
    for index, intent in enumerate(runtime_result.order_intents, start=1):
        signal_id = f"{correlation_id}-sig-{index}"
        response = deps.submit_signal_func(
            project_id=config.project_id,
            deploy_id=config.deploy_id,
            intent=intent,
            correlation_id=correlation_id,
            signal_id=signal_id,
            expires_at_utc=now + timedelta(minutes=10),
            sync_jsonl_path=config.sync_jsonl_path,
            ledger_path=config.signal_ledger_path,
            audit_journal_path=config.audit_journal_path,
            client=deps.client,
            now_utc=now,
        )
        status = str(getattr(response, "status", "unknown"))
        statuses.append(status)
        if bool(getattr(response, "command_delivered", False)):
            delivered += 1
    context["delivered_signal_count"] = delivered
    return SchedulerJobResult.success(
        SchedulerJobId.PAPER_DELIVERY_GATE,
        started_at=started,
        ended_at=datetime.now(timezone.utc),
        details={"delivered_signal_count": delivered, "submission_statuses": statuses},
    )


def _order_poll_job(
    *,
    config: SchedulerConfig,
    deps: ProductionRunnerDependencies,
    context: dict[str, object],
    correlation_id: str,
    now: datetime,
) -> SchedulerJobResult:
    started = datetime.now(timezone.utc)
    if int(context.get("delivered_signal_count", 0)) <= 0:
        return SchedulerJobResult.skipped(
            SchedulerJobId.ORDER_AUTHORITY_POLL,
            started_at=started,
            ended_at=datetime.now(timezone.utc),
            reason=SchedulerSkipReason.NO_ORDER_INTENT,
            details={"delivered_signal_count": 0},
        )
    result = deps.poll_orders_func(
        project_id=config.project_id,
        deploy_id=config.deploy_id,
        audit_journal_path=config.audit_journal_path,
        correlation_id=correlation_id,
        client=deps.client,
        observed_at_utc=now,
    )
    observed = int(getattr(result, "observed_count", 0))
    context["observed_order_count"] = observed
    return SchedulerJobResult.success(
        SchedulerJobId.ORDER_AUTHORITY_POLL,
        started_at=started,
        ended_at=datetime.now(timezone.utc),
        details={
            "observed_order_count": observed,
            "audit_record_count": int(getattr(result, "audit_record_count", 0)),
            "warning_count": int(getattr(result, "warning_count", 0)),
        },
    )


def _dashboard_export_job(
    *,
    config: SchedulerConfig,
    deps: ProductionRunnerDependencies,
    context: dict[str, object],
    source_timestamp: datetime,
) -> SchedulerJobResult:
    started = datetime.now(timezone.utc)
    if deps.dashboard_export_sink is None:
        return SchedulerJobResult.skipped(
            SchedulerJobId.DASHBOARD_EXPORT,
            started_at=started,
            ended_at=datetime.now(timezone.utc),
            reason=SchedulerSkipReason.EXPORT_NOT_CONFIGURED,
            details={"phase_16_1_interface_ready": True},
        )
    latest_sync = read_last_sync_record(config.sync_jsonl_path) or {}
    runtime_result = context.get("runtime_result")
    payload = build_dashboard_export_payload(
        portfolio=dict(latest_sync.get("portfolio") or {}),
        runtime_evidence=_runtime_evidence(runtime_result),
        source_timestamp=source_timestamp,
        fixture_label="scheduler-production-cycle",
    )
    deps.dashboard_export_sink.publish(payload.to_json())
    return SchedulerJobResult.success(
        SchedulerJobId.DASHBOARD_EXPORT,
        started_at=started,
        ended_at=datetime.now(timezone.utc),
        details={"published": True},
    )


def _notification_job(*, deps: ProductionRunnerDependencies, context: dict[str, object]) -> SchedulerJobResult:
    started = datetime.now(timezone.utc)
    events = _notifications(context)
    if deps.notification_sink is None:
        return SchedulerJobResult.skipped(
            SchedulerJobId.NOTIFICATION_EMISSION,
            started_at=started,
            ended_at=datetime.now(timezone.utc),
            reason=SchedulerSkipReason.NOTIFICATION_SINK_NOT_CONFIGURED,
            details={"event_count": len(events), "phase_16_1_interface_ready": True},
        )
    delivered = sum(1 for event in events if deps.notification_sink and deps.notification_sink.emit(event))
    return SchedulerJobResult.success(
        SchedulerJobId.NOTIFICATION_EMISSION,
        started_at=started,
        ended_at=datetime.now(timezone.utc),
        details={"event_count": len(events), "delivered_count": delivered},
    )


def _heartbeat_job(
    *,
    config: SchedulerConfig,
    run_id: str,
    context: dict[str, object],
    now: datetime,
) -> SchedulerJobResult:
    started = datetime.now(timezone.utc)
    append_scheduler_heartbeat(
        config.heartbeat_path,
        SchedulerHeartbeatRecord(
            run_id=run_id,
            timestamp=now,
            status="attempted",
            last_attempted_run_id=run_id,
            last_successful_run_id=run_id if int(context.get("delivered_signal_count", 0)) >= 0 else None,
            dependency_health={
                "delivered_signal_count": int(context.get("delivered_signal_count", 0)),
                "observed_order_count": int(context.get("observed_order_count", 0)),
            },
        ),
    )
    return SchedulerJobResult.success(
        SchedulerJobId.HEARTBEAT,
        started_at=started,
        ended_at=datetime.now(timezone.utc),
        details={"heartbeat_path": str(config.heartbeat_path)},
    )


def run_scheduler_forever(config: SchedulerConfig | None = None) -> None:
    """Start APScheduler inside the Render Background Worker process."""

    resolved = config or load_scheduler_config_from_env()
    try:
        from apscheduler.schedulers.blocking import BlockingScheduler
        from apscheduler.triggers.cron import CronTrigger
    except ImportError as exc:  # pragma: no cover - depends on deployed optional dependency
        raise RuntimeError("APScheduler is required for scheduler worker mode.") from exc

    scheduler = BlockingScheduler(timezone=resolved.timezone_name)
    trigger = CronTrigger(**build_apscheduler_cron_kwargs(resolved))
    scheduler.add_job(
        lambda: run_production_cycle(resolved),
        trigger=trigger,
        id="marketpilot-production-cycle",
        max_instances=1,
        coalesce=True,
        replace_existing=True,
    )
    _logger.info("Starting MarketPilot scheduler worker")
    scheduler.start()


def _run_status(jobs: Iterable[SchedulerJobResult]) -> str:
    statuses = [job.status for job in jobs]
    if any(status is SchedulerJobStatus.FAILED for status in statuses):
        return "failed"
    if any(status is SchedulerJobStatus.SUCCESS for status in statuses):
        return "completed"
    return "skipped"


def _runtime_evidence(runtime_result: object) -> dict[str, object]:
    if not isinstance(runtime_result, RuntimeOrchestrationResult):
        return {"runtime_status": "not_available"}
    return {
        "runtime_status": runtime_result.status.value,
        "order_intent_count": len(runtime_result.order_intents),
        "skipped_reasons": [reason.value for reason in runtime_result.skipped_reasons],
        "paper_trading_only": True,
    }


def _order_intent_count(runtime_result: object) -> int:
    if not isinstance(runtime_result, RuntimeOrchestrationResult):
        return 0
    return len(runtime_result.order_intents)


def _notifications(context: Mapping[str, object]) -> list[NotificationDomainEvent]:
    raw = context.get("notifications", [])
    if not isinstance(raw, list):
        return []
    return [event for event in raw if isinstance(event, NotificationDomainEvent)]


def _default_owner() -> str:
    return f"{socket.gethostname()}:{os.getpid()}"


def _release_lock(lock_store: FileLockStore, lease: SchedulerLockLease | None) -> None:
    if lease is None:
        return
    try:
        lock_store.release(lease=lease)
    except OSError:
        _logger.warning("Failed to release scheduler lock for run %s", lease.run_id)


def _aware_utc(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(timezone.utc)


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run MarketPilot production scheduler utilities.")
    parser.add_argument("command", nargs="?", choices=("once", "scheduler"), default="once")
    parser.add_argument("--dry-run", action="store_true", help="Print config and exit without touching QuantConnect.")
    args = parser.parse_args(argv)

    config = load_scheduler_config_from_env()
    if args.dry_run:
        print(json.dumps({"status": "dry_run", "config": {"project_id": config.project_id, "deploy_id": config.deploy_id}}, sort_keys=True))
        return 0
    if args.command == "scheduler":
        run_scheduler_forever(config)
        return 0
    result = run_production_cycle(config)
    print(json.dumps(result.to_json_dict(), sort_keys=True))
    return 0 if result.status != "failed" else 2


if __name__ == "__main__":
    raise SystemExit(_main())


__all__ = [
    "DashboardExportSink",
    "NotificationSink",
    "ProductionRunnerDependencies",
    "ProductionRuntimeResult",
    "run_production_cycle",
    "run_scheduler_forever",
]

