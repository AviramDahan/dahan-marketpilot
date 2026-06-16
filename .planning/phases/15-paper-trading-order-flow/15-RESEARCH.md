# Phase 15: Paper Trading & Order Flow - Research

**Researched:** 2026-06-16
**Domain:** QuantConnect Cloud Paper Trading command delivery, LEAN order handling, fill tracking, and append-only audit traceability
**Confidence:** HIGH for codebase constraints and official QuantConnect API surface; MEDIUM for exact live response payload edge cases that require credentialed execution.

## User Constraints

- Dahan MarketPilot is simulated Paper Trading only, and no real-money trading path, real brokerage credentials, leverage, margin, short selling, options, futures, cryptocurrency trading, Forex, or dashboard order-entry controls may be introduced. [VERIFIED: AGENTS.md]
- QuantConnect is authoritative for simulated cash, portfolio equity, holdings, open positions, orders, fills, Paper Trading state, algorithm status, and QuantConnect Backtest results. [VERIFIED: AGENTS.md]
- Render/Streamlit dashboard remains read-only and must never submit orders or maintain active portfolio authority. [VERIFIED: AGENTS.md]
- Telegram failures must remain independent from trading safety, and notification delivery cannot stop protective trading logic. [VERIFIED: AGENTS.md]
- Credentials, API tokens, brokerage credentials, and secrets must not be printed, logged, stored in repo files, or requested in chat. [VERIFIED: AGENTS.md]
- Core tests must be deterministic offline fixtures/mocks and must not require QuantConnect, Telegram, Render, broker credentials, internet, or real market access. [VERIFIED: AGENTS.md]
- Phase 15 must satisfy PTD-01 through PTD-05, FT-01 through FT-04, and SAFE-05. [VERIFIED: .planning/REQUIREMENTS.md]
- Phase 15 depends on Phase 14 because pre-submission reconciliation and freshness checks require the QuantConnect sync layer. [VERIFIED: .planning/ROADMAP.md]

## Project Constraints (from AGENTS.md)

