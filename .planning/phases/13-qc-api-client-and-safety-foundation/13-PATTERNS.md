# Phase 13: QC API Client & Safety Foundation - Pattern Map

**Mapped:** 2026-06-16
**Files analyzed:** 5
**Analogs found:** 5 / 5

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `marketpilot/qc_api.py` | service | request-response | `marketpilot/reconciliation.py` + `marketpilot/safety.py` | role-match |
| `tests/test_qc_api.py` | test | request-response | `tests/test_reconciliation.py` + `tests/test_safety.py` | exact |
| `.pre-commit-config.yaml` | config | — | (no analog — new config type) | no-analog |
| `.secrets.baseline` | config | — | (no analog — generated file) | no-analog |
| `requirements.txt` / `pyproject.toml` | config | — | `requirements.txt` / `pyproject.toml` (self) | exact |

## Pattern Assignments

### `marketpilot/qc_api.py` (service, request-response)

**Analog:** `marketpilot/safety.py` (fail-closed validation pattern), `marketpilot/reconciliation.py` (QC type consumer), `marketpilot/configuration.py` (config loading)

**Imports pattern** (`safety.py` lines 1-8):
```python
"""Fail-closed safety validation for Dahan MarketPilot configuration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from marketpilot.constants import PAPER_TRADING_ONLY
```

**Module docstring convention** (all modules use triple-quote docstrings at line 1):
```python
"""QuantConnect Cloud Paper Trading prerequisite and operator-command contracts."""
```

**Frozen dataclass pattern** (`safety.py` lines 55-60):
```python
@dataclass(frozen=True)
class SafetyIssue:
    """A sanitized validation issue safe for logs, tests, and UI surfaces."""

    path: str
    code: str
    message: str
```

**Custom exception with structured data** (`safety.py` lines 63-70):
```python
class SafetyValidationError(ValueError):
    """Raised when configuration violates the paper-only safety contract."""

    def __init__(self, issues: Iterable[SafetyIssue]):
        self.issues = tuple(issues)
        summary = "; ".join(f"{issue.path}: {issue.message}" for issue in self.issues)
        super().__init__(summary or "Unsafe configuration rejected.")
```

**PAPER_TRADING_ONLY assertion pattern** (`safety.py` lines 73-84):
```python
def validate_paper_trading_constant() -> None:
    """Ensure the central guard has not been modified."""

    if PAPER_TRADING_ONLY is not True:
        raise SafetyValidationError(
            [
                SafetyIssue(
                    path="PAPER_TRADING_ONLY",
                    code="paper_guard_disabled",
                    message="Central paper-only guard must remain true.",
                )
            ]
        )
```

**QC dataclass imports pattern** (`reconciliation.py` lines 1-12):
```python
"""QuantConnect-authoritative Paper Trading reconciliation contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping

from marketpilot.notification_events import NotificationDomainEvent, event_for_system_incident
from marketpilot.order_lifecycle import OrderIntent, OrderLifecycleEvent
from marketpilot.quantconnect_paper import QuantConnectPaperFill, QuantConnectPaperSnapshot
```

**Enum pattern for status codes** (`quantconnect_paper.py` lines 14-37):
```python
class QuantConnectDeploymentStatus(str, Enum):
    NOT_CONFIGURED = "not_configured"
    NOT_RUN = "not_run"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"


class QuantConnectAlgorithmStatus(str, Enum):
    NOT_CONFIGURED = "not_configured"
    NOT_RUN = "not_run"
    RUNNING = "running"
    STOPPED = "stopped"
    RUNTIME_ERROR = "runtime_error"
```

**Frozen dataclass with validation** (`quantconnect_paper.py` lines 40-47):
```python
@dataclass(frozen=True)
class QuantConnectHolding:
    symbol: str
    quantity: int
    average_price: Decimal
    market_price: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(self, "symbol", self.symbol.strip().upper())
```

**Config dataclass pattern** (`configuration.py` lines 17-25):
```python
@dataclass(frozen=True)
class EnvironmentConfig:
    name: str
    paper_trading_only: bool
    fx_seed: FxSeed
```

**Function signature with keyword-only args** (`reconciliation.py` lines 52-60):
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

### `tests/test_qc_api.py` (test, request-response)

**Analog:** `tests/test_safety.py` (safety assertion testing), `tests/test_reconciliation.py` (QC dataclass fixture construction)

**Test imports pattern** (`test_safety.py` lines 1-5):
```python
import pytest

from marketpilot.constants import PAPER_TRADING_ONLY
from marketpilot.safety import SafetyValidationError, validate_safety_config
```

**Simple assertion test** (`test_safety.py` lines 8-9):
```python
def test_central_paper_trading_guard_is_true():
    assert PAPER_TRADING_ONLY is True
```

**Exception matching with pytest.raises** (`test_safety.py` lines 12-14):
```python
def test_paper_trading_only_false_fails():
    with pytest.raises(SafetyValidationError, match="paper_trading_only"):
        validate_safety_config({"paper_trading_only": False})
```

