from datetime import datetime, timezone
from decimal import Decimal

from marketpilot.backtesting import BacktestRunStatus
from marketpilot.notification_events import FakeNotificationCollector
from marketpilot.paper_modes import PaperTradingMode
from marketpilot.production_runner import (
    ProductionRunnerDependencies,
    build_production_dependencies_from_env,
    run_production_cycle,
)
from marketpilot.quantconnect_paper import (
    QuantConnectAlgorithmStatus,
    QuantConnectDeploymentStatus,
    QuantConnectPaperPerformance,
    QuantConnectPaperSnapshot,
)
from marketpilot.risk import PortfolioSnapshot
from marketpilot.runtime_orchestrator import RuntimeOrchestrationInput
from marketpilot.scheduler_config import SchedulerConfig
from marketpilot.scheduler_jobs import SchedulerJobId, SchedulerJobStatus
from marketpilot.setups.base import NumericEvidence, SetupResult, SetupStatus, SetupTiming
from marketpilot.sync import SyncResult
from marketpilot.timeframes import StrategyMode
from marketpilot.validation import ActivationApprovalState, evaluate_activation_gates


class FakeSubmitResult:
    status = "command_delivered"
    command_delivered = True


class FakePollResult:
    observed_count = 1
    audit_record_count = 1
    warning_count = 0


class FakeDashboardSink:
    def __init__(self) -> None:
        self.payloads: list[str] = []

    def publish(self, payload_json: str) -> None:
        self.payloads.append(payload_json)


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


def _sync_success(**_kwargs):
    return SyncResult(status="success", generation=1)


def _runtime_input(correlation_id: str) -> RuntimeOrchestrationInput:
    signal_time = datetime(2026, 6, 16, 14, 0, tzinfo=timezone.utc)
    setup = SetupResult(
        setup_name="relative_strength_leader",
        symbol="MSFT",
        status=SetupStatus.VALID,
        timing=SetupTiming(signal_time=signal_time, strategy_mode=StrategyMode.DAILY_ONLY, bar_end=signal_time),
        evidence=(
            NumericEvidence("close_above_ema50", True, True, True),
            NumericEvidence("ema50_above_ema200", True, True, True),
            NumericEvidence("spy_rs20", 0.04, "> 0", True),
            NumericEvidence("spy_rs60", 0.06, "> 0", True),
            NumericEvidence("rsi14", 55.0, "supporting", True),
            NumericEvidence("breakout_close", 100.0, 99.0, True),
            NumericEvidence("volume_ratio", 1.8, 1.5, True),
            NumericEvidence("reward_risk_proxy", 2.5, 2.0, True),
            NumericEvidence("atr_pct", 4.0, 8.0, True),
            NumericEvidence("regime", "risk_on", "entry_allowed", True),
            NumericEvidence("strategy_mode", "daily_only", "config", True),
            NumericEvidence("planned_entry_price", 100.0, "later_valid_price", True),
            NumericEvidence("initial_stop_price", 95.0, "risk_model", True),
            NumericEvidence("target_price", 112.5, "risk_model", True),
            NumericEvidence("sector", "Technology", "classification_source", True),
        ),
        explanation=("Deterministic valid setup fixture.",),
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
    snapshot = QuantConnectPaperSnapshot(
        fixture_label="deterministic-test-fixture",
        captured_at=signal_time,
        cash=Decimal("100000"),
        portfolio_equity=Decimal("100000"),
        holdings=(),
        orders=(),
        fills=(),
        deployment_status=QuantConnectDeploymentStatus.RUNNING,
        algorithm_status=QuantConnectAlgorithmStatus.RUNNING,
        performance=QuantConnectPaperPerformance(total_orders=0, total_fills=0, unrealized_profit=Decimal("0")),
    )
    portfolio = PortfolioSnapshot(
        simulated_equity=Decimal("100000"),
        available_cash=Decimal("100000"),
        open_positions=0,
        sector_exposure={"Technology": Decimal("0")},
        new_entries_today=0,
        portfolio_epoch="qc-paper-epoch-1",
    )
    return RuntimeOrchestrationInput(
        correlation_id=correlation_id,
        strategy_mode=StrategyMode.DAILY_ONLY,
        setup_results=(setup,),
        validation_decision=validation,
        quantconnect_snapshot=snapshot,
        portfolio_snapshot=portfolio,
    )


def test_production_cycle_runs_signal_to_order_poll_with_fakes(tmp_path):
    dashboard = FakeDashboardSink()
    notifications = FakeNotificationCollector()
    config = _config(tmp_path)

    result = run_production_cycle(
        config,
        now=datetime(2026, 6, 16, 14, 0, tzinfo=timezone.utc),
        dependencies=ProductionRunnerDependencies(
            sync_func=_sync_success,
            runtime_input_factory=_runtime_input,
            submit_signal_func=lambda **_kwargs: FakeSubmitResult(),
            poll_orders_func=lambda **_kwargs: FakePollResult(),
            dashboard_export_sink=dashboard,
            notification_sink=notifications,
        ),
    )

    assert result.status == "completed"
    assert result.order_intent_count == 1
    assert result.delivered_signal_count == 1
    assert result.observed_order_count == 1
    assert dashboard.payloads
    assert notifications.events
    assert {job.job_id for job in result.job_results} == set(SchedulerJobId)


def test_production_cycle_skips_closed_market_without_qc_calls(tmp_path):
    calls = {"sync": 0}

    def sync_never(**_kwargs):
        calls["sync"] += 1
        return SyncResult(status="success", generation=1)

    result = run_production_cycle(
        _config(tmp_path),
        now=datetime(2026, 6, 20, 14, 0, tzinfo=timezone.utc),
        dependencies=ProductionRunnerDependencies(sync_func=sync_never),
    )

    assert calls["sync"] == 0
    assert result.job_results[0].job_id is SchedulerJobId.MARKET_GUARD
    assert result.job_results[0].status is SchedulerJobStatus.SKIPPED
    assert result.job_results[1].job_id is SchedulerJobId.QC_SYNC
    assert result.job_results[1].status is SchedulerJobStatus.SKIPPED


def test_production_cycle_prevents_overlapping_runs(tmp_path):
    config = _config(tmp_path)
    now = datetime(2026, 6, 16, 14, 0, tzinfo=timezone.utc)

    from marketpilot.scheduler_lock import FileLockStore

    lock = FileLockStore(config.lock_path)
    lock.acquire(run_id="existing-run", owner="worker-a", now=now, ttl_seconds=600)

    result = run_production_cycle(config, now=now, owner="worker-b")

    assert result.status == "skipped_overlap"
    assert result.job_results[0].details["locked_run_id"] == "existing-run"


def test_production_dependencies_from_env_are_empty_without_external_secrets():
    deps = build_production_dependencies_from_env(env={})

    assert deps.dashboard_export_sink is None
    assert deps.notification_sink is None
    assert deps.lock_store is None
