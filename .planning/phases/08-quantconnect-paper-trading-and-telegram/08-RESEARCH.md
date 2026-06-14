# Phase 08: QuantConnect Paper Trading and Telegram - Research

**Researched:** 2026-06-14
**Domain:** QuantConnect Cloud Paper Trading, LEAN CLI deployment, paper-state reconciliation, Telegram Bot API delivery
**Confidence:** MEDIUM - API-sensitive claims were checked against official QuantConnect, Telegram, and OWASP documentation; codebase integration claims were verified by local reads and grep.

## User Constraints (from CONTEXT.md)

Source for this section: copied from `.planning/phases/08-quantconnect-paper-trading-and-telegram/08-CONTEXT.md`. [VERIFIED: codebase grep]

### Locked Decisions

#### Paper Mode Gating

- **D-01:** Phase 8 will model three active stages: Shadow Mode, Limited Paper Mode, and Full Approved Paper Mode. The default remains not active for Paper.
- **D-02:** `validation_passed` alone is not enough to submit Paper orders. `approved_for_shadow` allows signal previews and Telegram previews without Paper orders, `approved_for_limited_paper` allows tightly capped Paper entries, and `approved_for_full_paper` allows the configured Phase 6 risk limits.
- **D-03:** Limited Paper Mode should be more conservative than Phase 6 default risk: start with 0.5% per-trade risk, maximum 3 open Paper positions, maximum 1 new Paper entry per trading day, and existing Phase 6 allocation, sector, reward/risk, stop, and target checks still enforced.
- **D-04:** Mode transitions are operator-visible and auditable. They require current activation-gate evidence and should record the prior state, requested state, decision reason, timestamp, and correlation ID.
- **D-05:** If validation evidence is stale, unavailable, fixture-only, not-run, or inconsistent with Phase 7 activation gates, Paper order eligibility fails closed to Shadow or unvalidated.

#### QuantConnect Deployment Boundary

- **D-06:** QuantConnect Cloud Paper Trading is the preferred deployment target for Phase 8. Planning should use official QuantConnect Cloud/LEAN CLI docs and avoid designing local live trading as the primary route.
- **D-07:** Deployment commands may be documented and wrapped as dry-run or operator-run steps, but tests must not invoke real `lean cloud live deploy`, start a Live Node, or require credentials.
- **D-08:** QuantConnect account, paid organization access if required, live trading node availability, project ID, API credentials, and data-provider settings are external prerequisites. Missing prerequisites must produce a typed `not_configured` or `not_run` state, not a fake deployment.
- **D-09:** If non-interactive deployment is later supported, all required CLI flags must come from approved secret/config stores. Interactive wizard behavior should remain documented for user-operated setup.
- **D-10:** The project must never introduce live-money brokerage configuration. The only allowed brokerage target for this phase is QuantConnect Paper Trading.

#### Reconciliation And Recovery

- **D-11:** QuantConnect remains authoritative for Paper cash, equity, holdings, orders, fills, deployment status, algorithm status, and Paper performance. Local records are an audit mirror and recovery context only.
- **D-12:** Reconciliation should compare QuantConnect live state to local order lifecycle/audit records. On mismatch, block new entries, preserve exit and protective recovery obligations, emit a high-severity system event, and require explicit recovery handling.
- **D-13:** QuantConnect order IDs and fill data become authoritative after submission. Local idempotency keys still prevent duplicate local intent generation before submission.
- **D-14:** Restart recovery should rebuild active position and order context from QuantConnect first, then attach local audit history. If QuantConnect is unavailable, the system must not pretend local state is complete authority.
- **D-15:** Protective-order recovery is safety-critical. If a filled Paper position lacks required stop/target/protective state, new entries are blocked and Telegram/system alerts may be emitted, but Telegram failure must not block the protective recovery logic.

#### Telegram Delivery

- **D-16:** Telegram delivery will use a transport boundary over the official Telegram Bot API `sendMessage` path, with real delivery guarded behind explicit enabled configuration and secrets. Existing `NotificationDomainEvent` remains the internal domain event contract.
- **D-17:** Bot token and chat ID must be provided only through approved secret stores such as QuantConnect secure parameters, GitHub Secrets, or local environment variables outside committed files. They must be redacted in payloads, logs, docs examples, tests, and discussion artifacts.
- **D-18:** Missing token, missing chat ID, disabled notifications, quota/rate limiting, network/API failure, and Telegram rejection produce typed delivery results. None of these may stop trading logic, order lifecycle, protective exits, or reconciliation.
- **D-19:** Deduplication uses stable event type + correlation ID keys, while rate limiting is conservative and local. Paid broadcast features are out of scope and should not be used.
- **D-20:** Telegram messages should be concise, sanitized, and include the paper-only warning where relevant. They may include symbol, setup, score, mode, activation state, order/fill state, stop/target context, regime state, and system health, but must not include secrets, credentials, or profitability guarantees.

#### Alert Coverage

- **D-21:** Phase 8 should cover configured BUY candidate, WATCH, Paper BUY, Paper SELL, submitted-order, partial-fill, full-fill, stop, target, partial-close, full-close, rejected-order, canceled-order, regime-change, system, error, start/restart, and daily-summary alerts.
- **D-22:** Regime alerts are emitted only on actual regime transitions, not on unchanged repeated states.
- **D-23:** Daily summaries should be modeled as a scheduled/end-of-day notification artifact with active Paper mode, new signals, entries, exits, open positions, rejected actions, and system warnings.
- **D-24:** Historical backtests remain real-Telegram-disabled by default. Backtest preview events from Phase 7 remain fake-collector-only unless a future operator explicitly requests a preview pathway outside normal backtest execution.