- Communicate with the user in Hebrew; keep source code, identifiers, file names, configuration, tests, technical documentation, commit messages, GSD planning artifacts, and project files in English. [VERIFIED: AGENTS.md]
- Before phase work, read `.planning/PROJECT.md`, `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`, `.planning/STATE.md`, and `docs/AI-COLLABORATION.md`. [VERIFIED: AGENTS.md]
- Verify current official QuantConnect APIs before using them; do not invent QuantConnect APIs, LEAN classes, Cloud API endpoints, package behavior, or tutorial details. [VERIFIED: AGENTS.md]
- Never invent Paper Trading results, fills, portfolio values, profitability, or backtest claims. [VERIFIED: AGENTS.md]
- Use focused commits for completed verified planning or implementation units when commits are approved. [VERIFIED: AGENTS.md]
- Do not modify completed phases without a change plan. [VERIFIED: AGENTS.md]
- Do not copy third-party source without updating `NOTICE`, `THIRD_PARTY_NOTICES.md`, and related documentation. [VERIFIED: AGENTS.md]

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PTD-01 | Deploy a paper trading algorithm to QC Cloud via API with hardcoded paper-only configuration | Use `/live/create` only through `QCApiClient`, require `QuantConnectBrokerage` plus `environment: live-paper`, `versionId`, `projectId`, `compileId`, `nodeId`, and `dataProviders`; gate duplicate deploy attempts with local idempotency before the request leaves the process. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/create-live-algorithm] |
| PTD-02 | Deliver signals to running algorithm via Commands API without redeployment | Add `QCApiClient.create_live_command()` for `/live/commands/create`; send custom signal payloads to `on_command`, not direct external order commands. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/live-commands/create-live-command] |
| PTD-03 | Stop and liquidate a running paper algorithm via API | Preserve existing paper-gated `stop_live_algorithm()` and `liquidate_live_algorithm()` wrappers; both official endpoints take `projectId` and return a `RestResponse`. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/update-live-algorithm/stop-live-algorithm] [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/update-live-algorithm/liquidate-live-portfolio] |
| PTD-04 | Deployment uses idempotent keys; duplicate deploy requests are safely rejected | Use a deployment ledger entry keyed by project, compile id, node id, brokerage environment, strategy/config version, and paper-only mode before calling `/live/create`. [VERIFIED: marketpilot/order_lifecycle.py] |
| PTD-05 | Algorithm receives signal commands and translates them to paper orders within LEAN | Implement `DahanMarketPilotRuntime.on_command()` and place LEAN paper orders only inside the algorithm after payload validation; official docs state `on_command` receives injected payload data and returns success. [CITED: https://www.quantconnect.com/docs/v2/writing-algorithms/live-trading/commands] |
| FT-01 | Poll QC `/live/orders/read` and map fills to local signal IDs | Add an actual `/live/orders/read` wrapper; the current `read_live_orders()` method calls `/live/read`, which does not meet this requirement. [VERIFIED: marketpilot/qc_api.py] [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/read-live-algorithm/orders] |
| FT-02 | Fill events update local audit journal while QC remains authoritative | Append JSONL audit records from order-poll results and LEAN order tags, but keep QuantConnect as source of truth for order and fill status. [VERIFIED: marketpilot/audit_journal.py] |
| FT-03 | Partial fills and order rejections are tracked with reasons | Map QC/LEAN order statuses into existing lifecycle states `PARTIALLY_FILLED`, `FILLED`, and `REJECTED`; official docs identify `OrderEvent` as the order-state update object and show partial fill handling. [VERIFIED: marketpilot/order_lifecycle.py] [CITED: https://www.quantconnect.com/docs/v2/writing-algorithms/trading-and-orders/order-events] |
| FT-04 | Signal-to-order-to-fill chain is fully traceable in audit log | Carry `correlation_id`, `signal_id`, `idempotency_key`, LEAN order tag, QC order id, status, fill price/quantity/time, and rejection reason through every audit record. [VERIFIED: marketpilot/runtime_orchestrator.py] |
| SAFE-05 | Execution window guards skip stale signals outside valid execution window | Add a stale signal policy before Commands API delivery and again inside `on_command`; skipped signals must produce audit records and no LEAN order. [VERIFIED: .planning/REQUIREMENTS.md] |

</phase_requirements>

## Summary

Phase 15 should add the smallest execution bridge around the existing pure runtime pipeline: the local pipeline still produces `OrderIntent` only, `QCApiClient` delivers validated signal commands to a running QuantConnect paper algorithm, and `lean/main.py` turns those commands into LEAN paper orders inside `on_command`. [VERIFIED: marketpilot/runtime_orchestrator.py] [CITED: https://www.quantconnect.com/docs/v2/writing-algorithms/live-trading/commands]

The safest implementation is not to use QuantConnect's generic `OrderCommand` payload as the primary integration, because PTD-05 requires the algorithm to translate signal commands to paper orders within LEAN. [VERIFIED: .planning/REQUIREMENTS.md] Send a project-specific signal payload with an idempotency key and audit fields, validate freshness and paper-only constraints in both local sender and LEAN receiver, then call LEAN order methods with the idempotency key in the order tag. [CITED: https://www.quantconnect.com/docs/v2/writing-algorithms/trading-and-orders/order-types/market-orders]

Fill tracking should poll `/live/orders/read` for authoritative order state, while `on_order_event` inside LEAN should preserve the immediate signal-to-order mapping in tags/log/evidence where possible. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/read-live-algorithm/orders] [CITED: https://www.quantconnect.com/docs/v2/writing-algorithms/trading-and-orders/order-events] The external audit journal remains append-only JSONL and never becomes portfolio authority. [VERIFIED: marketpilot/audit_journal.py]

**Primary recommendation:** Build Phase 15 as five units: API wrapper corrections, paper deploy ledger, signal command sender, LEAN command/order-event receiver, and order/fill audit poller. [VERIFIED: repo grep]

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|--------------|----------------|-----------|
| Paper deploy request | API / Backend | QuantConnect Cloud | Local code validates idempotency and paper-only payload, then calls QC `/live/create`; QC creates the deployment. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/create-live-algorithm] |
| Signal command delivery | API / Backend | QuantConnect Cloud | Local code sends `/live/commands/create`; QC injects payload into the running algorithm. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/live-commands/create-live-command] |
| Signal-to-order translation | QuantConnect LEAN Algorithm | API / Backend | Orders must be placed inside `lean/main.py` after `on_command` validation, not by external dashboard/API order controls. [VERIFIED: .planning/REQUIREMENTS.md] |
| Fill/rejection detection | QuantConnect Cloud | API / Backend | QC order state is authoritative; local code polls and mirrors to audit JSONL. [VERIFIED: AGENTS.md] |
| Audit traceability | API / Backend | Local JSONL mirror | Audit JSONL records explain what happened but cannot override QC portfolio/order state. [VERIFIED: marketpilot/audit_journal.py] |
| Dashboard display | Browser / Client | Dashboard Server | Existing dashboard reads sync JSONL and remains read-only; Phase 15 should not add order-entry UI. [VERIFIED: dashboard/data.py] |

## Standard Stack

### Core

| Library / Module | Version | Purpose | Why Standard |
|------------------|---------|---------|--------------|
| Python | 3.10.10 installed locally; project requires `>=3.11` | Implementation runtime and tests | Existing project language; planner should note local version mismatch for strict validation. [VERIFIED: pyproject.toml] [VERIFIED: `python --version`] |
| `requests` | Existing transitive/runtime import in `marketpilot/qc_api.py` | HTTP transport to QuantConnect API | Already used by `QCApiClient`; do not add a new HTTP client. [VERIFIED: marketpilot/qc_api.py] |
| `tenacity` | `>=9.0.0` in project dependencies | Retry with exponential jitter | Existing QC API retry foundation from Phase 13. [VERIFIED: pyproject.toml] |
| QuantConnect LEAN | Cloud runtime, version selected by deployment `versionId` | Runs paper algorithm and executes simulated paper orders | Official runtime for `on_command`, `on_order_event`, and Paper Trading execution. [CITED: https://www.quantconnect.com/docs/v2/writing-algorithms/live-trading/commands] |
| Append-only JSONL | Local project pattern | Audit and mirror records | Existing `AppendOnlyJsonlAuditJournal` and sync JSONL patterns are already tested. [VERIFIED: marketpilot/audit_journal.py] [VERIFIED: marketpilot/sync.py] |

### Supporting

| Library / Module | Version | Purpose | When to Use |
|------------------|---------|---------|-------------|
| `pytest` | 7.3.1 installed locally | Offline deterministic tests | Use for Phase 15 API wrapper, command payload, stale-window, and audit poller tests. [VERIFIED: `pytest --version`] |
| `unittest.mock` | Python stdlib | Mock QC API boundaries | Existing tests patch `QCApiClient` and reconciliation boundaries without network access. [VERIFIED: tests/test_sync.py] |
| `datetime` / `zoneinfo` | Python stdlib | UTC/ET freshness windows | Use UTC internally; convert to ET only at market-hours/display boundaries. [VERIFIED: .planning/REQUIREMENTS.md] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Custom signal command handled by `on_command` | QuantConnect `OrderCommand` payload | `OrderCommand` can trigger order placement via command payload, but PTD-05 requires local signal translation inside LEAN, so direct order commands are not the project-standard path. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/live-commands/create-live-command] [VERIFIED: .planning/REQUIREMENTS.md] |
| Poll `/live/orders/read` | Infer fills from local lifecycle only | Local inference would violate QuantConnect source-of-truth policy. [VERIFIED: AGENTS.md] |
| Append-only JSONL audit | SQLite/new database | v1.1 forbids new database infrastructure; JSONL is established for audit mirrors. [VERIFIED: .planning/REQUIREMENTS.md] |

**Installation:**

```bash
# No new external packages recommended for Phase 15.
```

**Version verification:** Existing runtime/test versions were checked with `python --version` and `pytest --version`; no new package install is recommended. [VERIFIED: local shell]

## Package Legitimacy Audit

No new external packages are recommended for Phase 15. [VERIFIED: pyproject.toml]

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| None | N/A | N/A | N/A | N/A | OK | No install needed |

**Packages removed due to [SLOP] verdict:** none.
**Packages flagged as suspicious [SUS]:** none.

## Architecture Patterns

### System Architecture Diagram

```text
Runtime pipeline
  -> OrderIntent(s) with idempotency_key + correlation_id
  -> Pre-submit guards
       -> paper-only constant check
       -> latest Phase 14 sync freshness/reconciliation check
       -> stale signal window check
       -> deploy/signal idempotency ledger check
  -> QCApiClient /live/commands/create
       -> QuantConnect Cloud running paper deployment
       -> lean/main.py on_command(signal_payload)
            -> validate schema + idempotency + stale window + supported asset/scope
            -> LEAN market/limit order with tag=idempotency_key/signal_id
            -> on_order_event(order_event)
                 -> logs/order tag evidence for QC order id/status/fill/rejection
  -> QCApiClient /live/orders/read polling
       -> map QC order id/status/fill data back to idempotency_key
       -> append-only audit JSONL records
       -> optional notification-domain event, safety unaffected by delivery
```

### Recommended Project Structure

```text
marketpilot/
├── qc_api.py                    # Add live commands and real live/orders/read wrappers
├── paper_order_flow.py          # New local deploy/signal/fill orchestration boundary
├── paper_command_models.py      # New frozen dataclasses for signal command payloads and audit mapping
├── order_lifecycle.py           # Reuse lifecycle states and idempotency functions
├── audit_journal.py             # Reuse append-only JSONL writer; add atomic variant if needed
└── sync.py                      # Reuse latest Phase 14 reconciliation/freshness input
lean/
└── main.py                      # Add on_command and on_order_event only; keep strategy logic delegated
tests/
├── test_paper_order_flow.py     # New offline tests for deploy/signal/fill flow
├── test_qc_api.py               # Extend endpoint allowlist/wrapper tests
└── test_lean_command_flow.py    # New fake LEAN adapter tests if feasible without LEAN runtime
```

### Pattern 1: API Wrapper Is the Only QuantConnect REST Boundary

**What:** Add `/live/commands/create` and `/live/orders/read` to `QCApiClient` allowlists and wrappers; no other module should construct QuantConnect URLs. [VERIFIED: tests/test_qc_api.py]

**When to use:** Every local operation that contacts QuantConnect Cloud. [VERIFIED: marketpilot/qc_api.py]

**Example:**

```python
# Source: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/live-commands/create-live-command
def create_live_command(self, *, project_id: int, command: Mapping[str, object]) -> bool:
    payload = {"projectId": project_id, "command": dict(command)}
    response = self._make_request("live/commands/create", payload)
    return bool(response.get("success", False))
```

### Pattern 2: Signal Payload, Not External Order Payload

**What:** Send a project-specific command payload such as `{"command_type": "marketpilot_signal", "signal_id": "...", "idempotency_key": "...", "symbol": "MSFT", "quantity": 10, "signal_time_utc": "...", "expires_at_utc": "..."}` and let `on_command` decide whether to order. [VERIFIED: .planning/REQUIREMENTS.md]

**When to use:** PTD-02/PTD-05 signal delivery. [VERIFIED: .planning/REQUIREMENTS.md]

**Example:**

```python
# Source: https://www.quantconnect.com/docs/v2/writing-algorithms/live-trading/commands
def on_command(self, data):
    command_type = getattr(data, "Command_type", None) or getattr(data, "command_type", None)
    if command_type != "marketpilot_signal":
        self.debug("Rejected unsupported MarketPilot command")
        return False
    # Validate idempotency_key, signal_time_utc, expires_at_utc, symbol, quantity.
    # If valid and fresh, submit a LEAN paper order with tag carrying signal identity.
    return True
```

### Pattern 3: Tag Every LEAN Order for Traceability

**What:** Use LEAN order `tag` to store compact trace fields such as `mp:<signal_id>:<idempotency_key>`. [CITED: https://www.quantconnect.com/docs/v2/writing-algorithms/trading-and-orders/order-types/market-orders]

**When to use:** Every order submitted from `on_command`. [VERIFIED: .planning/REQUIREMENTS.md]

**Example:**

```python
# Source: https://www.quantconnect.com/docs/v2/writing-algorithms/trading-and-orders/order-types/market-orders
ticket = self.market_order(symbol, quantity, tag=tag)
```

### Pattern 4: Poll and Mirror QC Orders, Do Not Infer Authority

**What:** Poll `/live/orders/read` with `algorithmId`, `start`, `end`, and `projectId`, then append local audit records with QC status and mapped signal ids. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/read-live-algorithm/orders]

**When to use:** Fill tracking, partial fill updates, rejection tracking, and recovery after restarts. [VERIFIED: .planning/REQUIREMENTS.md]

**Example:**

```python
# Source: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/read-live-algorithm/orders
payload = {
    "algorithmId": deploy_id,
    "start": start,
    "end": end,
    "projectId": project_id,
}
```

### Anti-Patterns to Avoid

- **Calling QuantConnect order commands directly from local code:** This bypasses PTD-05's requirement that LEAN translate signals to paper orders. [VERIFIED: .planning/REQUIREMENTS.md]
- **Using dashboard controls for order entry:** Render must remain read-only. [VERIFIED: AGENTS.md]
- **Treating command API success as order success:** `/live/commands/create` returns request success; fills/rejections must come from LEAN order events or QC order polling. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/live-commands/create-live-command]
- **Relying only on local lifecycle state:** QuantConnect remains authoritative for order and fill state. [VERIFIED: AGENTS.md]
- **Submitting stale signals after market window drift:** SAFE-05 requires stale signal skips with logged reason. [VERIFIED: .planning/REQUIREMENTS.md]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Cloud command transport | Custom webhook/server inside LEAN | QuantConnect `/live/commands/create` | Official API already injects payloads into running algorithms. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/live-commands/create-live-command] |
| Order execution | External broker/order API | LEAN order methods inside `on_command` | Project requires orders never placed externally. [VERIFIED: .planning/REQUIREMENTS.md] |
| Fill authority | Local simulated fill engine | QuantConnect `/live/orders/read` and `on_order_event` | QC is authoritative and LEAN emits order-state events. [CITED: https://www.quantconnect.com/docs/v2/writing-algorithms/trading-and-orders/order-events] |
| Idempotency hashing | Ad hoc random IDs | Existing `make_order_idempotency_key()` plus deploy/signal ledgers | Existing deterministic keying is tested and auditable. [VERIFIED: marketpilot/order_lifecycle.py] |
| Audit persistence | Mutable state table | Append-only JSONL records | Existing audit journal is append-only and secret-sanitizing. [VERIFIED: marketpilot/audit_journal.py] |
| Retry policy | Custom retry loops | Existing `QCApiClient` + `tenacity` | Existing API client already handles retryable QC errors. [VERIFIED: marketpilot/qc_api.py] |

**Key insight:** Phase 15 should connect existing boundaries, not replace them: runtime orchestration creates intent, QuantConnect executes and reports authority, and local JSONL records explain the chain. [VERIFIED: repo grep]

## Recommended Plan Decomposition

| Plan | Scope | Key Deliverables | Primary Tests |
|------|-------|------------------|---------------|
| 15-01 | QCApiClient endpoint corrections | Add `/live/commands/create`; add true `/live/orders/read`; update `/live/create` payload to official paper config; preserve safety allowlist. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/create-live-algorithm] | Extend `tests/test_qc_api.py` for payload shape, endpoint allowlist, credential redaction, no direct URLs. |
| 15-02 | Deploy idempotency and paper control | New deploy request/ledger model; reject duplicate deploy keys; append audit events for deploy requested/rejected/succeeded/failed; keep stop/liquidate paper gated. [VERIFIED: marketpilot/order_lifecycle.py] | New `tests/test_paper_order_flow.py` using tmp_path JSONL and mocked `QCApiClient`. |
| 15-03 | Signal command sender with stale-window guard | Convert `OrderIntent` to command payload; enforce latest sync/reconciliation, `PAPER_TRADING_ONLY`, UTC expiry, duplicate signal id, and stale skip audit. [VERIFIED: marketpilot/runtime_orchestrator.py] | Tests for fresh send, stale skip, duplicate skip, QC API error audit, no network. |
| 15-04 | LEAN command and order-event receiver | Add `on_command` validation, supported long-only US equity guard, order tag, local in-algorithm duplicate guard, and `on_order_event` status logging/evidence. [CITED: https://www.quantconnect.com/docs/v2/writing-algorithms/live-trading/commands] | Fake-data tests around helper functions; static tests forbidding real brokerage/imported secrets/dashboard controls. |
| 15-05 | Fill poller and audit trace | Poll `/live/orders/read`; parse status/fill/rejection fields defensively; map tag/idempotency to audit records; support partial fills and rejections. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/read-live-algorithm/orders] | Fixture-based parser tests for filled/partially filled/rejected/unknown status and full trace chain query. |

