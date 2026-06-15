"""Single-cycle QuantConnect portfolio synchronization."""

from __future__ import annotations

import argparse
import json
import logging
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Literal, Mapping, Sequence

from marketpilot.constants import PAPER_TRADING_ONLY
from marketpilot.notification_events import NotificationDomainEvent, event_for_system_incident
from marketpilot.qc_api import QCApiClient, QCApiError
from marketpilot.quantconnect_paper import QuantConnectPaperSnapshot
from marketpilot.reconciliation import (
    ReconciliationDecision,
    ReconciliationMismatchType,
    reconcile_quantconnect_state,
)


DEFAULT_JSONL_PATH = Path("data/portfolio_sync.jsonl")

_logger = logging.getLogger("marketpilot.sync")
_MATERIAL_MISMATCH_TYPES = {
    ReconciliationMismatchType.ORDER_ID,
    ReconciliationMismatchType.ORDER_STATE,
    ReconciliationMismatchType.FILL_DATA,
}
_VALUE_THRESHOLD_MISMATCH_TYPES = {
    ReconciliationMismatchType.CASH,
    ReconciliationMismatchType.HOLDINGS,
}
_VALUE_THRESHOLD_RATIO = Decimal("0.01")


@dataclass(frozen=True)
class SyncRecord:
    generation: int
    source_timestamp: datetime
    captured_at: datetime
    sync_status: Literal["success", "api_error", "reconciliation_mismatch"]
    reconciliation_clean: bool
    portfolio: Mapping[str, object]
    orders_count: int
    fills_count: int
    deployment_status: str
    algorithm_status: str
    error_detail: str | None = None

    def to_json_dict(self) -> dict[str, object]:
        """Serialize a sync record with UTC ISO-8601 timestamps."""

        return {
            "generation": self.generation,
            "source_timestamp": _utc_isoformat(self.source_timestamp),
            "captured_at": _utc_isoformat(self.captured_at),
            "sync_status": self.sync_status,
            "reconciliation_clean": self.reconciliation_clean,
            "portfolio": dict(self.portfolio),
            "orders_count": self.orders_count,
            "fills_count": self.fills_count,
            "deployment_status": self.deployment_status,
            "algorithm_status": self.algorithm_status,
            "error_detail": self.error_detail,
        }


@dataclass(frozen=True)
class SyncResult:
    status: str
    generation: int | None = None
    error: str | None = None
    alert_emitted: bool = False


def atomic_jsonl_append(path: Path, record: dict) -> None:
    """Append one JSON record using a same-directory temp file and atomic replace."""

    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, sort_keys=True) + "\n"
    existing = ""
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if existing and not existing.endswith("\n"):
            existing += "\n"

    fd, tmp_path = tempfile.mkstemp(dir=path.parent, prefix=".sync_", suffix=".tmp")
    tmp_name = str(tmp_path)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            fd = -1
            handle.write(existing)
            handle.write(line)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    finally:
        if fd >= 0:
            os.close(fd)
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def read_last_sync_record(path: Path) -> dict | None:
    """Read the last non-empty JSONL record, or None for missing/empty files."""

    if not path.exists() or path.stat().st_size == 0:
        return None

    with path.open("rb") as handle:
        handle.seek(0, os.SEEK_END)
        size = handle.tell()
        chunk_size = min(size, 4096)
        handle.seek(-chunk_size, os.SEEK_END)
        chunk = handle.read().decode("utf-8")

    lines = [line for line in chunk.splitlines() if line.strip()]
    if not lines:
        return None
    if size > 4096 and "\n" not in chunk:
        return _read_last_sync_record_full(path)
    try:
        return json.loads(lines[-1])
    except json.JSONDecodeError:
        if size > 4096:
            return _read_last_sync_record_full(path)
        raise


def sync_portfolio(
    *,
    project_id: int,
    deploy_id: str,
    jsonl_path: Path,
    client: QCApiClient | None = None,
) -> SyncResult:
    """Execute one poll -> reconcile -> alert -> persist portfolio sync cycle."""

    if PAPER_TRADING_ONLY is not True:
        raise RuntimeError("PAPER_TRADING_ONLY must be True for portfolio sync.")

    if client is None:
        client = QCApiClient()

    try:
        snapshot = client.read_live_algorithm(project_id=project_id, deploy_id=deploy_id)
    except QCApiError as exc:
        record = _build_error_record(jsonl_path, exc)
        atomic_jsonl_append(jsonl_path, record)
        _logger.warning("Portfolio sync API error persisted at generation %s", record["generation"])
        return SyncResult(status="api_error", generation=record["generation"], error=str(exc))

    generation = _next_generation(jsonl_path)
    correlation_id = f"sync-gen-{generation}"
    decision = reconcile_quantconnect_state(
        snapshot=snapshot,
        correlation_id=correlation_id,
        local_order_intents=(),
        local_lifecycle_events=(),
        local_audit_records=(),
    )
    alert_event = _build_discrepancy_alert(correlation_id, decision, snapshot)
    record = _build_success_record(jsonl_path, snapshot, decision, generation=generation)
    atomic_jsonl_append(jsonl_path, record)
    _logger.info("Portfolio sync persisted at generation %s with status %s", generation, record["sync_status"])
    return SyncResult(status="success", generation=generation, alert_emitted=alert_event is not None)


