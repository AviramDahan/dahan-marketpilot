# Phase 9: Render Dashboard - Pattern Map

**Mapped:** 2026-06-15
**Files analyzed:** 12 target new/modified areas
**Analogs found:** 12 / 12

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `dashboard/app.py` | component | request-response | `dashboard/app.py` | exact |
| `dashboard/models.py` | model | transform | `dashboard/models.py`, `marketpilot/quantconnect_paper.py` | exact |
| `dashboard/safety_view.py` | utility | transform | `dashboard/safety_view.py` | exact |
| `dashboard/data.py` | service | request-response | `marketpilot/quantconnect_paper.py`, `marketpilot/reconciliation.py` | role-match |
| `dashboard/status.py` | model | transform | `marketpilot/quantconnect_paper.py`, `marketpilot/telegram.py` | role-match |
| `dashboard/auth.py` | utility | request-response | `marketpilot/telegram.py` config loader | role-match |
| `dashboard/redaction.py` | utility | transform | `marketpilot/telegram.py`, `marketpilot/notification_events.py` | exact |
| `dashboard/fx_view.py` | utility | transform | `marketpilot/fx.py` | exact |
| `dashboard/pages/*.py` | component | request-response | `dashboard/app.py`, `dashboard/safety_view.py` | role-match |
| `config/dashboard.yaml` | config | transform | `config/dashboard.yaml`, `config/notifications.yaml` via `marketpilot/telegram.py` | exact |
| `tests/test_dashboard.py` | test | transform | `tests/test_dashboard.py` | exact |
| `tests/test_dashboard_*.py` | test | request-response | `tests/test_telegram_secret_handling.py`, `tests/test_telegram_failure_isolation.py`, `tests/test_quantconnect_paper_contract.py` | role-match |

## Pattern Assignments

### `dashboard/app.py` (component, request-response)

**Analog:** `dashboard/app.py`

**Thin Streamlit UI pattern** (lines 6-19):
```python
def main() -> None:
    try:
        import streamlit as st
    except ModuleNotFoundError as exc:
        raise RuntimeError("Install Streamlit to run the local dashboard shell.") from exc

    lines = safety_lines()
    st.set_page_config(page_title="Dahan MarketPilot", layout="centered")
    st.title(lines[0])
    st.warning(lines[1])
    st.subheader(lines[2])
    st.info(lines[3])
    st.caption(lines[4])
    st.write(lines[5])
```

**Use for Phase 9:** Keep `dashboard/app.py` as the Streamlit composition layer only. It should call pure helpers that return typed view models, lines, tables, and status banners. Do not put QuantConnect parsing, password validation, stale calculations, redaction, or cache policy directly inside Streamlit widget calls.

---

### `dashboard/models.py` (model, transform)

**Analog:** `dashboard/models.py`

**Frozen safety model pattern** (lines 10-21):
```python
@dataclass(frozen=True)
class DashboardSafetyState:
    title: str = "Dahan MarketPilot"
    disclaimer: str = DISCLAIMER
    paper_only_status: str = "Paper-only safety mode"
    read_only_status: str = "Read-only dashboard shell"
    data_status: str = "No live data connected"
    scope_note: str = "Phase 1 displays safety state only."


def default_safety_state() -> DashboardSafetyState:
    return DashboardSafetyState()
```

**Use for Phase 9:** Add frozen dataclasses for dashboard DTOs: source metadata, freshness status, overview cards, portfolio display, positions, trades, signals, backtests, strategy evidence, risk, notifications, activity, and system health. Defaults must be safe and explicit, not optimistic.

---

### `dashboard/safety_view.py` (utility, transform)

**Analog:** `dashboard/safety_view.py`

**Pure render helper pattern** (lines 8-21):
```python
def safety_lines(state: DashboardSafetyState | None = None) -> list[str]:
    current = state or default_safety_state()
    return [
        current.title,
        current.disclaimer,
        current.paper_only_status,
        current.read_only_status,
        current.data_status,
        current.scope_note,
    ]


def render_markdown(state: DashboardSafetyState | None = None) -> str:
    return "\n\n".join(safety_lines(state))
```

**Use for Phase 9:** Build view helpers as pure functions that accept typed dashboard state and return plain strings, lists, dicts, or table rows. Tests should call helpers without importing Streamlit.

---

### `dashboard/data.py` (service, request-response)

**Analog:** `marketpilot/quantconnect_paper.py`

