from __future__ import annotations

"""Production scheduler runner for one autonomous Paper Trading cycle."""


import argparse
import json
import logging
import os
import socket
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Callable, Iterable, Mapping, Protocol

from marketpilot.backtesting import BacktestRunStatus
from marketpilot.constants import PAPER_TRADING_ONLY
from marketpilot.dashboard_export import build_dashboard_export_payload
from marketpilot.notification_events import NotificationDomainEvent
from marketpilot.paper_modes import PaperTradingMode
from marketpilot.paper_order_flow import poll_quantconnect_order_updates, submit_signal_command
from marketpilot.qc_api import QCApiClient
from marketpilot.quantconnect_paper import (
    QuantConnectAlgorithmStatus,
    QuantConnectDeploymentStatus,
    QuantConnectHolding,
    QuantConnectPaperPerformance,
    QuantConnectPaperSnapshot,
)
from marketpilot.risk import PortfolioSnapshot
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
from marketpilot.setups.base import NumericEvidence, SetupResult, SetupStatus, SetupTiming
from marketpilot.shared_state import RenderKeyValueStore
from marketpilot.sync import SyncResult, read_last_sync_record, sync_portfolio
from marketpilot.telegram import TelegramDeliveryService, load_telegram_config
from marketpilot.timeframes import StrategyMode
from marketpilot.validation import ActivationApprovalState, evaluate_activation_gates


_logger = logging.getLogger("marketpilot.production_runner")


class DashboardExportSink(Protocol):
    def publish(self, payload_json: str) -> object:
        ...


class HeartbeatSink(Protocol):
    def publish_heartbeat(self, payload: Mapping[str, object]) -> object:
        ...


class NotificationSink(Protocol):
    def emit(self, event: NotificationDomainEvent) -> bool:
        ...


class SchedulerLockStore(Protocol):
    def acquire(self, *, run_id: str, owner: str, now: datetime, ttl_seconds: int) -> object:
        ...

    def release(self, *, lease: SchedulerLockLease) -> bool:
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
    lock_store: SchedulerLockStore | None = None


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
    lock_store = deps.lock_store or FileLockStore(config.lock_path)
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
                    deps=deps,
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
            now_utc=datetime.now(timezone.utc),
        )
        status = str(getattr(response, "status", "unknown"))
        statuses.append(status)
        if bool(getattr(response, "command_delivered", False)):
            delivered += 1
            context.setdefault("submitted_signal_links", []).append(
                {
                    "signal_id": signal_id,
                    "idempotency_key": str(getattr(response, "idempotency_key", "")),
                }
            )
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
        expected_signal_id=_first_submitted_signal_value(context, "signal_id"),
        expected_idempotency_key=_first_submitted_signal_value(context, "idempotency_key"),
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


def _first_submitted_signal_value(context: dict[str, object], key: str) -> str | None:
    links = context.get("submitted_signal_links")
    if not isinstance(links, list):
        return None
    for link in links:
        if isinstance(link, dict):
            value = str(link.get(key) or "").strip()
            if value:
                return value
    return None


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
        runtime_evidence={
            **_runtime_evidence(runtime_result),
            "sync_status": latest_sync.get("sync_status"),
            "reconciliation_clean": latest_sync.get("reconciliation_clean"),
            "generation": latest_sync.get("generation"),
        },
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
    deps: ProductionRunnerDependencies,
    run_id: str,
    context: dict[str, object],
    now: datetime,
) -> SchedulerJobResult:
    started = datetime.now(timezone.utc)
    record = SchedulerHeartbeatRecord(
        run_id=run_id,
        timestamp=now,
        status="attempted",
        last_attempted_run_id=run_id,
        last_successful_run_id=run_id if int(context.get("delivered_signal_count", 0)) >= 0 else None,
        dependency_health={
            "delivered_signal_count": int(context.get("delivered_signal_count", 0)),
            "observed_order_count": int(context.get("observed_order_count", 0)),
        },
    )
    append_scheduler_heartbeat(config.heartbeat_path, record)
    heartbeat_published = _publish_shared_heartbeat(deps.dashboard_export_sink, record)
    return SchedulerJobResult.success(
        SchedulerJobId.HEARTBEAT,
        started_at=started,
        ended_at=datetime.now(timezone.utc),
        details={"heartbeat_path": str(config.heartbeat_path), "shared_state_published": heartbeat_published},
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
        lambda: run_production_cycle(resolved, dependencies=build_production_dependencies_from_env()),
        trigger=trigger,
        id="marketpilot-production-cycle",
        max_instances=1,
        coalesce=True,
        replace_existing=True,
    )
    _logger.info("Starting MarketPilot scheduler worker")
    scheduler.start()