**Parametrized test** (`test_safety.py` lines 17-34):
```python
@pytest.mark.parametrize(
    "key",
    [
        "real_broker_enabled",
        "live_money_enabled",
        "leverage_allowed",
        ...
    ],
)
def test_unsafe_feature_classes_fail(key):
    with pytest.raises(SafetyValidationError):
        validate_safety_config({"paper_trading_only": True, key: True})
```

**Secret non-leakage assertion** (`test_safety.py` lines 37-42):
```python
def test_real_broker_credentials_fail_without_leaking_value():
    secret_value = "super-secret-token"
    with pytest.raises(SafetyValidationError) as exc:
        validate_safety_config({"paper_trading_only": True, "broker_api_key": secret_value})

    assert secret_value not in str(exc.value)
    assert "broker_api_key" in str(exc.value)
```

**Fixture helper function** (`test_reconciliation.py` lines 24-62):
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
        ...
    )
```

**Test naming convention** (all tests use `test_<what_is_being_tested>` with descriptive snake_case):
```python
def test_quantconnect_snapshot_fields_are_authoritative():
def test_reconciliation_mismatch_blocks_new_entries_preserves_exits_and_emits_high_severity_event():
```

**tmp_path fixture for file-based tests** (`test_configuration.py` lines 23-24):
```python
def test_yaml_loader_uses_safe_load_for_plain_mappings(tmp_path):
    path = tmp_path / "safe.yaml"
    path.write_text("paper_trading_only: true\n", encoding="utf-8")
```

---

### `requirements.txt` / `pyproject.toml` (config, MODIFIED)

**Analog:** Self (existing files)

**requirements.txt pattern** (lines 1-2):
```
PyYAML>=6.0.2
streamlit>=1.51,<2
```
Convention: `package>=min_version` with optional upper bound.

**pyproject.toml dependencies section** (lines 12-15):
```toml
dependencies = [
  "PyYAML>=6.0.2",
  "streamlit>=1.51,<2",
]
```

**Dev dependencies** (`requirements-dev.txt` lines 1-2):
```
-r requirements.txt
pytest>=8.0
```

**pyproject.toml dev extras** (lines 18-20):
```toml
[project.optional-dependencies]
dev = [
  "pytest>=8.0",
]
```

---

## Shared Patterns

### Safety-First Module Guard
**Source:** `marketpilot/safety.py` lines 73-84
**Apply to:** `marketpilot/qc_api.py` — startup assertion and per-request validation
```python
from marketpilot.constants import PAPER_TRADING_ONLY

def validate_paper_trading_constant() -> None:
    if PAPER_TRADING_ONLY is not True:
        raise SafetyValidationError(
            [SafetyIssue(path="PAPER_TRADING_ONLY", code="paper_guard_disabled",
                         message="Central paper-only guard must remain true.")]
        )
```

### Frozen Dataclass Convention
**Source:** `marketpilot/quantconnect_paper.py` (entire file), `marketpilot/safety.py` lines 55-60
**Apply to:** `QCApiConfig` dataclass in `qc_api.py`
```python
@dataclass(frozen=True)
class QuantConnectHolding:
    symbol: str
    quantity: int
    average_price: Decimal
    market_price: Decimal

    def __post_init__(self) -> None:
        object.__setattr__(self, "symbol", self.symbol.strip().upper())
```

### `from __future__ import annotations` (All Modules)
**Source:** Every module in `marketpilot/`
**Apply to:** `qc_api.py`, `test_qc_api.py`
```python
from __future__ import annotations
```

### Secret Non-Leakage Testing
**Source:** `tests/test_safety.py` lines 37-42
**Apply to:** `tests/test_qc_api.py` — credential redaction tests
```python
def test_real_broker_credentials_fail_without_leaking_value():
    secret_value = "super-secret-token"
    with pytest.raises(SafetyValidationError) as exc:
        validate_safety_config({"paper_trading_only": True, "broker_api_key": secret_value})

    assert secret_value not in str(exc.value)
    assert "broker_api_key" in str(exc.value)
```

### Notification Event for System Incidents
**Source:** `marketpilot/notification_events.py` + `marketpilot/reconciliation.py` lines 82-93
**Apply to:** `qc_api.py` — auth failure alerting
```python
from marketpilot.notification_events import event_for_system_incident

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

### Existing QC Dataclass Return Types
**Source:** `marketpilot/quantconnect_paper.py` (full file)
**Apply to:** `qc_api.py` — all endpoint wrappers must return these types
```python
from marketpilot.quantconnect_paper import (
    QuantConnectAlgorithmStatus,
    QuantConnectDeploymentStatus,
    QuantConnectHolding,
    QuantConnectPaperFill,
    QuantConnectPaperOrder,
    QuantConnectPaperPerformance,
    QuantConnectPaperSnapshot,
)
```

---

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `.pre-commit-config.yaml` | config | — | No pre-commit config exists yet in the project; use RESEARCH.md pattern |
| `.secrets.baseline` | config | — | Generated by `detect-secrets scan`; no hand-authoring needed |

---

## Metadata

**Analog search scope:** `marketpilot/`, `tests/`, project root
**Files scanned:** 8 analog candidates read
**Pattern extraction date:** 2026-06-16