**Typed QuantConnect status/snapshot contracts** (lines 14-33, 88-108, 139-147):
```python
class QuantConnectPaperStatusCode(str, Enum):
    NOT_CONFIGURED = "not_configured"
    NOT_RUN = "not_run"
    CONFIGURED_OPERATOR_ACTION_REQUIRED = "configured_operator_action_required"


@dataclass(frozen=True)
class QuantConnectPaperSnapshot:
    fixture_label: str
    captured_at: datetime
    cash: Decimal
    portfolio_equity: Decimal
    holdings: tuple[QuantConnectHolding, ...]
    orders: tuple[QuantConnectPaperOrder, ...]
    fills: tuple[QuantConnectPaperFill, ...]
    deployment_status: QuantConnectDeploymentStatus
    algorithm_status: QuantConnectAlgorithmStatus
    performance: QuantConnectPaperPerformance
    authoritative_source: str = "quantconnect"

    def __post_init__(self) -> None:
        if self.authoritative_source != "quantconnect":
            raise ValueError("QuantConnect Paper snapshots must use quantconnect as authoritative_source.")


@dataclass(frozen=True)
class QuantConnectPaperStatus:
    status_code: QuantConnectPaperStatusCode
    allowed_brokerage_target: str
    missing_prerequisites: tuple[str, ...] = field(default_factory=tuple)
    reasons: tuple[str, ...] = field(default_factory=tuple)
    command_text: str | None = None
    executed: bool = False
    deployment_id: str | None = None
```

**Fail-visible status pattern** (lines 157-173):
```python
def evaluate_quantconnect_paper_status(
    prerequisites: QuantConnectPaperPrerequisites,
) -> QuantConnectPaperStatus:
    validate_quantconnect_paper_brokerage(prerequisites.brokerage_target)
    missing = prerequisites.missing
    if missing:
        return QuantConnectPaperStatus(
            status_code=QuantConnectPaperStatusCode.NOT_CONFIGURED,
            allowed_brokerage_target=QUANTCONNECT_PAPER_BROKERAGE,
            missing_prerequisites=missing,
            reasons=("missing_quantconnect_prerequisites",),
        )
    return QuantConnectPaperStatus(
        status_code=QuantConnectPaperStatusCode.NOT_RUN,
        allowed_brokerage_target=QUANTCONNECT_PAPER_BROKERAGE,
        reasons=("operator_deployment_not_run",),
    )
```

**Use for Phase 9:** Dashboard data adapters should return typed `not_configured`, `not_available`, `stale`, `error`, or `fresh` results. Production code must not fabricate portfolio/backtest values when QuantConnect data is missing.

---

### `dashboard/status.py` (model, transform)

**Analog:** `marketpilot/reconciliation.py`

**Fail-closed decision model** (lines 31-42, 69-95):
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

block_new_entries = bool(mismatches)
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

**Use for Phase 9:** Status models should keep degraded states visible. A subsystem failure should produce a typed dashboard warning with source, timestamp, operator action, and severity. For dashboard display, no failure should imply healthy state by omission.

---

### `dashboard/auth.py` (utility, request-response)

**Analog:** `marketpilot/telegram.py`

**External-secret config pattern** (lines 259-300, 303-318):
```python
def load_telegram_config(
    path: str | Path = DEFAULT_CONFIG_PATH,
    *,
    env: Mapping[str, str] | None = None,
) -> TelegramConfig:
    """Load Telegram notification settings without reading secrets from files."""

    with Path(path).open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    if not isinstance(loaded, dict):
        raise ValueError("notifications config root must be a mapping.")

    _validate_notifications_config(raw)
    secret_source = env if env is not None else os.environ


def _validate_notifications_config(raw: Mapping[object, object]) -> None:
    if raw.get("paper_trading_only") is not True:
        raise ValueError("notifications.paper_trading_only must be true.")
    if raw.get("delivery_required_for_safety") is not False:
        raise ValueError("notifications.delivery_required_for_safety must be false.")

    for key, value in raw.items():
        normalized = str(key).strip().replace("-", "_").lower()
        if _is_secret_reference_name(normalized):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"notifications.{normalized} must name an external secret reference.")
            continue
        if _looks_secret_key(normalized) and _has_value(value):
            raise ValueError(
                f"notifications.{normalized} must come from an external secret store, not repository config."
            )
```

**Use for Phase 9:** Dashboard password config should store only env var names in repository config. The password value must come from Render env vars or test-provided env mappings. Failed auth must render no dashboard data and must not log or display the raw password.

---

### `dashboard/redaction.py` (utility, transform)

**Analog:** `marketpilot/telegram.py`

**Safe dict and repr pattern** (lines 43-81, 84-114):
```python
@dataclass(frozen=True, repr=False)
class TelegramConfig:
    bot_token: str | None = field(default=None, repr=False)
    chat_id: str | None = field(default=None, repr=False)

    def to_safe_dict(self) -> dict[str, object]:
        return {
            "bot_token": "[redacted]" if self.bot_token else None,
            "chat_id": "[redacted]" if self.chat_id else None,
        }

    def __repr__(self) -> str:
        safe = self.to_safe_dict()
        return f"TelegramConfig({safe!r})"


@dataclass(frozen=True, repr=False)
class TelegramDeliveryResult:
    def to_safe_dict(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "event_type": self.event_type,
            "correlation_id": self.correlation_id,
            "detail": self.detail,
        }
```

