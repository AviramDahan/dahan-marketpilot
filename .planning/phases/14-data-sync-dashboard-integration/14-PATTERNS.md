# Phase 14: Data Sync & Dashboard Integration - Pattern Map

**Mapped:** 2026-06-16
**Files analyzed:** 7 (new/modified files)
**Analogs found:** 7 / 7

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `marketpilot/sync.py` | service | request-response + CRUD | `marketpilot/reconciliation.py` | role-match |
| `marketpilot/__main__.py` (sync CLI) | utility | request-response | `marketpilot/qc_api.py` (client init pattern) | partial |
| `dashboard/data.py` (add `sync_jsonl` loader) | service | file-I/O | `dashboard/data.py` (`_load_local_json_snapshot`) | exact |
| `dashboard/models.py` (add ERROR freshness state) | model | — | `dashboard/models.py` (`DashboardFreshnessStatus`) | exact |
| `dashboard/config.py` (add `sync_jsonl` data_source_kind) | config | — | `dashboard/config.py` (`data_source_kind`) | exact |
| `dashboard/pages/overview.py` (extend portfolio display) | component | request-response | `dashboard/pages/overview.py` (`build_overview`) | exact |
| `tests/test_sync.py` | test | — | `tests/test_audit_journal.py` + `tests/test_reconciliation.py` | role-match |

## Pattern Assignments

### `marketpilot/sync.py` (service, request-response + CRUD)

**Analog:** `marketpilot/reconciliation.py` (orchestration pattern) + `marketpilot/audit_journal.py` (JSONL I/O)

**Imports pattern** (`reconciliation.py` lines 1-12):
```python
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping

from marketpilot.notification_events import NotificationDomainEvent, event_for_system_incident
from marketpilot.order_lifecycle import OrderIntent, OrderLifecycleEvent
from marketpilot.quantconnect_paper import QuantConnectPaperFill, QuantConnectPaperSnapshot
```

**Safety gate pattern** (`qc_api.py` lines 170-177):
```python
from marketpilot.constants import PAPER_TRADING_ONLY

# At module entry point:
if not PAPER_TRADING_ONLY:
    raise RuntimeError("PAPER_TRADING_ONLY must be True")
```

**Frozen dataclass pattern** (`reconciliation.py` lines 20-34):
```python
@dataclass(frozen=True)
class ReconciliationDecision:
    authoritative_source: str
    block_new_entries: bool
    preserve_exits: bool
    requires_explicit_recovery: bool
    mismatches: tuple[ReconciliationMismatch, ...]
    correlation_id: str
    system_event: NotificationDomainEvent | None = None
```

**JSONL write pattern** (`audit_journal.py` lines 36-42):
```python
class AppendOnlyJsonlAuditJournal:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def append(self, record: AuditJournalRecord) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(record.to_json_dict(), sort_keys=True) + "\n")
```

**NOTE:** Phase 14 uses temp+rename instead of simple append. The audit journal pattern shows the JSONL serialization convention (`json.dumps(record, sort_keys=True) + "\n"`), but the write mechanism must use `tempfile` + `os.replace()` per D-04.

**Alert emission pattern** (`reconciliation.py` lines 80-95):
```python
system_event = None
if block_new_entries:
    system_event = event_for_system_incident(
        correlation_id,
        {
            "authoritative_source": "quantconnect",
            "mismatch_types": tuple(mismatch.mismatch_type.value for mismatch in mismatches),
            "block_new_entries": True,
            "preserve_exits": True,
            "requires_explicit_recovery": True,
        },
        severity="high",
    )
```

**Function signature pattern** (`reconciliation.py` lines 43-52):
```python
def reconcile_quantconnect_state(
    *,
    snapshot: QuantConnectPaperSnapshot,
    correlation_id: str,
    local_order_intents: tuple[OrderIntent, ...] = (),
    local_lifecycle_events: tuple[OrderLifecycleEvent, ...] = (),
    local_audit_records: tuple[Mapping[str, object], ...] = (),
) -> ReconciliationDecision:
```

---

### `marketpilot/__main__.py` — Sync CLI entrypoint (utility, request-response)

**Analog:** `marketpilot/qc_api.py` (client initialization with env vars)