### the agent's Discretion

The user explicitly delegated Phase 8 discussion choices to the agent. The agent selected conservative safety-first defaults: Shadow first, Limited Paper with stricter caps, Cloud Paper as the primary QuantConnect route, no automatic deployment in tests, Telegram as non-authoritative, and official-doc verification before API-specific implementation.

### Deferred Ideas (OUT OF SCOPE)

- Render dashboard display of active Paper mode, reconciliation state, and Telegram health remains Phase 9.
- GitHub Actions automation for QuantConnect deployment/backtest workflows remains Phase 10 unless Phase 8 only documents prerequisites.
- Paid Telegram broadcast features are out of scope.
- Any migration to real-money brokerage remains prohibited and out of scope.

## Summary

Phase 8 should be implemented as a paper-mode activation and transport integration layer over existing Phase 6 and Phase 7 contracts, not as a new strategy engine. `ActivationApprovalState`, `ValidationGateDecision.paper_eligible`, `OrderIntent`, idempotency keys, restart recovery, and transport-neutral notification events already exist and should remain the core boundaries. [VERIFIED: codebase grep]

QuantConnect Cloud Paper Trading should be treated as live-mode infrastructure with fictional capital and simulated fills, while QuantConnect remains authoritative for live deployment status, portfolio state, orders, and runtime statistics. Missing QuantConnect account, API token, project id, live node, LEAN CLI, or data-provider setup must produce typed `not_configured` or `not_run` states, never fake deployments or fake paper data. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/live-trading/brokerages/quantconnect-paper-trading] [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/list-live-algorithms]

