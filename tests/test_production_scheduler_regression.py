from marketpilot.constants import PAPER_TRADING_ONLY
from marketpilot.production_runner import run_production_cycle
from marketpilot.scheduler_calendar import evaluate_market_session
from marketpilot.scheduler_config import SchedulerConfig, build_apscheduler_cron_kwargs
from marketpilot.scheduler_health import evaluate_scheduler_heartbeat
from marketpilot.scheduler_jobs import SchedulerJobId
from marketpilot.scheduler_lock import FileLockStore
from marketpilot.scheduler_storage import JsonlSchedulerStorage


def test_phase_16_public_boundaries_import_without_starting_external_work(tmp_path):
    config = SchedulerConfig(project_id=123, deploy_id="L-paper", data_dir=tmp_path)

    assert PAPER_TRADING_ONLY is True
    assert callable(run_production_cycle)
    assert callable(evaluate_market_session)
    assert callable(evaluate_scheduler_heartbeat)
    assert build_apscheduler_cron_kwargs(config)["timezone"] == "America/New_York"
    assert SchedulerJobId.MARKET_GUARD.value == "market_guard"
    assert FileLockStore(tmp_path / "lock.json").inspect() is None
    assert JsonlSchedulerStorage(tmp_path / "runs.jsonl").read_records() == ()