## Concrete Constraints

- Add no new package unless the planner explicitly proves an existing dependency cannot satisfy the need. [VERIFIED: pyproject.toml]
- Do not touch `.planning/research/.cache/`, `data/`, or `lean.json` during planning/research execution. [VERIFIED: user request]
- Any new local JSONL path must be configurable and tests must use `tmp_path`; tests must not write shared `data/` artifacts. [VERIFIED: tests/test_sync.py]
- `QCApiClient.read_live_orders()` currently calls `live/read`; Phase 15 must change or replace it to call official `/live/orders/read` for FT-01. [VERIFIED: marketpilot/qc_api.py] [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/read-live-algorithm/orders]
- Existing `create_live_algorithm()` currently omits official `versionId` and `dataProviders` fields; Phase 15 must update the wrapper before relying on PTD-01. [VERIFIED: marketpilot/qc_api.py] [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/create-live-algorithm]
- Because QuantConnect docs say live order/portfolio snapshots update about every 10 minutes, tests and UX must not assume immediate API-visible fills. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/read-live-algorithm/orders]
- The QuantConnect Paper Trading brokerage supports cash and margin accounts, but this project must force cash/long-only/no margin behavior. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/live-trading/brokerages/quantconnect-paper-trading] [VERIFIED: AGENTS.md]