def _next_generation(path: Path) -> int:
    last = read_last_sync_record(path)
    if last is None:
        return 1
    return int(last["generation"]) + 1


def _exceeds_threshold(decision: ReconciliationDecision, snapshot: QuantConnectPaperSnapshot) -> bool:
    for mismatch in decision.mismatches:
        if mismatch.mismatch_type in _MATERIAL_MISMATCH_TYPES:
            return True
        if mismatch.mismatch_type in _VALUE_THRESHOLD_MISMATCH_TYPES:
            if _relative_difference_exceeds_threshold(
                mismatch.local_value,
                mismatch.quantconnect_value,
                snapshot.portfolio_equity,
            ):
                return True
    return False


def _build_success_record(
    path: Path,
    snapshot: QuantConnectPaperSnapshot,
    decision: ReconciliationDecision,
    *,
    generation: int | None = None,
) -> dict:
    clean = len(decision.mismatches) == 0
    record = SyncRecord(
        generation=generation if generation is not None else _next_generation(path),
        source_timestamp=snapshot.captured_at,
        captured_at=datetime.now(timezone.utc),
        sync_status="success" if clean else "reconciliation_mismatch",
        reconciliation_clean=clean,
        portfolio=_serialize_portfolio(snapshot),
        orders_count=len(snapshot.orders),
        fills_count=len(snapshot.fills),
        deployment_status=snapshot.deployment_status.value,
        algorithm_status=snapshot.algorithm_status.value,
        error_detail=None,
    )
    return record.to_json_dict()


def _build_error_record(path: Path, exc: Exception) -> dict:
    now = datetime.now(timezone.utc)
    record = SyncRecord(
        generation=_next_generation(path),
        source_timestamp=now,
        captured_at=now,
        sync_status="api_error",
        reconciliation_clean=False,
        portfolio={},
        orders_count=0,
        fills_count=0,
        deployment_status="unknown",
        algorithm_status="unknown",
        error_detail=str(exc),
    )
    return record.to_json_dict()


def _main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a single QuantConnect portfolio sync cycle.")
    parser.add_argument("command", nargs="?", default="sync", choices=("sync",), help="Command to execute.")
    parser.add_argument(
        "--jsonl-path",
        default=str(DEFAULT_JSONL_PATH),
        help="Path to the portfolio sync JSONL file.",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    try:
        project_id = _read_project_id_from_env()
        deploy_id = _read_required_env("QC_DEPLOY_ID")
    except ValueError as exc:
        print(f"Sync configuration error: {exc}")
        return 1

    result = sync_portfolio(project_id=project_id, deploy_id=deploy_id, jsonl_path=Path(args.jsonl_path))
    if result.status == "api_error":
        print(f"Sync failed: status={result.status}, error={result.error}")
        return 1
    print(f"Sync complete: status={result.status}, generation={result.generation}")
    return 0


def _build_discrepancy_alert(
    correlation_id: str,
    decision: ReconciliationDecision,
    snapshot: QuantConnectPaperSnapshot,
) -> NotificationDomainEvent | None:
    if not _exceeds_threshold(decision, snapshot):
        return None
    return event_for_system_incident(
        correlation_id,
        {
            "alert_type": "SYNC_DISCREPANCY",
            "authoritative_source": "quantconnect",
            "mismatch_types": tuple(mismatch.mismatch_type.value for mismatch in decision.mismatches),
            "auto_correct": False,
        },
        severity="high",
    )


def _serialize_portfolio(snapshot: QuantConnectPaperSnapshot) -> dict[str, object]:
    return {
        "cash": str(snapshot.cash),
        "equity": str(snapshot.portfolio_equity),
        "holdings": [
            {
                "symbol": holding.symbol,
                "quantity": holding.quantity,
                "average_price": str(holding.average_price),
                "market_price": str(holding.market_price),
            }
            for holding in snapshot.holdings
        ],
        "unrealized_profit": str(snapshot.performance.unrealized_profit),
    }


def _relative_difference_exceeds_threshold(
    local_value: object,
    quantconnect_value: object,
    portfolio_equity: Decimal,
) -> bool:
    if portfolio_equity <= 0:
        return False
    local_decimal = _to_decimal(local_value)
    quantconnect_decimal = _to_decimal(quantconnect_value)
    if local_decimal is None or quantconnect_decimal is None:
        return False
    return abs(local_decimal - quantconnect_decimal) / portfolio_equity > _VALUE_THRESHOLD_RATIO


def _to_decimal(value: object) -> Decimal | None:
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None


def _read_last_sync_record_full(path: Path) -> dict | None:
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        return None
    return json.loads(lines[-1])


def _utc_isoformat(value: datetime) -> str:
    if value.tzinfo is None:
        raise ValueError("sync timestamps must be timezone-aware UTC datetimes.")
    return value.astimezone(timezone.utc).isoformat()


def _read_project_id_from_env() -> int:
    raw = _read_required_env("QC_PROJECT_ID")
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError("QC_PROJECT_ID must be an integer.") from exc


def _read_required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ValueError(f"{name} environment variable is required but missing or empty.")
    return value


if __name__ == "__main__":
    raise SystemExit(_main())
