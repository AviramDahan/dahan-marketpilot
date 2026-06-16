from datetime import datetime, timedelta, timezone

from marketpilot.scheduler_jobs import (
    SchedulerJobId,
    SchedulerJobResult,
    SchedulerJobStatus,
    SchedulerSkipReason,
    run_dependency_aware_jobs,
)


def test_dependency_failure_skips_downstream_job():
    now = datetime(2026, 6, 16, 14, 0, tzinfo=timezone.utc)

    def clock():
        return now

    results = run_dependency_aware_jobs(
        job_order=(SchedulerJobId.MARKET_GUARD, SchedulerJobId.QC_SYNC),
        job_factories={
            SchedulerJobId.MARKET_GUARD: lambda: SchedulerJobResult.failed(
                SchedulerJobId.MARKET_GUARD,
                started_at=now,
                ended_at=now + timedelta(seconds=1),
                error="market guard failed",
            ),
            SchedulerJobId.QC_SYNC: lambda: SchedulerJobResult.success(
                SchedulerJobId.QC_SYNC,
                started_at=now,
                ended_at=now,
            ),
        },
        clock=clock,
    )

    assert results[0].status is SchedulerJobStatus.FAILED
    assert results[1].status is SchedulerJobStatus.SKIPPED
    assert results[1].skipped_reason is SchedulerSkipReason.DEPENDENCY_FAILED
    assert results[1].details["dependency"] == "market_guard"


def test_job_result_serializes_enum_values():
    started = datetime(2026, 6, 16, 14, 0, tzinfo=timezone.utc)
    ended = started + timedelta(seconds=2)

    result = SchedulerJobResult.skipped(
        SchedulerJobId.PAPER_DELIVERY_GATE,
        started_at=started,
        ended_at=ended,
        reason=SchedulerSkipReason.NO_ORDER_INTENT,
    )

    data = result.to_json_dict()

    assert data["job_id"] == "paper_delivery_gate"
    assert data["status"] == "skipped"
    assert data["skipped_reason"] == "no_order_intent"
    assert data["duration_seconds"] == 2