def build_production_dependencies_from_env(
    *,
    env: Mapping[str, str] | None = None,
) -> ProductionRunnerDependencies:
    """Build optional production integrations from environment-only secrets."""

    source = env if env is not None else os.environ
    shared_store = None
    if str(source.get("REDIS_URL") or "").strip():
        shared_store = RenderKeyValueStore.from_env(env=source)

    notification_sink = None
    try:
        telegram_config = load_telegram_config(env=source)
    except (FileNotFoundError, ValueError):
        telegram_config = None
    if telegram_config is not None and telegram_config.can_deliver:
        notification_sink = _TelegramNotificationSink(TelegramDeliveryService(telegram_config))

    runtime_input_factory = _runtime_input_factory_from_env(source)

    return ProductionRunnerDependencies(
        runtime_input_factory=runtime_input_factory,
        dashboard_export_sink=shared_store,
        notification_sink=notification_sink,
        lock_store=shared_store,
    )


def _runtime_input_factory_from_env(source: Mapping[str, str]) -> RuntimeInputFactory | None:
    kind = str(source.get("MARKETPILOT_RUNTIME_INPUT_KIND") or "").strip().lower()
    enabled = _env_flag(source.get("MARKETPILOT_OPERATOR_PAPER_PROBE_ENABLED"))
    if kind != "operator_paper_probe" or not enabled:
        return None

    data_dir = Path(str(source.get("MARKETPILOT_DATA_DIR") or "data"))
    sync_path = data_dir / "portfolio_sync.jsonl"
    symbol = _required_probe_text(source, "MARKETPILOT_OPERATOR_PAPER_PROBE_SYMBOL").upper()
    sector = str(source.get("MARKETPILOT_OPERATOR_PAPER_PROBE_SECTOR") or "Technology").strip() or "Technology"
    entry = _required_positive_decimal(source, "MARKETPILOT_OPERATOR_PAPER_PROBE_ENTRY_PRICE")
    stop = _required_positive_decimal(source, "MARKETPILOT_OPERATOR_PAPER_PROBE_STOP_PRICE")
    target = _required_positive_decimal(source, "MARKETPILOT_OPERATOR_PAPER_PROBE_TARGET_PRICE")
    if stop >= entry or target <= entry:
        raise ValueError("operator paper probe requires stop < entry < target.")

    def factory(run_id: str) -> RuntimeOrchestrationInput | None:
        latest_sync = read_last_sync_record(sync_path)
        if latest_sync is None:
            return None
        return _build_operator_paper_probe_runtime_input(
            run_id=run_id,
            sync_record=latest_sync,
            symbol=symbol,
            sector=sector,
            entry_price=entry,
            stop_price=stop,
            target_price=target,
        )

    return factory