**Environment variable loading pattern** (`qc_api.py` lines 171-178):
```python
user_id = os.environ.get("QUANTCONNECT_USER_ID", "").strip()
api_token = os.environ.get("QUANTCONNECT_API_TOKEN", "").strip()
if not user_id or not api_token:
    raise QCAuthenticationError(
        "QUANTCONNECT_USER_ID and QUANTCONNECT_API_TOKEN environment "
        "variables are required but missing or empty."
    )
```

**Logger setup pattern** (`qc_api.py` lines 158-160):
```python
_logger = logging.getLogger("marketpilot.qc_api")
_logger.addFilter(CredentialRedactionFilter())
```

---

### `dashboard/data.py` — Add `sync_jsonl` loader (service, file-I/O)

**Analog:** `dashboard/data.py` (`_load_local_json_snapshot` at lines 192-218 + `load_dashboard_snapshot` dispatch)

**Source loader dispatch pattern** (`data.py` lines 170-186):
```python
def load_dashboard_snapshot(config: DashboardConfig, *, now: datetime) -> DashboardSnapshot:
    """Load the configured read-only dashboard snapshot or return an honest degraded state."""

    if config.data_source_kind == "none":
        return DashboardDataClient.not_configured(missing=("dashboard_data_source",))

    if config.data_source_kind == "local_json":
        return _load_local_json_snapshot(config.data_source_path, cache_timestamp=now)

    if config.data_source_kind == "object_store":
        return _load_object_store_snapshot(config.data_source_path, cache_timestamp=now)

    return _source_error(
        code="dashboard_source_not_configured",
        message="Unsupported dashboard data source kind.",
        reason="dashboard_data_source",
    )
```

**File-based loader pattern** (`data.py` lines 192-218):
```python
def _load_local_json_snapshot(path_value: str | None, *, cache_timestamp: datetime) -> DashboardSnapshot:
    if not path_value:
        return DashboardDataClient.not_configured(missing=("dashboard_data_source",))
    path = Path(path_value)
    if not path.exists():
        return _source_error(
            code="dashboard_source_missing",
            message=f"Dashboard data source is not available: {path}",
            reason="missing_dashboard_data_source",
            status=DashboardSectionStatus.NOT_AVAILABLE,
        )
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if not isinstance(payload, Mapping):
            raise ValueError("dashboard source root must be a mapping")
        return DashboardDataClient.from_quantconnect_portfolio_fixture(
            payload,
            cache_timestamp=cache_timestamp,
        )
    except Exception as exc:
        return _source_error(
            code="dashboard_source_error",
            message=f"Dashboard data source read failed: {exc}",
            reason="dashboard_source_error",
            status=DashboardSectionStatus.ERROR,
        )
```

**Error snapshot builder pattern** (`data.py` lines 221-247):
```python
def _source_error(
    *,
    code: str,
    message: str,
    reason: str,
    status: DashboardSectionStatus = DashboardSectionStatus.ERROR,
) -> DashboardSnapshot:
    error = DashboardSectionError(code=code, message=message)
    metadata = DashboardSourceMetadata(
        source="dashboard_runtime_source",
        source_timestamp=None,
        cache_timestamp=None,
        freshness_status=DashboardFreshnessStatus.UNKNOWN,
        authority=DashboardAuthority.AUTHORITATIVE,
        reasons=(reason,),
    )
    portfolio = DashboardPortfolioSection(status=status, reasons=(reason,), errors=(error,))
    section = DashboardCollectionSection(status=status, reasons=(reason,), errors=(error,))
    return DashboardSnapshot(
        source_metadata=metadata,
        portfolio=portfolio,
        positions=section,
        ...
    )
```

---

### `dashboard/models.py` — Add ERROR freshness state (model)

**Analog:** `dashboard/models.py` (existing `DashboardFreshnessStatus` enum, line 38)

**Enum extension pattern** (`models.py` lines 38-41):
```python
class DashboardFreshnessStatus(str, Enum):
    FRESH = "fresh"
    STALE = "stale"
    UNKNOWN = "unknown"
```

**Target:** Add `ERROR = "error"` member to this enum. Note `DashboardSectionStatus` already has an `ERROR = "error"` member (line 49), confirming the naming convention.

---

### `dashboard/config.py` — Add `sync_jsonl` data_source_kind (config)