## Common Pitfalls

### Pitfall 1: Command Success Treated as Fill Success

**What goes wrong:** The sender records a submitted/fill state immediately after `/live/commands/create` returns success. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/live-commands/create-live-command]

**Why it happens:** The command API response is a `RestResponse`, not an order/fill response. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/live-commands/create-live-command]

**How to avoid:** Record `command_accepted_by_qc_api`, then wait for `on_order_event` or `/live/orders/read` evidence before recording submitted/partial/filled/rejected lifecycle states. [CITED: https://www.quantconnect.com/docs/v2/writing-algorithms/trading-and-orders/order-events]

**Warning signs:** Audit entries contain fill price, QC order id, or rejection reason before any QC order data was observed. [VERIFIED: marketpilot/audit_journal.py]

### Pitfall 2: Stale Signals Sent After the Intended Execution Window

**What goes wrong:** A signal from a completed bar is delivered after the configured valid window and executes at an unintended later price. [VERIFIED: .planning/PROJECT.md]

**Why it happens:** Scheduler/API retries can outlive the signal's validity window. [ASSUMED]

**How to avoid:** Store `signal_time_utc`, `eligible_after_utc`, and `expires_at_utc`; enforce the window before API call and again inside `on_command`. [VERIFIED: .planning/REQUIREMENTS.md]

**Warning signs:** Command payload lacks expiry fields or stale-skip audit records. [VERIFIED: .planning/REQUIREMENTS.md]

### Pitfall 3: Duplicate Deploy or Signal on Retry

**What goes wrong:** A network retry or manual rerun deploys another live algorithm or sends the same signal twice. [ASSUMED]

**Why it happens:** `/live/create` and `/live/commands/create` do not provide project-specific idempotency keys in the documented request models. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/create-live-algorithm] [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/live-commands/create-live-command]