def _build_operator_paper_probe_runtime_input(
    *,
    run_id: str,
    sync_record: Mapping[str, object],
    symbol: str,
    sector: str,
    entry_price: Decimal,
    stop_price: Decimal,
    target_price: Decimal,
) -> RuntimeOrchestrationInput | None:
    if str(sync_record.get("sync_status") or "") != "success":
        return None
    if sync_record.get("reconciliation_clean") is not True:
        return None

    source_timestamp = _parse_sync_timestamp(sync_record.get("source_timestamp"))
    portfolio_data = sync_record.get("portfolio")
    if not isinstance(portfolio_data, Mapping):
        return None

    cash = _decimal_from_mapping(portfolio_data, "cash")
    equity = _decimal_from_mapping(portfolio_data, "equity")
    if cash is None or equity is None or cash <= 0 or equity <= 0:
        return None

    holdings = _holdings_from_portfolio(portfolio_data)
    snapshot = QuantConnectPaperSnapshot(
        fixture_label="render-sync-authoritative-probe",
        captured_at=source_timestamp,
        cash=cash,
        portfolio_equity=equity,
        holdings=holdings,
        orders=(),
        fills=(),
        deployment_status=_deployment_status(sync_record.get("deployment_status")),
        algorithm_status=_algorithm_status(sync_record.get("algorithm_status")),
        performance=QuantConnectPaperPerformance(
            total_orders=int(sync_record.get("orders_count") or 0),
            total_fills=int(sync_record.get("fills_count") or 0),
            unrealized_profit=_decimal_from_mapping(portfolio_data, "unrealized_profit") or Decimal("0"),
        ),
    )
    timing = SetupTiming(signal_time=source_timestamp, strategy_mode=StrategyMode.DAILY_ONLY, bar_end=source_timestamp)
    reward_risk = (target_price - entry_price) / (entry_price - stop_price)
    setup = SetupResult(
        setup_name="operator_gated_paper_probe",
        symbol=symbol,
        status=SetupStatus.VALID,
        timing=timing,
        evidence=(
            NumericEvidence("close_above_ema50", True, True, True),
            NumericEvidence("ema50_above_ema200", True, True, True),
            NumericEvidence("spy_rs20", 0.04, "> 0", True),
            NumericEvidence("spy_rs60", 0.06, "> 0", True),
            NumericEvidence("rsi14", 55.0, "supporting", True),
            NumericEvidence("breakout_close", float(entry_price), "operator_probe", True),
            NumericEvidence("volume_ratio", 1.8, 1.5, True),
            NumericEvidence("reward_risk_proxy", float(reward_risk), "operator_probe", True),
            NumericEvidence("atr_pct", 4.0, 8.0, True),
            NumericEvidence("regime", "risk_on", "entry_allowed", True),
            NumericEvidence("strategy_mode", StrategyMode.DAILY_ONLY.value, "config", True),
            NumericEvidence("planned_entry_price", float(entry_price), "operator_probe", True),
            NumericEvidence("initial_stop_price", float(stop_price), "operator_probe", True),
            NumericEvidence("target_price", float(target_price), "operator_probe", True),
            NumericEvidence("sector", sector, "operator_probe", True),
            NumericEvidence("operator_gated_paper_probe", True, True, True),
        ),
        explanation=("Operator-gated Paper-only validation probe; not a production strategy signal.",),
    )
    validation = evaluate_activation_gates(
        run_status=BacktestRunStatus.REAL_QUANTCONNECT,
        no_lookahead_passed=True,
        no_fake_results=True,
        coverage_complete=True,
        benchmark_available=True,
        risk_checks_passed=True,
        assumptions_present=True,
        report_complete=True,
        requested_state=ActivationApprovalState.APPROVED_FOR_LIMITED_PAPER,
    )
    portfolio = PortfolioSnapshot(
        simulated_equity=equity,
        available_cash=cash,
        open_positions=len(holdings),
        sector_exposure={sector: Decimal("0")},
        new_entries_today=0,
        portfolio_epoch=f"qc-sync-gen-{sync_record.get('generation', 'unknown')}",
    )
    return RuntimeOrchestrationInput(
        correlation_id=run_id,
        strategy_mode=StrategyMode.DAILY_ONLY,
        setup_results=(setup,),
        validation_decision=validation,
        quantconnect_snapshot=snapshot,
        portfolio_snapshot=portfolio,
        evidence={
            "input_kind": "operator_gated_paper_probe",
            "paper_trading_only": True,
            "probe_is_strategy_signal": False,
            "paper_mode": PaperTradingMode.LIMITED_PAPER.value,
        },
    )


