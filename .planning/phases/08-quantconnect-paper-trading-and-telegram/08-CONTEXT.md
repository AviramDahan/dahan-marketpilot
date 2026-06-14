# Phase 8: QuantConnect Paper Trading and Telegram - Context

**Gathered:** 2026-06-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 8 enables gated QuantConnect Cloud Paper Trading modes and real Telegram
delivery after Phase 7 validation gates. It may create Paper-mode contracts,
deployment prerequisites, QuantConnect reconciliation/recovery adapters,
Telegram transport/configuration, alert formatting, delivery-result tracking,
deduplication/rate-limiting behavior, tests, and documentation.

Phase 8 must not add real-money broker support, bypass validation gates, store
secrets in the repository, make Telegram delivery authoritative, treat local
state as the Paper portfolio source of truth, or automatically deploy live
algorithms without explicit user-managed QuantConnect credentials and
operator-controlled commands.

</domain>

<decisions>
## Implementation Decisions

### Paper Mode Gating

- **D-01:** Phase 8 will model three active stages: Shadow Mode, Limited Paper
  Mode, and Full Approved Paper Mode. The default remains not active for Paper.
- **D-02:** `validation_passed` alone is not enough to submit Paper orders.
  `approved_for_shadow` allows signal previews and Telegram previews without
  Paper orders, `approved_for_limited_paper` allows tightly capped Paper
  entries, and `approved_for_full_paper` allows the configured Phase 6 risk
  limits.
- **D-03:** Limited Paper Mode should be more conservative than Phase 6 default
  risk: start with 0.5% per-trade risk, maximum 3 open Paper positions, maximum
  1 new Paper entry per trading day, and existing Phase 6 allocation, sector,
  reward/risk, stop, and target checks still enforced.
- **D-04:** Mode transitions are operator-visible and auditable. They require
  current activation-gate evidence and should record the prior state, requested
  state, decision reason, timestamp, and correlation ID.
- **D-05:** If validation evidence is stale, unavailable, fixture-only,
  not-run, or inconsistent with Phase 7 activation gates, Paper order
  eligibility fails closed to Shadow or unvalidated.

### QuantConnect Deployment Boundary

- **D-06:** QuantConnect Cloud Paper Trading is the preferred deployment target
  for Phase 8. Planning should use official QuantConnect Cloud/LEAN CLI docs and
  avoid designing local live trading as the primary route.
- **D-07:** Deployment commands may be documented and wrapped as dry-run or
  operator-run steps, but tests must not invoke real `lean cloud live deploy`,
  start a Live Node, or require credentials.
- **D-08:** QuantConnect account, paid organization access if required, live
  trading node availability, project ID, API credentials, and data-provider
  settings are external prerequisites. Missing prerequisites must produce a
  typed `not_configured` or `not_run` state, not a fake deployment.
- **D-09:** If non-interactive deployment is later supported, all required CLI
  flags must come from approved secret/config stores. Interactive wizard
  behavior should remain documented for user-operated setup.
- **D-10:** The project must never introduce live-money brokerage configuration.
  The only allowed brokerage target for this phase is QuantConnect Paper
  Trading.

### Reconciliation And Recovery

- **D-11:** QuantConnect remains authoritative for Paper cash, equity,
  holdings, orders, fills, deployment status, algorithm status, and Paper
  performance. Local records are an audit mirror and recovery context only.
- **D-12:** Reconciliation should compare QuantConnect live state to local
  order lifecycle/audit records. On mismatch, block new entries, preserve exit
  and protective recovery obligations, emit a high-severity system event, and
  require explicit recovery handling.
- **D-13:** QuantConnect order IDs and fill data become authoritative after
  submission. Local idempotency keys still prevent duplicate local intent
  generation before submission.
- **D-14:** Restart recovery should rebuild active position and order context
  from QuantConnect first, then attach local audit history. If QuantConnect is
  unavailable, the system must not pretend local state is complete authority.
- **D-15:** Protective-order recovery is safety-critical. If a filled Paper
  position lacks required stop/target/protective state, new entries are blocked
  and Telegram/system alerts may be emitted, but Telegram failure must not block
  the protective recovery logic.

### Telegram Delivery