**Text redaction pattern** (lines 208-213, 247-251):
```python
def _redact(self, text: str) -> str:
    redacted = text
    for value in (self.config.bot_token, self.config.chat_id):
        if value:
            redacted = redacted.replace(value, "[redacted]")
    return redacted

if not _looks_secret_key(key) and value != "[redacted]":
    lines.append(f"{_label(key)}: {_sanitize_message_value(value)}")
```

**Use for Phase 9:** Every dashboard status/config object that may touch env vars, API keys, passwords, account IDs, tokens, or chat IDs should expose `to_safe_dict()` and `repr=False` for raw secret fields. UI helpers should render safe objects only.

---

### `dashboard/fx_view.py` (utility, transform)

**Analog:** `marketpilot/fx.py`

**USD/NIS validation pattern** (lines 9-17, 28-62):
```python
@dataclass(frozen=True)
class FxSeed:
    starting_budget_nis: Decimal
    initial_usd_ils_rate: Decimal
    starting_cash_usd: Decimal
    trading_currency: str
    display_currency: str
    fx_rate_timestamp: str
    fx_rate_source: str


def build_fx_seed(config: dict[str, object]) -> FxSeed:
    calculated_cash = calculate_starting_cash_usd(
        config.get("starting_budget_nis"),
        config.get("initial_usd_ils_rate"),
    )
    configured_cash = _positive_decimal(config.get("starting_cash_usd"), "starting_cash_usd")

    if abs(configured_cash - calculated_cash) > Decimal("0.01"):
        raise ValueError("starting_cash_usd must match starting_budget_nis / initial_usd_ils_rate.")

    trading_currency = str(config.get("trading_currency", "")).upper()
    display_currency = str(config.get("display_currency", "")).upper()
    if trading_currency != "USD":
        raise ValueError("trading_currency must be USD.")
    if display_currency != "NIS":
        raise ValueError("display_currency must be NIS.")
```

**Use for Phase 9:** Keep USD as accounting/source currency. NIS helpers should be display-only and must include FX source, timestamp, and stale/unavailable status. If FX is missing or stale, render USD normally and mark NIS unavailable rather than inventing a rate.

---

### `config/dashboard.yaml` (config, transform)

**Analog:** `config/dashboard.yaml`

**Read-only config pattern** (lines 1-7):
```yaml
dashboard:
  paper_trading_only: true
  read_only: true
  manual_order_controls_enabled: false
  display_currency: NIS
  trading_currency: USD
  no_live_data_connected: true
```

**Use for Phase 9:** Extend this file only with non-secret keys such as cache TTLs, stale thresholds, section toggles, and env var names. Keep `paper_trading_only: true`, `read_only: true`, and `manual_order_controls_enabled: false` as fail-closed invariants.

---

### `tests/test_dashboard.py` and `tests/test_dashboard_*.py` (test, transform/request-response)

**Analog:** `tests/test_dashboard.py`

**Forbidden text and pure helper test pattern** (lines 8-20, 30-50):
```python
FORBIDDEN_DASHBOARD_TEXT = [
    "portfolio value",
    "mock portfolio",
    "fake holdings",
    "backtest metrics",
    "P&L",
    "profit and loss",
    "submit order",
    "buy button",
    "sell button",
    "order form",
]

def test_dashboard_shell_lines_are_read_only_and_static():
    text = render_markdown()

    assert "Dahan MarketPilot" in text
    assert "Paper-only safety mode" in text
    assert "Read-only dashboard shell" in text
    assert "No live data connected" in text

def test_dashboard_shell_has_no_fake_trading_language():
    combined = "\n".join([...]).lower()

    for forbidden in FORBIDDEN_DASHBOARD_TEXT:
        assert forbidden.lower() not in combined
```

**Secret handling test pattern:** `tests/test_telegram_secret_handling.py` lines 52-82:
```python
safe = config.to_safe_dict()
assert safe["bot_token"] == "[redacted]"
assert safe["chat_id"] == "[redacted]"
assert token_value not in repr(config)
assert chat_value not in repr(config)
assert token_value not in str(safe)
assert chat_value not in str(safe)
```