def _holdings_from_portfolio(portfolio_data: Mapping[str, object]) -> tuple[QuantConnectHolding, ...]:
    raw_holdings = portfolio_data.get("holdings")
    if not isinstance(raw_holdings, list):
        return ()
    holdings: list[QuantConnectHolding] = []
    for raw in raw_holdings:
        if not isinstance(raw, Mapping):
            continue
        quantity = int(raw.get("quantity") or 0)
        average_price = _decimal_from_mapping(raw, "average_price") or Decimal("0")
        market_price = _decimal_from_mapping(raw, "market_price") or Decimal("0")
        symbol = str(raw.get("symbol") or "").strip().upper()
        if symbol and quantity and average_price >= 0 and market_price >= 0:
            holdings.append(
                QuantConnectHolding(
                    symbol=symbol,
                    quantity=quantity,
                    average_price=average_price,
                    market_price=market_price,
                )
            )
    return tuple(holdings)


def _deployment_status(value: object) -> QuantConnectDeploymentStatus:
    normalized = str(value or "").strip().lower()
    return QuantConnectDeploymentStatus.RUNNING if normalized == "running" else QuantConnectDeploymentStatus.NOT_RUN


def _algorithm_status(value: object) -> QuantConnectAlgorithmStatus:
    normalized = str(value or "").strip().lower()
    return QuantConnectAlgorithmStatus.RUNNING if normalized == "running" else QuantConnectAlgorithmStatus.NOT_RUN


def _parse_sync_timestamp(value: object) -> datetime:
    if not isinstance(value, str):
        raise ValueError("source_timestamp is required for operator paper probe runtime input.")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("source_timestamp must be timezone-aware.")
    return parsed.astimezone(timezone.utc)


def _decimal_from_mapping(mapping: Mapping[str, object], key: str) -> Decimal | None:
    try:
        return Decimal(str(mapping[key]))
    except (KeyError, InvalidOperation, TypeError, ValueError):
        return None


def _required_probe_text(source: Mapping[str, str], key: str) -> str:
    value = str(source.get(key) or "").strip()
    if not value:
        raise ValueError(f"{key} is required when operator paper probe is enabled.")
    return value


def _required_positive_decimal(source: Mapping[str, str], key: str) -> Decimal:
    value = source.get(key)
    if value is None or str(value).strip() == "":
        raise ValueError(f"{key} is required when operator paper probe is enabled.")
    parsed = Decimal(str(value))
    if parsed <= 0:
        raise ValueError("operator paper probe price inputs must be positive.")
    return parsed


def _env_flag(value: object) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


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


def _publish_shared_heartbeat(sink: object, record: SchedulerHeartbeatRecord) -> bool:
    publish = getattr(sink, "publish_heartbeat", None)
    if not callable(publish):
        return False
    publish(record.to_json_dict())
    return True


@dataclass(frozen=True)
class _TelegramNotificationSink:
    service: TelegramDeliveryService

    def emit(self, event: NotificationDomainEvent) -> bool:
        return self.service.deliver(event).delivered


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
    result = run_production_cycle(config, dependencies=build_production_dependencies_from_env())
    print(json.dumps(result.to_json_dict(), sort_keys=True))
    return 0 if result.status != "failed" else 2


if __name__ == "__main__":
    raise SystemExit(_main())


__all__ = [
    "DashboardExportSink",
    "HeartbeatSink",
    "NotificationSink",
    "ProductionRunnerDependencies",
    "ProductionRuntimeResult",
    "run_production_cycle",
    "run_scheduler_forever",
]