Telegram should be a delivery adapter over `NotificationDomainEvent` using `sendMessage`, with explicit disabled, missing-token, missing-chat-id, rate-limited, rejected, failed, and delivered outcomes. Telegram failure must not block order safety, exits, protective recovery, reconciliation, or mode gates. [CITED: https://core.telegram.org/bots/api] [VERIFIED: codebase grep]

**Primary recommendation:** Use a fail-closed `paper_mode` module, a QuantConnect state adapter that only mirrors official live state, and a Telegram delivery adapter that consumes existing notification-domain events without affecting trading control flow. [VERIFIED: codebase grep]

## Project Constraints (from AGENTS.md)

- Source code, identifiers, file names, configuration, tests, technical documentation, commit messages, and GSD artifacts must be written in English; user-facing chat communication is Hebrew. [VERIFIED: AGENTS.md]
- Current official QuantConnect APIs must be verified before use; do not invent QuantConnect APIs, LEAN classes, Cloud API endpoints, package behavior, or tutorial details. [VERIFIED: AGENTS.md]
- The product is simulated Paper Trading only; do not add real-broker code, real-money credentials, leverage, margin, short selling, options, futures, cryptocurrency trading, or hidden live-trading switches. [VERIFIED: AGENTS.md]
- QuantConnect is the source of truth for simulated cash, portfolio equity, holdings, open positions, orders, fills, Paper Trading state, algorithm status, and QuantConnect Backtest results. [VERIFIED: AGENTS.md]
- Telegram failures must remain independent from trading safety, and Telegram secrets must never appear in logs, docs, tests, reports, or chat. [VERIFIED: AGENTS.md]
- Deterministic tests must not require QuantConnect, Telegram, Render, broker credentials, internet, or real market access. [VERIFIED: AGENTS.md]
- No commits should be made unless explicitly requested by the user. [VERIFIED: AGENTS.md]

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| REG-04 | Telegram regime transition alerts are generated when enabled and duplicate unchanged-state alerts are suppressed. | Use transition-only regime events with existing `NotificationDeduplicator` keyed by event type and correlation ID. [VERIFIED: .planning/REQUIREMENTS.md] [VERIFIED: marketpilot/notification_events.py] |
| TEL-01 | Shadow Mode, Limited Paper Mode, and Full Approved Paper Mode are gated by validation state. | Existing approval states include all three target states, and `paper_eligible` only returns true for limited/full paper. [VERIFIED: marketpilot/validation.py] |
| TEL-02 | Paper Trading deployment, order reconciliation, restart recovery, and protective-order recovery are designed around QuantConnect as source of truth. | QuantConnect APIs expose live list/status, live portfolio state, orders, and live read statistics; local recovery already marks QuantConnect as winner on mismatch. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/list-live-algorithms] [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/read-live-algorithm/portfolio-state] [VERIFIED: marketpilot/recovery.py] |
| TEL-03 | Telegram sends configured signal, paper order/fill, exit, regime, system, error, start/restart, and daily-summary alerts. | Existing notification event taxonomy covers several lifecycle/recovery classes; Phase 8 should extend taxonomy for alert coverage before formatting. [VERIFIED: docs/notification_events.md] [VERIFIED: marketpilot/notification_events.py] |
| TEL-04 | Telegram duplicate suppression, rate limiting, quota handling, missing-token behavior, missing-chat-ID behavior, disabled-notification behavior, and delivery failure behavior are unit-tested. | Existing dedup/rate-limit classes provide local deterministic foundations; Telegram API responses expose success/failure JSON fields for delivery result mapping. [VERIFIED: marketpilot/notification_events.py] [CITED: https://core.telegram.org/bots/api] |
| TEL-05 | Telegram secrets are stored only in approved secret stores and never in repository files. | Existing safety validation treats token/chat-id-like keys as secret hints; Telegram token is part of the HTTPS bot URL and must be external. [VERIFIED: marketpilot/safety.py] [CITED: https://core.telegram.org/bots/api] |
| TEL-06 | Telegram delivery failure does not stop trading logic or protective exit logic. | Existing notification docs state dedup/rate limiting affect notification emission only, not risk/order/exit safety. [VERIFIED: docs/notification_events.md] |

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|--------------|----------------|-----------|
| Paper mode gating | Backend domain layer | QuantConnect adapter | Activation eligibility is local policy over validation evidence, while QuantConnect only receives orders after the gate passes. [VERIFIED: marketpilot/validation.py] |
| QuantConnect deployment prerequisite status | Backend integration layer | Operator CLI/docs | The adapter should report `not_configured` or `not_run`; operator-run `lean cloud live deploy` remains outside unit tests. [CITED: https://www.quantconnect.com/docs/v2/lean-cli/api-reference/lean-cloud-live-deploy] |
| Paper portfolio, orders, fills, live status | QuantConnect Cloud | Backend audit mirror | QuantConnect exposes live list, read, portfolio, and order APIs; local JSONL remains recovery/audit context only. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/list-live-algorithms] [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/read-live-algorithm/portfolio-state] |
| Restart and protective-order recovery | Backend recovery layer | QuantConnect Cloud | Recovery should rebuild from QuantConnect snapshots first, then attach local audit history and block new entries on mismatch. [VERIFIED: marketpilot/recovery.py] |
| Telegram delivery | Backend notification transport | Telegram Bot API | `NotificationDomainEvent` remains internal; Telegram `sendMessage` is outbound delivery only. [VERIFIED: marketpilot/notification_events.py] [CITED: https://core.telegram.org/bots/api] |
| Secrets | Secret store / environment | Backend config validation | Tokens, chat IDs, QuantConnect user IDs, and API tokens must not be stored in repo config or logs. [VERIFIED: marketpilot/safety.py] [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/authentication] |

## Standard Stack

### Core

| Library/Tool | Version | Purpose | Why Standard |
|--------------|---------|---------|--------------|
| Python standard library `urllib.request`, `json`, `hashlib`, `base64`, `time` | Python >=3.11 required by project | HTTPS adapters, JSON parsing, QuantConnect authentication hashing, Telegram requests | Avoids adding external dependencies for small API clients and keeps offline tests simple. [VERIFIED: pyproject.toml] [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/authentication] |
| Existing `PyYAML` | `>=6.0.2` in project metadata | Typed config loading remains consistent with current config patterns | Already used by project configuration loaders. [VERIFIED: pyproject.toml] [VERIFIED: marketpilot/configuration.py] |
| Existing `pytest` | Project asks `>=8.0`; local environment has 7.3.1 | Deterministic offline tests | Existing suite uses pytest; release-grade local env should match project metadata. [VERIFIED: pyproject.toml] [VERIFIED: shell pytest --version] |
| LEAN CLI | Not installed locally | Operator-run QuantConnect cloud deployment/status commands | Official LEAN CLI docs define the `lean cloud live deploy` flow; tests must not require it. [CITED: https://www.quantconnect.com/docs/v2/lean-cli/api-reference/lean-cloud-live-deploy] [VERIFIED: shell lean not found] |

### Supporting

| Library/Tool | Version | Purpose | When to Use |
|--------------|---------|---------|-------------|
| QuantConnect Cloud API v2 | Current official docs | Live deployment list/read, portfolio snapshot, order snapshot, authentication | Use only behind `not_configured`/`not_run` guards and never as fake fixture source. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/authentication] |
| Telegram Bot API | Current official docs | `sendMessage` delivery | Use only when notifications enabled and token/chat ID are externally configured. [CITED: https://core.telegram.org/bots/api] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Python stdlib HTTP | `requests` | `requests` is ergonomic but would add a dependency; stdlib is enough for a small JSON POST adapter. [ASSUMED] |
| Direct Telegram Bot API | QuantConnect deployment-wizard Telegram notifications | QuantConnect wizard can notify order events and insights, but project-specific alert taxonomy needs explicit domain-event formatting and delivery results. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/live-trading/notifications] [VERIFIED: marketpilot/notification_events.py] |

**Installation:** No new external packages are recommended for Phase 8. [VERIFIED: pyproject.toml]

## Package Legitimacy Audit

No new external package install is recommended for Phase 8; the implementation should use existing project dependencies and Python standard library HTTP/JSON utilities. [VERIFIED: pyproject.toml]

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| None added | N/A | N/A | N/A | N/A | N/A | No install needed |

**Packages removed due to [SLOP] verdict:** none.
**Packages flagged as suspicious [SUS]:** none.

## Architecture Patterns

### System Architecture Diagram

```text
Phase 7 validation evidence
  -> PaperModeGate
     -> unvalidated / shadow / limited_paper / full_paper
     -> if not eligible: no Paper order intent submission
     -> if eligible: Phase 6 risk + lifecycle pipeline
        -> QuantConnectPaperAdapter
           -> configured? no: not_configured
           -> operator/cloud run? no: not_run
           -> official QC state: live status + portfolio + orders + fills
              -> Reconciler
                 -> match: append audit mirror + emit info/system event
                 -> mismatch: block new entries + preserve exits + emit warning/error event
              -> ProtectiveRecovery
                 -> missing stop/target: block new entries + recover protective obligations
NotificationDomainEvent
  -> Deduplicator -> RateLimiter -> TelegramTransport
     -> disabled / missing_secret / rate_limited / delivered / rejected / failed
     -> never feeds back into risk, lifecycle, exits, or reconciliation
```

This diagram is a conceptual data-flow map, not a file plan. [VERIFIED: codebase grep]

### Recommended Project Structure

```text
marketpilot/
  paper_modes.py              # activation state, mode caps, transition audit contracts
  quantconnect_paper.py       # typed QC prerequisite/status/snapshot adapters
  reconciliation.py           # QC snapshot vs local audit/lifecycle comparison
  telegram.py                 # Telegram transport, delivery result enum, HTTP boundary
  notification_events.py      # extend event taxonomy and keep transport-neutral domain events
config/
  paper_trading.yaml          # paper_trading_only true, mode caps, no secrets
  notifications.yaml          # enabled flags and non-secret transport settings only
docs/
  paper_trading.md            # operator prerequisites, not_configured/not_run behavior
  telegram.md                 # setup, secret storage, delivery result semantics
tests/
  test_paper_modes.py
  test_quantconnect_paper_contract.py
  test_reconciliation.py
  test_protective_recovery.py
  test_telegram_transport.py
  test_telegram_alert_coverage.py
```

The suggested files follow existing `marketpilot/`, `config/`, `docs/`, and `tests/` patterns already present in the repo. [VERIFIED: codebase grep]

### Pattern 1: Fail-Closed Paper Activation

**What:** Gate order eligibility through `ActivationApprovalState` and stricter Limited Paper caps; `validation_passed` is not enough for Paper orders. [VERIFIED: marketpilot/validation.py] [VERIFIED: .planning/phases/08-quantconnect-paper-trading-and-telegram/08-CONTEXT.md]

**When to use:** Before any Paper order intent is allowed to reach a QuantConnect submission adapter. [VERIFIED: docs/activation_gates.md]

**Example:**

```python
# Source: marketpilot/validation.py
decision = evaluate_activation_gates(
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
assert decision.paper_eligible is True
```

### Pattern 2: Typed External Prerequisite Outcomes

**What:** Represent missing external setup as `not_configured` and skipped cloud actions as `not_run`; do not fabricate deployment, portfolio, or fill data. [VERIFIED: marketpilot/backtesting.py] [VERIFIED: docs/safety.md]

**When to use:** QuantConnect credentials, project id, live node, LEAN CLI, Telegram token, or chat ID are missing. [VERIFIED: .planning/phases/08-quantconnect-paper-trading-and-telegram/08-CONTEXT.md]

**Example:**

```python
# Source: marketpilot/backtesting.py pattern to mirror for Phase 8
event = record_quantconnect_not_run(
    reason="lean_cli_not_installed",
    command='lean cloud live deploy "<projectName>" --push --open',
)
assert event.status is BacktestRunStatus.NOT_RUN
```

### Pattern 3: QuantConnect-Wins Reconciliation

**What:** Compare QuantConnect snapshots against local audit/lifecycle records; if they differ, QuantConnect wins, local state is marked mismatched, new entries stop, and exits/protective recovery remain active. [VERIFIED: marketpilot/recovery.py]

**When to use:** On restart, scheduled reconciliation, live status polling, and any order/fill mismatch. [VERIFIED: .planning/phases/08-quantconnect-paper-trading-and-telegram/08-CONTEXT.md]

**Example:**

```python
# Source: marketpilot/recovery.py
decision = reconcile_restart_state(
    local_state={"cash": 100000, "holdings": {}},
    quantconnect_snapshot={"cash": 99800, "holdings": {"AAPL": 10}},
)
assert decision.quantconnect_wins is True
assert decision.local_state_marked_mismatched is True
```

### Pattern 4: Notification Transport Boundary

**What:** Domain events are sanitized, deduplicated, and rate-limited before transport; delivery result states never control trading logic. [VERIFIED: marketpilot/notification_events.py] [VERIFIED: docs/notification_events.md]

**When to use:** All Telegram delivery, including system incidents and daily summaries. [VERIFIED: .planning/phases/08-quantconnect-paper-trading-and-telegram/08-CONTEXT.md]

**Example:**

```python
# Source: marketpilot/notification_events.py
event = NotificationDomainEvent.create(
    "system",
    "restart-2026-06-14T07:00:00Z",
    {"telegram_token": "secret", "status": "restarted"},
)
assert event.payload["telegram_token"] == "[redacted]"
```

### Anti-Patterns to Avoid

- **Local portfolio authority:** Do not let JSONL, dashboard files, CSV, SQLite, or tests become active Paper portfolio truth. [VERIFIED: docs/safety.md]
- **Automatic deployment in tests:** Do not invoke `lean cloud live deploy`, start a live node, or require credentials in unit tests. [VERIFIED: .planning/phases/08-quantconnect-paper-trading-and-telegram/08-CONTEXT.md]
- **Telegram as safety control:** Do not block, approve, cancel, or recover orders based on Telegram delivery state. [VERIFIED: docs/notification_events.md]
- **Paid Telegram broadcast:** Do not use `allow_paid_broadcast`; it is optional and incurs Telegram Stars cost. [CITED: https://core.telegram.org/bots/api]
- **Manual QuantConnect IDE order drift:** The QuantConnect live results page supports manual trades; if manual trades appear in official state, reconciliation should detect mismatch and block new entries until recovered. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/live-trading/algorithm-control]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Paper portfolio truth | Local portfolio database | QuantConnect live portfolio, orders, and runtime APIs | Official endpoints expose portfolio, orders, and status snapshots; local state is only mirror/recovery context. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/read-live-algorithm/portfolio-state] |
| Deployment wizard replacement | Custom deployment workflow | Operator-run LEAN CLI and documented not-run/not-configured states | Official CLI already handles brokerage, data provider, node, notifications, restart, cash, and holdings prompts. [CITED: https://www.quantconnect.com/docs/v2/lean-cli/live-trading/brokerages/quantconnect-paper-trading] |
| Secret storage | Repo YAML with tokens/chat IDs | Environment variables, GitHub Secrets, QuantConnect secure parameters | Repo safety validator already rejects secret-like values. [VERIFIED: marketpilot/safety.py] |
| Telegram protocol | Custom chat protocol | Telegram Bot API `sendMessage` | Official API defines request URL, required fields, success result, and error envelope. [CITED: https://core.telegram.org/bots/api] |
| Dedup/rate-limit primitives | New transport-coupled logic | Existing `NotificationDeduplicator` and `NotificationRateLimiter` extended as needed | Keeps delivery behavior testable and non-authoritative. [VERIFIED: marketpilot/notification_events.py] |

**Key insight:** Phase 8 should adapt official external systems into typed local contracts; it should not replace QuantConnect state, validation gates, or Telegram protocol semantics with project-specific inventions. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/live-trading/brokerages/quantconnect-paper-trading] [CITED: https://core.telegram.org/bots/api]

## QuantConnect Paper Trading Guidance

- QuantConnect Paper Trading runs algorithms in live mode with real-time market data and fictional capital; paper orders use simulated fills rather than exchange routing. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/live-trading/brokerages/quantconnect-paper-trading]
- The Cloud deployment path requires an available live trading node for each live trading algorithm. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/live-trading/brokerages/quantconnect-paper-trading]
- QuantConnect deployment resources are tiered; the official deployment docs list Free tier live node quota as 0 and Quant Researcher as 2. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/live-trading/deployment]
- LEAN CLI cloud deployment should be documented as `lean cloud live deploy "<projectName>" --push --open` for operator use; tests must not run it. [CITED: https://www.quantconnect.com/docs/v2/lean-cli/live-trading/brokerages/quantconnect-paper-trading] [VERIFIED: .planning/phases/08-quantconnect-paper-trading-and-telegram/08-CONTEXT.md]
- Non-interactive `lean cloud live deploy` requires `--brokerage` and `--data-provider-live`; the official example uses `--brokerage "Paper Trading"` and `--data-provider-live QuantConnect`, plus `--node`, `--auto-restart`, notification flags, `--push`, and `--open`. [CITED: https://www.quantconnect.com/docs/v2/lean-cli/api-reference/lean-cloud-live-deploy]
- If required non-interactive options are omitted, LEAN CLI falls back to Lean config properties and aborts if they are not set. [CITED: https://www.quantconnect.com/docs/v2/lean-cli/api-reference/lean-cloud-live-deploy]
- The `/live/list` API supports optional `projectId` and `status` filters; documented status options include `Running`, `Stopped`, `RuntimeError`, and `Liquidated`. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/list-live-algorithms]
- The `/live/read` API returns live deployment details including deploy id, status, brokerage, security types, runtime statistics, project files, success, and errors. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/read-live-algorithm/live-algorithm-statistics]
- The `/live/portfolio/read` API reads live portfolio state and notes the snapshot updates about every 10 minutes; Phase 8 must treat this cadence as potentially stale for reconciliation/UI status. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/read-live-algorithm/portfolio-state]
- The `/live/orders/read` API reads orders by algorithm id, project id, start index, and end index, with documented range limit `end - start <= 1,000`. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/read-live-algorithm/orders]