- **D-16:** Telegram delivery will use a transport boundary over the official
  Telegram Bot API `sendMessage` path, with real delivery guarded behind
  explicit enabled configuration and secrets. Existing `NotificationDomainEvent`
  remains the internal domain event contract.
- **D-17:** Bot token and chat ID must be provided only through approved secret
  stores such as QuantConnect secure parameters, GitHub Secrets, or local
  environment variables outside committed files. They must be redacted in
  payloads, logs, docs examples, tests, and discussion artifacts.
- **D-18:** Missing token, missing chat ID, disabled notifications, quota/rate
  limiting, network/API failure, and Telegram rejection produce typed delivery
  results. None of these may stop trading logic, order lifecycle, protective
  exits, or reconciliation.
- **D-19:** Deduplication uses stable event type + correlation ID keys, while
  rate limiting is conservative and local. Paid broadcast features are out of
  scope and should not be used.
- **D-20:** Telegram messages should be concise, sanitized, and include the
  paper-only warning where relevant. They may include symbol, setup, score,
  mode, activation state, order/fill state, stop/target context, regime state,
  and system health, but must not include secrets, credentials, or profitability
  guarantees.

### Alert Coverage

- **D-21:** Phase 8 should cover configured BUY candidate, WATCH, Paper BUY,
  Paper SELL, submitted-order, partial-fill, full-fill, stop, target,
  partial-close, full-close, rejected-order, canceled-order, regime-change,
  system, error, start/restart, and daily-summary alerts.
- **D-22:** Regime alerts are emitted only on actual regime transitions, not on
  unchanged repeated states.
- **D-23:** Daily summaries should be modeled as a scheduled/end-of-day
  notification artifact with active Paper mode, new signals, entries, exits,
  open positions, rejected actions, and system warnings.
- **D-24:** Historical backtests remain real-Telegram-disabled by default.
  Backtest preview events from Phase 7 remain fake-collector-only unless a
  future operator explicitly requests a preview pathway outside normal backtest
  execution.

### The Agent's Discretion

The user explicitly delegated Phase 8 discussion choices to the agent. The
agent selected conservative safety-first defaults: Shadow first, Limited Paper
with stricter caps, Cloud Paper as the primary QuantConnect route, no automatic
deployment in tests, Telegram as non-authoritative, and official-doc
verification before API-specific implementation.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Scope And Safety

- `.planning/PROJECT.md` - Paper-only product scope, QuantConnect source of
  truth, Telegram non-authority, and external actions required later.
- `.planning/REQUIREMENTS.md` - Requirement IDs `REG-04`, `TEL-01` through
  `TEL-06`, and related QuantConnect architecture requirements.
- `.planning/ROADMAP.md` - Phase 8 goal, success criteria, and four planned
  plan areas.
- `.planning/STATE.md` - Current post-Phase-7 state and known blockers.
- `docs/Dahan-MarketPilot-Master-Spec.md` - Product-level Paper Trading,
  staged activation, Telegram alert coverage, notification safety, and
  operations expectations.
- `docs/safety.md` - Paper-only guardrails, QuantConnect authority, Telegram
  non-authority, and no-secret policy.
- `docs/activation_gates.md` - Activation states and Paper eligibility
  requirements.

### Inputs From Prior Phases

- `.planning/phases/06-portfolio-risk-and-order-lifecycle/06-CONTEXT.md` -
  Risk, order lifecycle, exits, audit mirror, restart recovery, and
  notification-domain decisions.
- `.planning/phases/06-portfolio-risk-and-order-lifecycle/06-VERIFICATION.md` -
  Verification that Phase 6 risk/lifecycle/exit/notification contracts pass.
- `.planning/phases/07-backtesting-and-validation/07-CONTEXT.md` - Validation
  gates, not-run behavior, report safety, and preview-notification decisions.
- `.planning/phases/07-backtesting-and-validation/07-VERIFICATION.md` -
  Verification that activation gates and backtesting/report contracts pass.

### Existing Code Contracts

- `marketpilot/validation.py` - `ActivationApprovalState` and
  `ValidationGateDecision`.
- `marketpilot/backtesting.py` - Backtest run status and not-run behavior.
- `marketpilot/backtest_reports.py` - Artifact source labels and report
  completeness contracts.