**Analog:** `dashboard/config.py` (existing `data_source_kind` field, line 50)

**Config field pattern** (`config.py` lines 43-51):
```python
@dataclass(frozen=True, repr=False)
class DashboardConfig:
    ...
    stale_warning_seconds: int = 600
    stale_error_seconds: int = 1800
    gentle_poll_seconds: int = 120
    data_source_kind: str = "none"
    data_source_path: str | None = None
```

**Validation pattern** (`config.py` line 55):
```python
object.__setattr__(self, "data_source_kind", self.data_source_kind.strip().lower())
```

**Target:** The `data_source_kind` already supports arbitrary string values dispatched in `load_dashboard_snapshot()`. Adding `"sync_jsonl"` requires only a new `if` branch in the dispatcher. The thresholds `stale_warning_seconds = 600` and `stale_error_seconds = 1800` already match D-09 requirements.

---

### `dashboard/pages/overview.py` — Extend portfolio display (component, request-response)

**Analog:** `dashboard/pages/overview.py` (existing `build_overview` function)

**View builder pattern** (`overview.py` lines 12-33):
```python
@dataclass(frozen=True)
class OverviewView:
    lines: tuple[str, ...]


def build_overview(snapshot: DashboardSnapshot) -> OverviewView:
    metadata = snapshot.source_metadata
    warnings = _system_warnings(snapshot)
    lines = (
        DISCLAIMER,
        f"QuantConnect source: {metadata.source}",
        "Paper mode: paper-only",
        f"Portfolio status: {snapshot.portfolio.status.value}",
        f"Freshness: {metadata.freshness_status.value}",
        f"Open positions: {len(snapshot.positions.items)}",
        f"Recent signals: {len(snapshot.signals.items)}",
        f"Recent activity: {len(snapshot.activity.items)}",
        f"System warnings: {warnings}",
    )
    return OverviewView(lines=lines)
```

**Target:** Extend to include freshness banner, portfolio metrics (cash/equity/unrealized P&L), holdings table, and sync status. Use same `@dataclass(frozen=True)` view model + pure function builder pattern.

---

### `tests/test_sync.py` (test)

**Analog:** `tests/test_audit_journal.py` (JSONL I/O testing) + `tests/test_reconciliation.py` (snapshot fixture pattern)

**Test fixture pattern** (`test_reconciliation.py` lines 26-64):
```python
def _snapshot() -> QuantConnectPaperSnapshot:
    return QuantConnectPaperSnapshot(
        fixture_label="deterministic-test-fixture",
        captured_at=datetime(2026, 6, 14, 14, 0, tzinfo=timezone.utc),
        cash=Decimal("98500"),
        portfolio_equity=Decimal("101250"),
        holdings=(
            QuantConnectHolding(symbol="MSFT", quantity=10, average_price=Decimal("420"), market_price=Decimal("425")),
        ),
        orders=(
            QuantConnectPaperOrder(
                quantconnect_order_id="qc-order-1",
                symbol="MSFT",
                status="filled",
                quantity=10,
                submitted_at=datetime(2026, 6, 14, 14, 1, tzinfo=timezone.utc),
                idempotency_key="intent-msft",
            ),
        ),
        fills=(
            QuantConnectPaperFill(
                quantconnect_order_id="qc-order-1",
                symbol="MSFT",
                quantity=10,
                fill_price=Decimal("421.50"),
                filled_at=datetime(2026, 6, 14, 14, 2, tzinfo=timezone.utc),
            ),
        ),
        deployment_status=QuantConnectDeploymentStatus.RUNNING,
        algorithm_status=QuantConnectAlgorithmStatus.RUNNING,
        performance=QuantConnectPaperPerformance(total_orders=1, total_fills=1, unrealized_profit=Decimal("35")),
    )
```

**tmp_path JSONL test pattern** (`test_audit_journal.py` lines 9-19):
```python
def test_audit_journal_appends_jsonl_records_in_order(tmp_path):
    journal = AppendOnlyJsonlAuditJournal(tmp_path / "audit.jsonl")
    journal.append(AuditJournalRecord("risk_decision", datetime(2026, 6, 14, tzinfo=timezone.utc), "a", {"quantity": 10}))
    journal.append(AuditJournalRecord("order_intent", datetime(2026, 6, 14, tzinfo=timezone.utc), "b", {"token": "secret"}))

    records = journal.read_records()

    assert [record["event_type"] for record in records] == ["risk_decision", "order_intent"]
    assert records[1]["payload"]["token"] == "[redacted]"
```

