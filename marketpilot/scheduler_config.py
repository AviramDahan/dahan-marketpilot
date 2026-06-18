from __future__ import annotations

"""Configuration boundary for the MarketPilot production scheduler."""


import os
from dataclasses import dataclass
from pathlib import Path

from marketpilot.constants import PAPER_TRADING_ONLY
from marketpilot.scheduler_calendar import MARKET_TIMEZONE


@dataclass(frozen=True)
class SchedulerConfig:
    project_id: int
    deploy_id: str
    timezone_name: str = MARKET_TIMEZONE
    cadence_minutes: int = 5
    stale_after_seconds: int = 600
    lock_ttl_seconds: int = 900
    data_dir: Path = Path("data")
    sync_jsonl_path: Path = Path("data/portfolio_sync.jsonl")
    signal_ledger_path: Path = Path("data/paper_signal_ledger.jsonl")
    audit_journal_path: Path = Path("data/paper_order_audit.jsonl")
    scheduler_ledger_path: Path = Path("data/scheduler_runs.jsonl")
    heartbeat_path: Path = Path("data/scheduler_heartbeat.jsonl")
    lock_path: Path = Path("data/scheduler.lock.json")
    paper_trading_only: bool = True

    def __post_init__(self) -> None:
        if self.paper_trading_only is not True or PAPER_TRADING_ONLY is not True:
            raise RuntimeError("PAPER_TRADING_ONLY must be True for scheduler startup.")
        if self.project_id <= 0:
            raise ValueError("project_id must be positive")
        if not self.deploy_id.strip():
            raise ValueError("deploy_id is required")
        if self.cadence_minutes <= 0:
            raise ValueError("cadence_minutes must be positive")
        if self.stale_after_seconds <= 0:
            raise ValueError("stale_after_seconds must be positive")
        if self.lock_ttl_seconds <= 0:
            raise ValueError("lock_ttl_seconds must be positive")


def load_scheduler_config_from_env() -> SchedulerConfig:
    project_id = _required_int_env("QC_PROJECT_ID", "QUANTCONNECT_PROJECT_ID")
    deploy_id = _required_env("QC_DEPLOY_ID", "QUANTCONNECT_LIVE_DEPLOY_ID")
    data_dir = Path(os.environ.get("MARKETPILOT_DATA_DIR", "data"))
    cadence_minutes = _optional_int_env("MARKETPILOT_SCHEDULER_CADENCE_MINUTES", 5)
    stale_after_seconds = _optional_int_env("MARKETPILOT_SCHEDULER_STALE_AFTER_SECONDS", 600)
    lock_ttl_seconds = _optional_int_env("MARKETPILOT_SCHEDULER_LOCK_TTL_SECONDS", 900)

    return SchedulerConfig(
        project_id=project_id,
        deploy_id=deploy_id,
        cadence_minutes=cadence_minutes,
        stale_after_seconds=stale_after_seconds,
        lock_ttl_seconds=lock_ttl_seconds,
        data_dir=data_dir,
        sync_jsonl_path=data_dir / "portfolio_sync.jsonl",
        signal_ledger_path=data_dir / "paper_signal_ledger.jsonl",
        audit_journal_path=data_dir / "paper_order_audit.jsonl",
        scheduler_ledger_path=data_dir / "scheduler_runs.jsonl",
        heartbeat_path=data_dir / "scheduler_heartbeat.jsonl",
        lock_path=data_dir / "scheduler.lock.json",
    )


def build_apscheduler_cron_kwargs(config: SchedulerConfig) -> dict[str, object]:
    """Return the cron trigger kwargs used by the Render Background Worker."""

    return {
        "day_of_week": "mon-fri",
        "hour": "9-16",
        "minute": f"*/{config.cadence_minutes}",
        "timezone": config.timezone_name,
    }


def _required_env(*names: str) -> str:
    for name in names:
        value = os.environ.get(name, "").strip()
        if value:
            return value
    joined = " or ".join(names)
    raise RuntimeError(f"{joined} is required for scheduler startup.")


def _required_int_env(*names: str) -> int:
    value = _required_env(*names)
    try:
        return int(value)
    except ValueError as exc:
        joined = " or ".join(names)
        raise RuntimeError(f"{joined} must be an integer.") from exc


def _optional_int_env(name: str, default: int) -> int:
    value = os.environ.get(name, "").strip()
    if not value:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer.") from exc


__all__ = [
    "SchedulerConfig",
    "build_apscheduler_cron_kwargs",
    "load_scheduler_config_from_env",
]