- `marketpilot/risk.py` - Position sizing and portfolio risk boundaries.
- `marketpilot/order_lifecycle.py` - Order intent, lifecycle states,
  idempotency keys, and transition audit events.
- `marketpilot/exits.py` - Stop, target, partial close, full close, and holding
  period obligations.
- `marketpilot/recovery.py` - Restart mismatch and QuantConnect-wins recovery
  contracts.
- `marketpilot/audit_journal.py` - Append-only audit mirror.
- `marketpilot/notification_events.py` - Transport-neutral notification events,
  fake collector, deduplication, and rate limiting.
- `docs/notification_events.md` - Current notification event boundary.

### Official External References

- `https://www.quantconnect.com/docs/v2/cloud-platform/live-trading/brokerages/quantconnect-paper-trading` - QuantConnect Cloud Paper Trading deployment flow.
- `https://www.quantconnect.com/docs/v2/lean-cli/live-trading/brokerages/quantconnect-paper-trading` - LEAN CLI Paper Trading brokerage flow and cloud deployment command.
- `https://www.quantconnect.com/docs/v2/lean-cli/api-reference/lean-cloud-live-deploy` - `lean cloud live deploy` behavior, wizard/non-interactive constraints, and required options.
- `https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/list-live-algorithms` - QuantConnect live deployment listing/status API reference.
- `https://core.telegram.org/bots/api` - Telegram Bot API, including `sendMessage`, `chat_id`, silent/protected message options, and paid broadcast field that is out of scope.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets

- `ActivationApprovalState` already defines `approved_for_shadow`,
  `approved_for_limited_paper`, and `approved_for_full_paper`.
- `ValidationGateDecision.paper_eligible` already distinguishes Paper-eligible
  approval states from validation-only states.
- `OrderIntent` and `make_order_idempotency_key()` can prevent duplicate local
  order intents before QuantConnect order IDs exist.
- `OrderLifecycleEvent` can record Paper order state transitions once
  QuantConnect state is reconciled.
- `ExitPlan` and exit obligation helpers can drive protective recovery checks
  without letting Telegram control safety logic.
- `AuditJournalRecord` and recovery mismatch contracts support QuantConnect-wins
  restart handling.
- `NotificationDomainEvent`, `FakeNotificationCollector`,
  `NotificationDeduplicator`, and `NotificationRateLimiter` are the base for
  Telegram delivery and deterministic tests.

### Established Patterns

- Config files must include `paper_trading_only: true` and unsafe behavior flags
  that fail closed.
- Tests are deterministic and offline; real QuantConnect and Telegram calls are
  documented/manual or mocked.
- Domain events are typed and sanitized before transport.
- Documentation is updated in the same phase as code.
- Missing external access is represented as `not_configured` or `not_run`, not
  replaced with invented data.

### Integration Points

- Phase 8 should connect Phase 7 activation decisions to Phase 6 order intent
  and lifecycle contracts.
- QuantConnect adapters should convert authoritative deployment/order/fill state
  into local audit mirror events, not the reverse.
- Telegram transport should consume `NotificationDomainEvent` and emit
  `NotificationDeliveryResult`-style outcomes.
- Phase 9 dashboard will later consume Phase 8 mode, reconciliation, Telegram,
  and system-health artifacts read-only.

</code_context>

<specifics>
## Specific Ideas

- Start with Shadow Mode as the safest operational state.
- Use Limited Paper as a small controlled canary with stricter caps than the
  default Phase 6 risk settings.
- Treat `lean cloud live deploy` as an operator-controlled command, not a unit
  test action.
- Preserve exact commands and prerequisites in docs when QuantConnect access is
  unavailable.
- Implement Telegram real transport behind explicit configuration and mocked
  tests, while preserving the existing fake collector for deterministic tests.

</specifics>

<deferred>
## Deferred Ideas

- Render dashboard display of active Paper mode, reconciliation state, and
  Telegram health remains Phase 9.
- GitHub Actions automation for QuantConnect deployment/backtest workflows
  remains Phase 10 unless Phase 8 only documents prerequisites.
- Paid Telegram broadcast features are out of scope.
- Any migration to real-money brokerage remains prohibited and out of scope.

</deferred>

---

*Phase: 8-QuantConnect Paper Trading and Telegram*
*Context gathered: 2026-06-14*