**How to avoid:** Persist local idempotency ledger entries before mutation endpoints and reject duplicates fail-closed. [VERIFIED: marketpilot/order_lifecycle.py]

**Warning signs:** Multiple audit entries share signal id/idempotency key with different QC command attempts marked executable. [VERIFIED: marketpilot/audit_journal.py]

### Pitfall 4: Partial Fill Collapsed to Filled

**What goes wrong:** The local mirror records a partial fill as complete and skips remaining quantity tracking. [CITED: https://www.quantconnect.com/docs/v2/writing-algorithms/trading-and-orders/order-events]

**Why it happens:** Parsers only check for "filled" and ignore intermediate order states. [VERIFIED: marketpilot/qc_api.py]

**How to avoid:** Preserve all observed status values and map partial fills to `OrderLifecycleState.PARTIALLY_FILLED`. [VERIFIED: marketpilot/order_lifecycle.py]

**Warning signs:** Audit payload lacks `filled_quantity`, `remaining_quantity`, or raw QC status for nonterminal states. [VERIFIED: marketpilot/order_lifecycle.py]

### Pitfall 5: Live-Paper Terminology Confusion

**What goes wrong:** Developers interpret QuantConnect "live algorithm" docs as permission to add real-money paths. [ASSUMED]

**Why it happens:** QuantConnect uses live deployment terminology for real-time paper algorithms as well as real broker deployments. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/live-trading/brokerages/quantconnect-paper-trading]

**How to avoid:** Keep every mutation endpoint paper-gated and require `QuantConnectBrokerage` with `environment: live-paper` for deployment payloads. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/create-live-algorithm]

**Warning signs:** Any config key accepts Alpaca, Interactive Brokers, live account credentials, margin, leverage, or non-US-equity asset classes. [VERIFIED: AGENTS.md]

## Code Examples

Verified patterns from official sources and local code:

### Create Live Command Wrapper

```python
# Source: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/live-commands/create-live-command
_PAPER_GATED_ENDPOINTS = frozenset({
    "live/create",
    "live/update/stop",
    "live/update/liquidate",
    "live/commands/create",
})

def create_live_command(self, *, project_id: int, command: Mapping[str, object]) -> bool:
    response = self._make_request(
        "live/commands/create",
        {"projectId": project_id, "command": dict(command)},
    )
    return bool(response.get("success", False))
```

### Read Live Orders Wrapper

```python
# Source: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/read-live-algorithm/orders
def read_live_orders_page(
    self,
    *,
    project_id: int,
    deploy_id: str,
    start: int = 0,
    end: int = 100,
) -> dict:
    return self._make_request(
        "live/orders/read",
        {
            "algorithmId": deploy_id,
            "start": start,
            "end": end,
            "projectId": project_id,
        },
    )
```

### LEAN Receiver Shape