## Telegram Guidance

- Telegram Bot API requests must use HTTPS to `https://api.telegram.org/bot<token>/METHOD_NAME`; the token is therefore secret-bearing URL material and must not be logged. [CITED: https://core.telegram.org/bots/api]
- Telegram API responses always contain Boolean `ok`; successful calls put the result in `result`, failed calls return `ok: false`, human-readable `description`, and an `error_code` whose contents are subject to change. [CITED: https://core.telegram.org/bots/api]
- `sendMessage` sends text messages, requires `chat_id` and `text`, constrains text to 1-4096 characters after entity parsing, and returns the sent Message on success. [CITED: https://core.telegram.org/bots/api]
- `disable_notification` and `protect_content` are optional message controls that can be exposed as non-secret config if desired. [CITED: https://core.telegram.org/bots/api]
- `allow_paid_broadcast` is optional and paid; Phase 8 should not use it because paid broadcast is explicitly out of scope. [CITED: https://core.telegram.org/bots/api] [VERIFIED: .planning/phases/08-quantconnect-paper-trading-and-telegram/08-CONTEXT.md]

## Common Pitfalls

### Pitfall 1: Treating `validation_passed` As Paper Approval

**What goes wrong:** A strategy with passed gates but no operator paper approval submits orders. [VERIFIED: docs/activation_gates.md]
**Why it happens:** `validation_passed` sounds positive but is not paper-eligible by project policy. [VERIFIED: docs/activation_gates.md]
**How to avoid:** Require `approved_for_limited_paper` or `approved_for_full_paper` before Paper order submission. [VERIFIED: marketpilot/validation.py]
**Warning signs:** Tests that assert `validation_passed.paper_eligible` or configs that skip explicit approval state. [VERIFIED: marketpilot/validation.py]

### Pitfall 2: Faking QuantConnect State When Credentials Are Missing

**What goes wrong:** Tests or docs create fake deployment ids, live statuses, fills, equity, or portfolio values. [VERIFIED: docs/safety.md]
**Why it happens:** Cloud access may be unavailable locally and implementers try to keep workflows green. [VERIFIED: .planning/STATE.md]
**How to avoid:** Emit typed `not_configured` or `not_run` records with exact missing prerequisite and command. [VERIFIED: marketpilot/backtesting.py]
**Warning signs:** JSON fixtures that look like real QuantConnect results without fixture labels. [VERIFIED: docs/safety.md]

### Pitfall 3: Reconciliation Loop Overwrites Safety Obligations

**What goes wrong:** A mismatch clears local stop/target obligations or lets new entries continue. [VERIFIED: .planning/phases/08-quantconnect-paper-trading-and-telegram/08-CONTEXT.md]
**Why it happens:** Local state is treated as equivalent to QuantConnect instead of audit mirror. [VERIFIED: marketpilot/recovery.py]
**How to avoid:** QuantConnect wins on holdings/orders/fills/cash, local state is marked mismatched, new entries are blocked, and protective exit obligations remain active. [VERIFIED: marketpilot/recovery.py] [VERIFIED: marketpilot/exits.py]
**Warning signs:** Reconciliation functions that return "resolved" without a mismatch event or new-entry block. [VERIFIED: marketpilot/recovery.py]

### Pitfall 4: Telegram Delivery Controls Trading Safety

**What goes wrong:** Failed alerts halt protective recovery or successful alerts approve risk/order transitions. [VERIFIED: docs/notification_events.md]
**Why it happens:** Notification code is coupled to domain logic instead of being an outbound transport. [VERIFIED: marketpilot/notification_events.py]
**How to avoid:** Delivery result states must be recorded independently and never used as gate inputs. [VERIFIED: docs/notification_events.md]
**Warning signs:** Order lifecycle tests that depend on a real Telegram response. [VERIFIED: AGENTS.md]

### Pitfall 5: Markdown Formatting Breaks Telegram Messages

**What goes wrong:** Scores, tickers, or punctuation are interpreted as invalid Markdown entities. [ASSUMED]
**Why it happens:** Telegram supports parse modes with entity parsing rules. [CITED: https://core.telegram.org/bots/api]
**How to avoid:** Send plain text by default or use explicit entity arrays only after tests cover escaping. [ASSUMED]
**Warning signs:** Telegram `ok: false` results for valid-looking business events. [CITED: https://core.telegram.org/bots/api]

## Code Examples

Verified patterns from local source and official docs:

### QuantConnect API Authentication Shape

```python
# Source: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/authentication
timestamp = str(int(time()))
hashed_token = sha256(f"{api_token}:{timestamp}".encode("utf-8")).hexdigest()
authentication = b64encode(f"{user_id}:{hashed_token}".encode("utf-8")).decode("ascii")
headers = {"Authorization": f"Basic {authentication}", "Timestamp": timestamp}
```

### Telegram Delivery Result Shape

```python
# Source: https://core.telegram.org/bots/api
payload = {"chat_id": chat_id, "text": message_text}
# POST JSON to https://api.telegram.org/bot<token>/sendMessage.
# Map ok/result to delivered; map ok false/error_code/description/parameters to rejected or rate_limited.
```

### Existing Deduplication Key

```python
# Source: marketpilot/notification_events.py
key = f"{event.event_type}|{event.correlation_id}"
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Treating local paper state as adequate for paper trading | QuantConnect is source of truth and local state is an audit mirror | Project decision active before Phase 8 | Planner must not create local portfolio authority. [VERIFIED: .planning/PROJECT.md] |
| `validation_passed` implies activation | Explicit `approved_for_shadow`, `approved_for_limited_paper`, or `approved_for_full_paper` states | Phase 7/8 context | Planner must require explicit approval transitions. [VERIFIED: docs/activation_gates.md] |
| Transport-specific notification strings | Transport-neutral `NotificationDomainEvent` plus adapter-specific delivery results | Phase 6 | Planner should extend event taxonomy before Telegram formatting. [VERIFIED: marketpilot/notification_events.py] |
| Manual or interactive deployment only | LEAN CLI supports non-interactive cloud live deploy if required options are supplied | Current official CLI docs | Planner may document non-interactive commands but tests must not execute them. [CITED: https://www.quantconnect.com/docs/v2/lean-cli/api-reference/lean-cloud-live-deploy] |

**Deprecated/outdated:**
- Treating Telegram or Render as authoritative state is prohibited by current project safety policy. [VERIFIED: docs/safety.md]
- Paid Telegram broadcast behavior is out of scope for this phase. [VERIFIED: .planning/phases/08-quantconnect-paper-trading-and-telegram/08-CONTEXT.md]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Python stdlib HTTP is sufficient and preferable to adding `requests`. | Standard Stack | Planner might need to revisit if timeout/retry ergonomics become too complex. |
| A2 | Plain text Telegram messages are safer than Markdown by default. | Common Pitfalls | Formatter may need entity escaping if rich formatting is later required. |

## Open Questions (RESOLVED)

1. **QuantConnect account and subscription readiness**
   - What we know: Free tier live node quota is documented as 0 and live nodes are required for deployments. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/live-trading/deployment]
   - What's unclear: The user's current QuantConnect organization tier, node availability, project id, API token, and live data settings are unknown. [VERIFIED: .planning/STATE.md]
   - Recommendation: Plan for `not_configured` until the operator configures QuantConnect outside the repo. [VERIFIED: .planning/phases/08-quantconnect-paper-trading-and-telegram/08-CONTEXT.md]
   - RESOLVED: Use `not_configured` and operator-run prerequisite documentation as the Phase 8 default. Do not block local deterministic planning or tests on QuantConnect credentials, project ID, live node, subscription tier, or data-provider settings. Plans must document required external setup and must never create fake deployment, live node, paper portfolio, order, or fill state.

2. **Telegram chat target**
   - What we know: `sendMessage` requires `chat_id` and `text`. [CITED: https://core.telegram.org/bots/api]
   - What's unclear: Bot token and chat ID are not available and must not be pasted into chat or committed. [VERIFIED: AGENTS.md]
   - Recommendation: Plan typed missing-token and missing-chat-id delivery results. [VERIFIED: .planning/phases/08-quantconnect-paper-trading-and-telegram/08-CONTEXT.md]
   - RESOLVED: Use typed `missing_token` and `missing_chat_id` delivery results, keep real Telegram disabled by default, and require token/chat ID only through external secret providers. Tests use fake or injected clients only and must not require network access or real Telegram credentials.

3. **Protective-order implementation detail in QuantConnect**
   - What we know: US Equity paper order types include market, limit, stop market, and stop limit in the DefaultBrokerageModel table. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/live-trading/brokerages/quantconnect-paper-trading]
   - What's unclear: Exact Phase 8 order submission/update/cancel code path should be verified against LEAN order-ticket docs during implementation. [ASSUMED]
   - Recommendation: Research/order-ticket verification should be a planner checkpoint before implementing actual submission methods. [ASSUMED]
   - RESOLVED: Phase 8 plans should implement typed contracts, reconciliation, and protective recovery around QuantConnect-authoritative order/fill snapshots first. Actual order-ticket submission/update/cancel code must remain guarded behind official-doc verification during execution, and no unit test may submit, update, cancel, or deploy real QuantConnect orders.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| Python | Local tests and tooling | Yes, but wrong major/minor for project metadata | 3.10.10 local; project requires >=3.11 | Use Python >=3.11 for release validation. [VERIFIED: shell python --version] [VERIFIED: pyproject.toml] |
| pytest | Deterministic offline tests | Yes, but lower than project dev metadata | 7.3.1 local; project asks >=8.0 | Use local for exploratory checks only; upgrade env for strict validation. [VERIFIED: shell pytest --version] [VERIFIED: pyproject.toml] |
| LEAN CLI | Operator-run cloud paper deployment/status | No | not found | Document commands and return `not_configured`/`not_run`; do not run in tests. [VERIFIED: shell lean not found] |
| QuantConnect account/API token/project/live node | Cloud paper deployment and reconciliation | Unknown | N/A | Typed `not_configured`; user-managed setup outside repo. [VERIFIED: .planning/STATE.md] |
| Telegram bot token/chat ID | Real Telegram delivery | Unknown | N/A | Typed missing-token/missing-chat-id; use fake collector in tests. [VERIFIED: .planning/STATE.md] |

**Missing dependencies with no fallback:**
- Real QuantConnect Paper deployment requires user-managed QuantConnect credentials and live node. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/live-trading/deployment]
- Real Telegram delivery requires bot token and chat ID stored outside repository files. [CITED: https://core.telegram.org/bots/api]

**Missing dependencies with fallback:**
- LEAN CLI absence has a documentation/not-run fallback for planning and tests. [VERIFIED: shell lean not found]
- Telegram real delivery has a fake collector fallback for deterministic tests. [VERIFIED: marketpilot/notification_events.py]

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest; local 7.3.1, project dev metadata >=8.0. [VERIFIED: shell pytest --version] [VERIFIED: pyproject.toml] |
| Config file | `pyproject.toml`. [VERIFIED: pyproject.toml] |
| Quick run command | `pytest tests/test_paper_modes.py tests/test_telegram_transport.py -q` [ASSUMED] |
| Full suite command | `pytest -q` [VERIFIED: pyproject.toml] |

### Phase Requirements -> Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| REG-04 | Regime transition alert emits only on changed state | unit | `pytest tests/test_telegram_alert_coverage.py -q` | No, Wave 0 gap. [VERIFIED: tests listing] |
| TEL-01 | Shadow/Limited/Full paper modes gate order eligibility | unit | `pytest tests/test_paper_modes.py -q` | No, Wave 0 gap. [VERIFIED: tests listing] |
| TEL-02 | QC reconciliation/restart/protective recovery block new entries on mismatch | unit | `pytest tests/test_reconciliation.py tests/test_protective_recovery.py -q` | No, Wave 0 gap. [VERIFIED: tests listing] |
| TEL-03 | Telegram alert coverage maps all required event families | unit | `pytest tests/test_telegram_alert_coverage.py -q` | No, Wave 0 gap. [VERIFIED: tests listing] |
| TEL-04 | Delivery result states, dedup, rate limiting, disabled/missing secret behavior | unit | `pytest tests/test_telegram_transport.py -q` | No, Wave 0 gap. [VERIFIED: tests listing] |
| TEL-05 | Secrets never stored/logged/rendered | unit/static | `pytest tests/test_telegram_transport.py tests/test_safety.py -q` | Partial existing safety tests. [VERIFIED: tests listing] |
| TEL-06 | Telegram failure does not stop safety/recovery logic | unit | `pytest tests/test_telegram_transport.py tests/test_protective_recovery.py -q` | No, Wave 0 gap. [VERIFIED: tests listing] |

### Sampling Rate

- **Per task commit:** targeted pytest file for changed module. [ASSUMED]
- **Per wave merge:** `pytest -q`. [VERIFIED: pyproject.toml]
- **Phase gate:** Full suite green in Python >=3.11, with external QuantConnect/Telegram checks recorded as not_configured/not_run if unavailable. [VERIFIED: pyproject.toml] [VERIFIED: docs/safety.md]

### Wave 0 Gaps

- [ ] `tests/test_paper_modes.py` - covers TEL-01. [VERIFIED: tests listing]
- [ ] `tests/test_quantconnect_paper_contract.py` - covers deployment status/not_configured/not_run parsing. [VERIFIED: tests listing]
- [ ] `tests/test_reconciliation.py` - covers TEL-02 restart and mismatch behavior. [VERIFIED: tests listing]
- [ ] `tests/test_protective_recovery.py` - covers TEL-02/TEL-06 protective-order recovery independence from Telegram. [VERIFIED: tests listing]
- [ ] `tests/test_telegram_transport.py` - covers TEL-04/TEL-05/TEL-06 delivery result states and secret redaction. [VERIFIED: tests listing]
- [ ] `tests/test_telegram_alert_coverage.py` - covers REG-04/TEL-03 event coverage and regime transition deduplication. [VERIFIED: tests listing]
- [ ] Local Python upgrade to >=3.11 for strict validation. [VERIFIED: shell python --version] [VERIFIED: pyproject.toml]

## Security Domain

Security enforcement is enabled in `.planning/config.json`. [VERIFIED: .planning/config.json]

### Applicable ASVS Categories

OWASP ASVS provides secure development and verification requirements, and the current stable version is 5.0.0. [CITED: https://owasp.org/www-project-application-security-verification-standard/]

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| Authentication / credential handling | yes | Store QuantConnect and Telegram credentials outside repo; hash QuantConnect API token per official auth docs; redact token/chat-id-like keys. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/authentication] [VERIFIED: marketpilot/safety.py] |
| Session Management | no | No browser session feature in Phase 8; dashboard auth remains Phase 9. [VERIFIED: .planning/phases/08-quantconnect-paper-trading-and-telegram/08-CONTEXT.md] |
| Access Control | yes | Paper order eligibility must require explicit activation state and must fail closed on stale/unavailable validation evidence. [VERIFIED: docs/activation_gates.md] |
| Input Validation | yes | Validate external API response shape, status enums, `ok` booleans, required ids, and no-secret configs before use. [CITED: https://core.telegram.org/bots/api] [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/list-live-algorithms] |
| Cryptography | yes | Use official QuantConnect timestamped SHA-256 token hash; do not invent secret transforms. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/authentication] |
| Logging and Error Handling | yes | Log typed sanitized result states only; never log Telegram bot token, chat ID, QuantConnect API token, Authorization header, or raw secret-bearing URL. [VERIFIED: marketpilot/safety.py] |

### Known Threat Patterns for This Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Secret leakage through config/logs/tests | Information Disclosure | Reject secret-like repo config, redact payload keys, and use external secret stores. [VERIFIED: marketpilot/safety.py] |
| Forged local activation state | Elevation of Privilege | Require current activation gate evidence and explicit paper approval states. [VERIFIED: docs/activation_gates.md] |
| Duplicate order submission after restart | Tampering | Keep local idempotency key before submission and reconcile authoritative QC order/fill IDs after submission. [VERIFIED: marketpilot/order_lifecycle.py] |
| Stale QuantConnect snapshot mistaken as current | Tampering | Record snapshot timestamp/cadence and block or warn when reconciliation input is stale. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/read-live-algorithm/portfolio-state] |
| Telegram API rejection hidden as success | Repudiation | Parse `ok`, `description`, `error_code`, and optional parameters into typed delivery results. [CITED: https://core.telegram.org/bots/api] |
| Rate-limit burst during incident | Denial of Service | Use local conservative rate limiting and typed `rate_limited` delivery result; do not use paid broadcast. [VERIFIED: marketpilot/notification_events.py] [CITED: https://core.telegram.org/bots/api] |

## Sources

### Primary (MEDIUM confidence, official docs)

- https://www.quantconnect.com/docs/v2/cloud-platform/live-trading/brokerages/quantconnect-paper-trading - Paper brokerage behavior, fills, order types, live node requirement.
- https://www.quantconnect.com/docs/v2/lean-cli/live-trading/brokerages/quantconnect-paper-trading - LEAN CLI Paper Trading wizard and cloud deployment flow.
- https://www.quantconnect.com/docs/v2/lean-cli/api-reference/lean-cloud-live-deploy - Non-interactive deployment requirements and options.
- https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/list-live-algorithms - Live deployment listing/status API.
- https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/read-live-algorithm/portfolio-state - Live portfolio snapshot API and update cadence.
- https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/read-live-algorithm/orders - Live orders API.
- https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/read-live-algorithm/live-algorithm-statistics - Live algorithm read/status API.
- https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/authentication - API v2 authentication.
- https://www.quantconnect.com/docs/v2/cloud-platform/live-trading/notifications - QuantConnect notification wizard and notification scope.
- https://core.telegram.org/bots/api - Telegram Bot API request/response and `sendMessage`.
- https://owasp.org/www-project-application-security-verification-standard/ - ASVS purpose and stable version.

### Primary (local verified)

- `.planning/PROJECT.md`, `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`, `.planning/STATE.md`, `AGENTS.md`, and Phase 6/7/8 contexts. [VERIFIED: codebase grep]
- `docs/safety.md`, `docs/activation_gates.md`, `docs/notification_events.md`. [VERIFIED: codebase grep]
- `marketpilot/validation.py`, `marketpilot/backtesting.py`, `marketpilot/order_lifecycle.py`, `marketpilot/recovery.py`, `marketpilot/notification_events.py`, `marketpilot/safety.py`, `marketpilot/configuration.py`, `marketpilot/exits.py`. [VERIFIED: codebase grep]

### Tertiary (LOW confidence)

- Assumptions A1-A2 are marked for planner confirmation if implementation complexity changes. [ASSUMED]

## Metadata

**Confidence breakdown:**
- Standard stack: MEDIUM - no new package recommendation; local environment mismatch verified. [VERIFIED: shell] [VERIFIED: pyproject.toml]
- Architecture: MEDIUM - based on existing code contracts and official API docs. [VERIFIED: codebase grep] [CITED: QuantConnect/Telegram docs]
- Pitfalls: MEDIUM - safety and API failure modes are supported by local docs and official response/deployment semantics. [VERIFIED: docs/safety.md] [CITED: https://core.telegram.org/bots/api]

**Research date:** 2026-06-14
**Valid until:** 2026-06-21 for QuantConnect/Telegram API details; 2026-07-14 for local architecture guidance.