**Mocked client test pattern** (`test_qc_api.py` lines 37-41):
```python
def _make_client_with_mocked_auth() -> QCApiClient:
    """Create a QCApiClient that skips real credential validation."""
    config = QCApiConfig(user_id="99999", api_token="FAKE-TOKEN-DO-NOT-USE")
    with patch.object(QCApiClient, "_validate_credentials"):
        return QCApiClient(config=config)
```

**Error assertion pattern** (`test_audit_journal.py` lines 22-25):
```python
def test_audit_journal_rejects_invalid_record(tmp_path):
    journal = AppendOnlyJsonlAuditJournal(tmp_path / "audit.jsonl")

    with pytest.raises(ValueError, match="event_type"):
        journal.append(AuditJournalRecord("", datetime(2026, 6, 14, tzinfo=timezone.utc), "a", {}))
```

---

## Shared Patterns

### Safety Gate (PAPER_TRADING_ONLY)
**Source:** `marketpilot/constants.py` + `marketpilot/qc_api.py` lines 232-236
**Apply to:** `marketpilot/sync.py` (initialization)
```python
from marketpilot.constants import PAPER_TRADING_ONLY

if not PAPER_TRADING_ONLY:
    raise RuntimeError("PAPER_TRADING_ONLY must be True")
```

### Frozen Dataclass Records
**Source:** `marketpilot/reconciliation.py` lines 14-34, `marketpilot/audit_journal.py` lines 12-27
**Apply to:** `marketpilot/sync.py` (SyncRecord), `dashboard/models.py` (if new models)
```python
@dataclass(frozen=True)
class SomeRecord:
    field: type
    timestamp: datetime
    # All timestamps as datetime with timezone.utc
```

### UTC Timestamps
**Source:** `marketpilot/audit_journal.py` line 26, `marketpilot/notification_events.py` line 78
**Apply to:** All new modules writing timestamps
```python
from datetime import datetime, timezone

# Storage/creation:
timestamp = datetime.now(timezone.utc)
# Serialization:
data["timestamp"] = self.timestamp.astimezone(timezone.utc).isoformat()
```

### Alert Emission via event_for_system_incident
**Source:** `marketpilot/notification_events.py` lines 242-247
**Apply to:** `marketpilot/sync.py` (discrepancy alerts)
```python
from marketpilot.notification_events import event_for_system_incident

event = event_for_system_incident(
    correlation_id,
    {"authoritative_source": "quantconnect", ...},
    severity="high",
)
```

### Dashboard Degraded State Returns
**Source:** `dashboard/data.py` (`DashboardDataClient.not_configured`, `_source_error`)
**Apply to:** `dashboard/data.py` (sync_jsonl loader — missing file, parse error cases)
```python
# Never crash; return honest degraded snapshot:
return DashboardDataClient.not_configured(missing=("dashboard_data_source",))
# or
return _source_error(code="...", message="...", reason="...", status=DashboardSectionStatus.NOT_AVAILABLE)
```

### Freshness Evaluation Pattern
**Source:** `marketpilot/dashboard_export.py` lines 188-195
**Apply to:** `dashboard/data.py` (sync_jsonl loader — 3-state version)
```python
def _evaluate_freshness(
    self,
    source_timestamp: datetime | None,
    cache_timestamp: datetime,
) -> DashboardFreshnessStatus:
    if source_timestamp is None:
        return DashboardFreshnessStatus.UNKNOWN
    age = (cache_timestamp - source_timestamp).total_seconds()
    if age > self._stale_threshold_seconds:
        return DashboardFreshnessStatus.STALE
    return DashboardFreshnessStatus.FRESH
```

---

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| (none) | — | — | All files have strong analogs in the codebase |

All Phase 14 files map directly to existing codebase patterns. The sync module is thin orchestration glue composing existing tested components.

## Metadata

**Analog search scope:** `marketpilot/`, `dashboard/`, `tests/`
**Files scanned:** 12 analog candidates examined
**Pattern extraction date:** 2026-06-16