```python
# Source: https://www.quantconnect.com/docs/v2/writing-algorithms/live-trading/commands
def on_command(self, data):
    payload = normalize_marketpilot_command(data)
    decision = validate_signal_command(payload, now_utc=self.time)
    if not decision.accepted:
        self.debug(f"MARKETPILOT_COMMAND_SKIPPED {decision.reason}")
        return False
    tag = f"mp:{payload.signal_id}:{payload.idempotency_key}"
    self.market_order(payload.symbol, payload.quantity, tag=tag)
    return True
```

### Order Event Shape

```python
# Source: https://www.quantconnect.com/docs/v2/writing-algorithms/trading-and-orders/order-events
def on_order_event(self, order_event):
    order = self.transactions.get_order_by_id(order_event.order_id)
    self.debug(
        "MARKETPILOT_ORDER_EVENT "
        f"order_id={order_event.order_id} status={order_event.status} tag={getattr(order, 'tag', '')}"
    )
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Redeploy algorithm to pass new signals | Send Commands API payload to a running live algorithm | Current QuantConnect docs as checked 2026-06-16 | Phase 15 can deliver signals without redeployment. [CITED: https://www.quantconnect.com/docs/v2/writing-algorithms/live-trading/commands] |
| Local fill inference | Poll QC live orders and process LEAN order events | Existing project safety plus official QC docs | Audit mirror can be queryable while QC remains authoritative. [VERIFIED: AGENTS.md] |
| Operator-only deployment metadata from Phase 8 | API-backed deployment with idempotency and paper config | Phase 15 scope | PTD-01 can become executable only after wrapper payload is corrected. [VERIFIED: marketpilot/quantconnect_paper.py] |

**Deprecated/outdated:**

- Treating `read_live_orders()` as FT-01 complete is outdated because the existing method reads `live/read`, not official `/live/orders/read`. [VERIFIED: marketpilot/qc_api.py]
- Treating `lean/main.py` as execution-ready is outdated because it lacks `on_command`, `on_order_event`, and any command-to-order translation. [VERIFIED: lean/main.py]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Scheduler/API retries can outlive a signal's valid window. | Common Pitfalls | Stale-window implementation may be overbuilt, but it is still required by SAFE-05. |
| A2 | Duplicate deploy/signal attempts can happen during network retries or manual reruns. | Common Pitfalls | Idempotency ledger could be more conservative than needed, but duplicate prevention is a success criterion. |
| A3 | QuantConnect terminology can confuse live-paper and real-money paths for developers. | Common Pitfalls | Documentation emphasis may be excessive, but safety constraints justify it. |

## Open Questions (RESOLVED AS EXECUTION GATES)

These questions are not left as planner ambiguity. They are resolved as Phase 15
execution and acceptance gates:

- Exact `/live/orders/read` response fields for tags, rejection reasons, and
  partial fill quantities must be captured as sanitized fixtures or manually
  recorded during the credentialed QuantConnect paper smoke check before FT-01,
  FT-03, and FT-04 can be marked externally verified.
- `/live/create` account-specific brokerage/data-provider payload must be
  implemented from the currently documented request shape and verified with
  operator-provided credentials before PTD-01 can be marked externally verified.
- If the credentialed smoke check cannot be run, Phase 15 may record offline
  implementation as passed, but the running-QuantConnect delivery goal remains
  `blocked_external_not_verified`; `not_run` is not acceptable proof of PTD-01
  or PTD-02.

1. **Exact live-orders response shape for tags and rejection messages**
   - What we know: `/live/orders/read` exists and returns live algorithm orders within a requested range. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/read-live-algorithm/orders]
   - What's unclear: The public docs do not fully expose every nested field needed for order tag, rejection reason, fill quantity, and partial fill parsing. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/read-live-algorithm/orders]
   - Recommendation: Planner should include a fixture-first parser and one manual credentialed verification checkpoint before marking FT-01/FT-03 complete.

2. **Whether `/live/create` requires additional brokerage/data-provider fields for this account**
   - What we know: Official docs require `versionId`, `projectId`, `compileId`, `nodeId`, `brokerage`, and at least one `dataProviders` entry. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/create-live-algorithm]
   - What's unclear: Account-specific organization/node/data-provider setup cannot be verified without user-managed QuantConnect credentials. [VERIFIED: AGENTS.md]
   - Recommendation: Planner should add a manual operator verification checkpoint using secrets outside chat.

3. **How much immediate order-event evidence can be recovered externally**
   - What we know: LEAN receives `on_order_event` events in the algorithm. [CITED: https://www.quantconnect.com/docs/v2/writing-algorithms/trading-and-orders/order-events]
   - What's unclear: Whether this phase should export order-event evidence through logs, Object Store, or only rely on `/live/orders/read` polling. [ASSUMED]
   - Recommendation: Use `/live/orders/read` as the required external source and keep any log/Object Store evidence optional until official execution verification.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| Python | Local tests and implementation | Yes | 3.10.10 | Project requires `>=3.11`; strict validation should use Python 3.11+. [VERIFIED: pyproject.toml] |
| pytest | Unit tests | Yes | 7.3.1 | None needed. [VERIFIED: local shell] |
| git | Commit research artifact | Yes | 2.45.2.windows.1 | None needed. [VERIFIED: local shell] |
| gsd-tools | GSD init/commit workflow | Yes | gsd-sdk v1.42.3 | `research-plan` and `classify-confidence` seams were unavailable; use official docs and record this gap. [VERIFIED: local shell] |
| QuantConnect credentials | Real API verification | No secrets available in repo/chat | N/A | Offline mocks for tests; manual user-managed secret setup for live verification. [VERIFIED: AGENTS.md] |

**Missing dependencies with no fallback:**

- Real QuantConnect credentials and live paper node are required for credentialed API verification, but implementation tests must remain offline. [VERIFIED: AGENTS.md]

**Missing dependencies with fallback:**

- GSD `research-plan` and `classify-confidence` commands are unavailable in the installed CLI; official QuantConnect docs were verified directly with web search/browser and sources are cited. [VERIFIED: local shell]

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 7.3.1 installed locally. [VERIFIED: local shell] |
| Config file | `pyproject.toml` with `testpaths = ["tests"]` and `pythonpath = ["."]`. [VERIFIED: pyproject.toml] |
| Quick run command | `pytest tests/test_qc_api.py tests/test_paper_order_flow.py -q` |
| Full suite command | `pytest -q` |

### Phase Requirements -> Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| PTD-01 | Paper-only deploy payload and idempotency | unit | `pytest tests/test_paper_order_flow.py::test_deploy_payload_is_paper_only -q` | No - Wave 0 |
| PTD-02 | Commands API signal delivery | unit | `pytest tests/test_qc_api.py::test_create_live_command_payload -q` | No - Wave 0 |
| PTD-03 | Stop/liquidate remain paper-gated | unit | `pytest tests/test_qc_api.py::test_safety_gate_allows_paper_gated_when_constant_true -q` | Yes |
| PTD-04 | Duplicate deploy rejected | unit | `pytest tests/test_paper_order_flow.py::test_duplicate_deploy_key_is_rejected_before_api_call -q` | No - Wave 0 |
| PTD-05 | LEAN receives signal and places tagged order inside algorithm | unit/static | `pytest tests/test_lean_command_flow.py -q` | No - Wave 0 |
| FT-01 | Poll `/live/orders/read` and map to signal ids | unit | `pytest tests/test_paper_order_flow.py::test_live_orders_read_maps_tag_to_signal_id -q` | No - Wave 0 |
| FT-02 | Fill events append audit JSONL | unit | `pytest tests/test_paper_order_flow.py::test_fill_poll_appends_audit_record -q` | No - Wave 0 |
| FT-03 | Partial fills/rejections tracked with reasons | unit | `pytest tests/test_paper_order_flow.py::test_partial_and_rejected_orders_are_preserved -q` | No - Wave 0 |
| FT-04 | Full signal-order-fill trace queryable | unit | `pytest tests/test_paper_order_flow.py::test_trace_chain_returns_signal_order_fill_records -q` | No - Wave 0 |
| SAFE-05 | Stale signals skipped before API and inside LEAN | unit | `pytest tests/test_paper_order_flow.py::test_stale_signal_skips_without_api_call -q` | No - Wave 0 |

### Sampling Rate

- **Per task commit:** Run the relevant new test file plus `pytest tests/test_qc_api.py -q` when touching API wrappers. [VERIFIED: tests/test_qc_api.py]
- **Per wave merge:** Run `pytest tests/test_qc_api.py tests/test_sync.py tests/test_paper_order_flow.py tests/test_lean_command_flow.py -q`. [VERIFIED: tests/test_sync.py]
- **Phase gate:** Run `pytest -q` and record any Python-version caveat. [VERIFIED: pyproject.toml]

### Wave 0 Gaps

- [ ] `tests/test_paper_order_flow.py` - deploy idempotency, signal command sender, fill poller, stale skips, audit trace chain. [VERIFIED: current tests directory]
- [ ] `tests/test_lean_command_flow.py` - pure helper/static tests around `lean/main.py` command/order-event behavior. [VERIFIED: lean/main.py]
- [ ] Extend `tests/test_qc_api.py` - `/live/commands/create`, `/live/orders/read`, corrected `/live/create` payload, and safety allowlist. [VERIFIED: tests/test_qc_api.py]
- [ ] Add JSON fixtures under `tests/fixtures/qc_api/` for live command success/error and live order statuses. [VERIFIED: tests/fixtures/qc_api]

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | Yes | Existing HMAC API token auth in `QCApiClient`; never print/store credentials. [VERIFIED: marketpilot/qc_api.py] |
| V3 Session Management | No | No browser session changes in Phase 15. [VERIFIED: dashboard/data.py] |
| V4 Access Control | Yes | Paper-only endpoint allowlist plus no dashboard mutation controls. [VERIFIED: marketpilot/qc_api.py] |
| V5 Input Validation | Yes | Validate command payload schema, symbol, quantity, timestamps, expiry, and idempotency before API send and in LEAN. [VERIFIED: .planning/REQUIREMENTS.md] |
| V6 Cryptography | Yes | Use existing HMAC auth; do not implement custom crypto beyond existing API auth helper. [VERIFIED: marketpilot/qc_api.py] |
| V7 Error Handling and Logging | Yes | Redact credentials and append sanitized audit payloads. [VERIFIED: marketpilot/qc_api.py] [VERIFIED: marketpilot/audit_journal.py] |
| V8 Data Protection | Yes | Do not store secrets; audit JSONL can store paper-only order ids and signal ids, not tokens. [VERIFIED: AGENTS.md] |

### Known Threat Patterns for QuantConnect Paper Order Flow

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Duplicate command replay | Tampering | Deterministic idempotency keys and local+LEAN duplicate guards. [VERIFIED: marketpilot/order_lifecycle.py] |
| Stale signal execution | Tampering | UTC expiry fields and stale skip audit before API call and inside `on_command`. [VERIFIED: .planning/REQUIREMENTS.md] |
| Secret leakage in audit/logs | Information Disclosure | Existing credential redaction filter and audit payload sanitizer. [VERIFIED: marketpilot/qc_api.py] [VERIFIED: marketpilot/audit_journal.py] |
| Real-money path introduced via deployment payload | Elevation of Privilege | Hardcode `QuantConnectBrokerage` `live-paper`, reject any non-paper brokerage credentials/settings. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/create-live-algorithm] |
| Local mirror overrides QC state | Tampering | Treat JSONL as audit/display mirror only; require QC order polling for authoritative status. [VERIFIED: AGENTS.md] |
| Command payload injection | Tampering | Use strict command type and schema allowlist; reject unknown fields that affect order behavior. [VERIFIED: .planning/REQUIREMENTS.md] |

## Official-Doc Assumptions to Reverify During Execution

- Reverify `/live/commands/create` request/response immediately before implementing `create_live_command()`, because this is the core PTD-02 integration. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/live-commands/create-live-command]
- Reverify `/live/orders/read` pagination fields and actual response payload with fixtures/manual credentialed run before completing FT-01/FT-03. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/read-live-algorithm/orders]
- Reverify `/live/create` payload for QuantConnect Paper Trading account settings before deployment, especially `versionId`, `dataProviders`, and brokerage environment. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/create-live-algorithm]
- Reverify LEAN Python casing for `on_command`, command payload property casing, and `on_order_event` attributes in the target QC runtime. [CITED: https://www.quantconnect.com/docs/v2/writing-algorithms/live-trading/commands] [CITED: https://www.quantconnect.com/docs/v2/writing-algorithms/trading-and-orders/order-events]

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| QC live-orders response lacks order tags needed for mapping | FT-01/FT-04 mapping may be incomplete | Put signal id/idempotency key in LEAN order tag and require manual fixture capture before completion. [CITED: https://www.quantconnect.com/docs/v2/writing-algorithms/trading-and-orders/order-types/market-orders] |
| API snapshot latency delays fills | Dashboard/audit may lag real paper state | Record `observed_at_utc` and source snapshot timestamp; do not claim real-time fill visibility. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/read-live-algorithm/orders] |
| Local Python is below project requirement | Strict validation mismatch | Use Python 3.11+ for release/CI verification; local 3.10 may still run tests but should be called out. [VERIFIED: pyproject.toml] |
| Existing `create_live_algorithm()` payload is incomplete | PTD-01 may fail against real QC API | Fix wrapper payload in first plan before deployment orchestration. [VERIFIED: marketpilot/qc_api.py] |
| LEAN code accidentally duplicates strategy/risk logic | Divergence from runtime orchestrator | Keep LEAN receiver limited to command validation and order submission; upstream pipeline remains source of signal/risk intent. [VERIFIED: marketpilot/lean_bridge.py] |

## Sources

### Primary (HIGH confidence)

- QuantConnect Commands docs - `on_command`, command payload injection, API/CLI command delivery. [CITED: https://www.quantconnect.com/docs/v2/writing-algorithms/live-trading/commands]
- QuantConnect Create Live Command API - `/live/commands/create` request and `RestResponse`. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/live-commands/create-live-command]
- QuantConnect Read Live Orders API - `/live/orders/read`, `algorithmId`, `start`, `end`, `projectId`, and snapshot cadence statement. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/read-live-algorithm/orders]
- QuantConnect Create Live Algorithm API - required deployment fields and response fields. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/create-live-algorithm]
- QuantConnect Order Events docs - `on_order_event`, order state updates, partial fill example. [CITED: https://www.quantconnect.com/docs/v2/writing-algorithms/trading-and-orders/order-events]
- QuantConnect Market Orders docs - `market_order(..., tag=...)`, fill monitoring, partial fill caveats. [CITED: https://www.quantconnect.com/docs/v2/writing-algorithms/trading-and-orders/order-types/market-orders]
- Local repo files explicitly requested by user: planning docs, Phase 13/14 summaries, `marketpilot/qc_api.py`, `marketpilot/sync.py`, `marketpilot/runtime_orchestrator.py`, `marketpilot/order_lifecycle.py`, `marketpilot/audit_journal.py`, `marketpilot/quantconnect_paper.py`, `lean/main.py`, `dashboard/data.py`, `tests/test_qc_api.py`, and `tests/test_sync.py`. [VERIFIED: repo grep]

### Secondary (MEDIUM confidence)

- None used for implementation recommendations; external facts are from QuantConnect official docs or repo files. [VERIFIED: web search]

### Tertiary (LOW confidence)

- Assumptions A1-A3 in the Assumptions Log. [ASSUMED]

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH - no new packages; existing Python/project modules verified from `pyproject.toml` and repo files. [VERIFIED: pyproject.toml]
- Architecture: HIGH - follows existing repo boundaries and official QuantConnect command/order docs. [VERIFIED: repo grep] [CITED: https://www.quantconnect.com/docs/v2/writing-algorithms/live-trading/commands]
- Pitfalls: MEDIUM - core pitfalls are source-backed; retry/duplicate operational scenarios are conservative assumptions. [ASSUMED]
- External API exact payload parsing: MEDIUM - endpoint models are official, but real account response fixtures need credentialed verification. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/read-live-algorithm/orders]

**Research date:** 2026-06-16
**Valid until:** 2026-07-16 for repo patterns; reverify QuantConnect API docs immediately before Phase 15 execution.