**Deterministic offline status test pattern:** `tests/test_quantconnect_paper_contract.py` lines 20-34 and 55-83:
```python
status = evaluate_quantconnect_paper_status(QuantConnectPaperPrerequisites())

assert status.status_code is QuantConnectPaperStatusCode.NOT_CONFIGURED
assert status.executed is False
assert status.deployment_id is None
assert status.allowed_brokerage_target == QUANTCONNECT_PAPER_BROKERAGE

status = render_operator_deployment_command(QuantConnectPaperPrerequisites(project_id=True))

assert status.status_code is QuantConnectPaperStatusCode.NOT_CONFIGURED
assert status.command_text is None
assert status.executed is False
assert status.deployment_id is None
assert "api_credentials" in status.missing_prerequisites
```

**Failure isolation test pattern:** `tests/test_telegram_failure_isolation.py` lines 38-56 and 87-108:
```python
results = [service.deliver(event) for event in events]

assert {result.status for result in results} == {TelegramDeliveryStatus.FAILED}
assert all(result.to_safe_dict()["controls_safety_logic"] is False for result in results)
assert all(result.to_safe_dict()["delivery_required_for_safety"] is False for result in results)

before = dict(safety_decision)
result = service.deliver(...)

assert result.status is TelegramDeliveryStatus.FAILED
assert safety_decision == before
```

**Use for Phase 9:** Add tests that instantiate dashboard models and helpers directly with deterministic fixtures. Do not require Streamlit, Render, QuantConnect, Telegram, internet, or real credentials for default unit tests.

## Shared Patterns

### Pure Helpers + Thin UI

**Source:** `dashboard/safety_view.py` lines 8-21 and `dashboard/app.py` lines 6-19  
**Apply to:** `dashboard/app.py`, `dashboard/pages/*.py`, all dashboard view helpers

Keep Streamlit code as a thin renderer over pure functions. Pure helpers should return deterministic values that tests can assert without importing Streamlit.

### Typed Status/Result Models

**Source:** `marketpilot/quantconnect_paper.py` lines 14-33, 88-108, 139-147 and `marketpilot/telegram.py` lines 32-40, 84-114  
**Apply to:** data adapters, cache/freshness state, auth state, system status, notification status, FX display status

Use `Enum` status codes plus frozen dataclasses. Include source, timestamps, reasons, missing prerequisites, and booleans such as `executed=False` where action boundaries matter.

### Secret Redaction

**Source:** `marketpilot/telegram.py` lines 27-29, 43-81, 208-213, 303-318 and `tests/test_telegram_secret_handling.py` lines 52-82  
**Apply to:** auth config, QuantConnect config, Render env status, Telegram status, system health

Never commit raw secret values. Accept env var names in config; read values from injected env mappings or `os.environ`; expose only redacted safe dicts and redacted errors.

### Fail-Closed and Fail-Visible

**Source:** `marketpilot/quantconnect_paper.py` lines 157-173 and `marketpilot/reconciliation.py` lines 45-95  
**Apply to:** QuantConnect source state, cache state, stale data, FX, Telegram, Render config, dashboard auth

Missing or mismatched source data should return typed degraded states and visible warnings. Do not hide unavailable critical sections in a way that implies healthy operation.

### Deterministic Offline Tests

**Source:** `tests/test_quantconnect_paper_contract.py` lines 20-83, `tests/test_telegram_failure_isolation.py` lines 11-35, `tests/test_dashboard.py` lines 30-50  
**Apply to:** all Phase 9 tests

Use local fake clients, fixed datetimes, injected env mappings, temp config files, and typed fixtures. Default tests must not call external APIs or depend on deployed Render/QuantConnect/Telegram resources.

### Read-Only Dashboard Safety

**Source:** `config/dashboard.yaml` lines 1-7 and `tests/test_dashboard.py` lines 8-20  
**Apply to:** dashboard UI, config, tests, docs

Keep allowed actions limited to login/logout/view/refresh. Tests should scan source and rendered helper output for order-entry language and fake trading claims.

## No Analog Found

All Phase 9 target areas have usable analogs. There is no existing full Streamlit multi-page dashboard, no existing dashboard password module, and no existing dashboard cache module; implement those by combining the analog patterns above rather than introducing new architectural styles.

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `dashboard/auth.py` | utility | request-response | No dashboard auth exists; use Telegram config secret-reference pattern and dashboard no-leak tests. |
| `dashboard/cache.py` | utility | transform | No dashboard cache exists; use typed status models and stale/fail-visible contracts. |
| `dashboard/pages/*.py` | component | request-response | No multi-page Streamlit structure exists; keep pages thin like current `dashboard/app.py`. |

## Metadata

**Analog search scope:** `dashboard/`, `marketpilot/`, `config/`, `tests/`, `.planning/phases/09-render-dashboard/09-CONTEXT.md`  
**Files scanned:** 18 source/config/test/context files plus relevant test file listing  
**Pattern extraction date:** 2026-06-15
