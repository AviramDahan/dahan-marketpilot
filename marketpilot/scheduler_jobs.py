from __future__ import annotations

"""Dependency-aware scheduler job contracts."""


from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Mapping


class SchedulerJobId(str, Enum):
    MARKET_GUARD = "market_guard"
    QC_SYNC = "quantconnect_sync"
    RUNTIME_EVALUATION = "runtime_evaluation"
    PAPER_DELIVERY_GATE = "paper_delivery_gate"
    ORDER_AUTHORITY_POLL = "order_authority_poll"
    DASHBOARD_EXPORT = "dashboard_export"
    NOTIFICATION_EMISSION = "notification_emission"
    HEARTBEAT = "heartbeat"


class SchedulerJobStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class SchedulerSkipReason(str, Enum):
    DEPENDENCY_FAILED = "dependency_failed"
    DEPENDENCY_SKIPPED = "dependency_skipped"
    MARKET_CLOSED = "market_closed"
    RUNTIME_INPUT_MISSING = "runtime_input_missing"
    NO_ORDER_INTENT = "no_order_intent"
    DELIVERY_NOT_CONFIGURED = "delivery_not_configured"
    EXPORT_NOT_CONFIGURED = "export_not_configured"
    NOTIFICATION_SINK_NOT_CONFIGURED = "notification_sink_not_configured"


@dataclass(frozen=True)
class SchedulerJobResult:
    job_id: SchedulerJobId
    status: SchedulerJobStatus
    started_at: datetime
    ended_at: datetime
    details: Mapping[str, object] = field(default_factory=dict)
    skipped_reason: SchedulerSkipReason | str | None = None
    error: str | None = None

    @classmethod
    def success(
        cls,
        job_id: SchedulerJobId,
        *,
        started_at: datetime,
        ended_at: datetime,
        details: Mapping[str, object] | None = None,
    ) -> "SchedulerJobResult":
        return cls(job_id, SchedulerJobStatus.SUCCESS, started_at, ended_at, details or {})

    @classmethod
    def skipped(
        cls,
        job_id: SchedulerJobId,
        *,
        started_at: datetime,
        ended_at: datetime,
        reason: SchedulerSkipReason | str,
        details: Mapping[str, object] | None = None,
    ) -> "SchedulerJobResult":
        return cls(job_id, SchedulerJobStatus.SKIPPED, started_at, ended_at, details or {}, reason)

    @classmethod
    def failed(
        cls,
        job_id: SchedulerJobId,
        *,
        started_at: datetime,
        ended_at: datetime,
        error: str,
        details: Mapping[str, object] | None = None,
    ) -> "SchedulerJobResult":
        return cls(job_id, SchedulerJobStatus.FAILED, started_at, ended_at, details or {}, error=error)

    @property
    def duration_seconds(self) -> float:
        return max(0.0, (self.ended_at - self.started_at).total_seconds())

    def to_json_dict(self) -> dict[str, object]:
        reason = self.skipped_reason.value if isinstance(self.skipped_reason, SchedulerSkipReason) else self.skipped_reason
        return {
            "job_id": self.job_id.value,
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat(),
            "duration_seconds": self.duration_seconds,
            "details": dict(self.details),
            "skipped_reason": reason,
            "error": self.error,
        }


JobFactory = Callable[[], SchedulerJobResult]


DEFAULT_JOB_DEPENDENCIES: dict[SchedulerJobId, tuple[SchedulerJobId, ...]] = {
    SchedulerJobId.MARKET_GUARD: (),
    SchedulerJobId.QC_SYNC: (SchedulerJobId.MARKET_GUARD,),
    SchedulerJobId.RUNTIME_EVALUATION: (SchedulerJobId.QC_SYNC,),
    SchedulerJobId.PAPER_DELIVERY_GATE: (SchedulerJobId.RUNTIME_EVALUATION,),
    SchedulerJobId.ORDER_AUTHORITY_POLL: (SchedulerJobId.PAPER_DELIVERY_GATE,),
    SchedulerJobId.DASHBOARD_EXPORT: (SchedulerJobId.QC_SYNC,),
    SchedulerJobId.NOTIFICATION_EMISSION: (SchedulerJobId.RUNTIME_EVALUATION,),
    SchedulerJobId.HEARTBEAT: (),
}


def run_dependency_aware_jobs(
    *,
    job_order: tuple[SchedulerJobId, ...],
    job_factories: Mapping[SchedulerJobId, JobFactory],
    dependencies: Mapping[SchedulerJobId, tuple[SchedulerJobId, ...]] | None = None,
    clock: Callable[[], datetime] | None = None,
) -> tuple[SchedulerJobResult, ...]:
    """Run jobs in order, skipping downstream dependencies when needed."""

    resolved_dependencies = dependencies or DEFAULT_JOB_DEPENDENCIES
    now = clock or (lambda: datetime.now(timezone.utc))
    results: dict[SchedulerJobId, SchedulerJobResult] = {}

    for job_id in job_order:
        failed_dep = _first_dependency_with_status(results, resolved_dependencies.get(job_id, ()), SchedulerJobStatus.FAILED)
        skipped_dep = _first_dependency_with_status(results, resolved_dependencies.get(job_id, ()), SchedulerJobStatus.SKIPPED)
        if failed_dep is not None or skipped_dep is not None:
            started_at = now()
            reason = SchedulerSkipReason.DEPENDENCY_FAILED if failed_dep is not None else SchedulerSkipReason.DEPENDENCY_SKIPPED
            dependency = failed_dep or skipped_dep
            results[job_id] = SchedulerJobResult.skipped(
                job_id,
                started_at=started_at,
                ended_at=now(),
                reason=reason,
                details={"dependency": dependency.value if dependency else None},
            )
            continue

        factory = job_factories[job_id]
        try:
            result = factory()
        except Exception as exc:  # pragma: no cover - defensive guard exercised through public behavior
            started_at = now()
            result = SchedulerJobResult.failed(
                job_id,
                started_at=started_at,
                ended_at=now(),
                error=f"{type(exc).__name__}: {exc}",
            )
        results[job_id] = result

    return tuple(results[job_id] for job_id in job_order)


def _first_dependency_with_status(
    results: Mapping[SchedulerJobId, SchedulerJobResult],
    dependencies: tuple[SchedulerJobId, ...],
    status: SchedulerJobStatus,
) -> SchedulerJobId | None:
    for dependency in dependencies:
        result = results.get(dependency)
        if result is not None and result.status is status:
            return dependency
    return None


__all__ = [
    "DEFAULT_JOB_DEPENDENCIES",
    "JobFactory",
    "SchedulerJobId",
    "SchedulerJobResult",
    "SchedulerJobStatus",
    "SchedulerSkipReason",
    "run_dependency_aware_jobs",
]
