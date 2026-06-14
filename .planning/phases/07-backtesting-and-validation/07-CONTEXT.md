# Phase 7: Backtesting and Validation - Context

**Gathered:** 2026-06-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 7 proves backtesting methodology, no-look-ahead behavior, execution
realism, reports, and activation gates before any QuantConnect Paper Trading.
It may create deterministic local harnesses, validation adapters, backtest
configuration, report schemas, report generators, activation-state models,
notification preview events, tests, and documentation.

Phase 7 must not activate QuantConnect Paper Trading, submit Paper orders, send
real Telegram messages, fabricate backtest results, fabricate portfolio values,
claim profitability, or imply future certainty. QuantConnect Cloud/LEAN remains
the source of truth for official backtest results when real cloud runs are
available. If credentials or cloud access are unavailable, cloud checks are
recorded as not run and the phase continues with deterministic offline tests and
exact documented commands.

</domain>

<decisions>
## Implementation Decisions

### Backtest Authority And Offline Harness

- **D-01:** QuantConnect Cloud/LEAN is the source of truth for official
  backtest results, while Phase 7 also builds a deterministic local harness for
  no-look-ahead, timing, rule-consistency, and report-schema tests.
- **D-02:** Backtest and future Paper Trading must use the same strategy-rule
  modules. Backtest/Paper behavior should be adapters over the shared setup ->
  scoring -> ranking -> risk -> lifecycle -> exits pipeline, not duplicated
  strategy logic.
- **D-03:** Phase 7 may produce real backtest result artifacts only if they come
  from an actual documented run. If no real run is executed, Phase 7 may produce
  report schemas, parsers, fixtures, and examples, but no performance claims.
- **D-04:** If QuantConnect credentials, subscription, Docker/LEAN CLI, or cloud
  access are unavailable, mark cloud execution as `not_run`, preserve exact
  commands and prerequisites, and continue with offline deterministic tests. Do
  not create fake results to fill the gap.

### Execution Realism And No-Look-Ahead

- **D-05:** Completed-bar signals are evaluated only after the bar is complete;
  default daily signal fills occur at the next valid tradable open/price, not
  the same close.
- **D-06:** Same-bar entry/exit ambiguity must fail closed or be explicitly
  marked ambiguous; no optimistic same-bar fill assumption is allowed.
- **D-07:** Backtests must include explicit configurable fees, slippage, fill
  model, execution timing, and partial-fill assumptions. Defaults should be
  conservative and documented.
- **D-08:** Tests must include no future bars, current-bar exclusion, signal/fill
  separation, same-bar ambiguity, stale data, and strategy-mode timing
  alignment for `daily_only`, `daily_filter_4h_setup`, and
  `daily_filter_4h_setup_1h_optional`.

### Reporting, Validation Windows, And Benchmarks

- **D-09:** Reports must include full-period, year-by-year, in-sample,
  out-of-sample, walk-forward or equivalent chronological validation,
  sensitivity analysis, benchmark comparison, fee/slippage assumptions, and
  activation-gate outcomes.
- **D-10:** Use SPY as the primary benchmark and QQQ as a secondary context
  benchmark, consistent with prior relative-strength and regime decisions.
- **D-11:** Year-by-year and chronological validation should be explicit even
  when a fixture dataset is small; small datasets can mark some windows as
  unavailable, but cannot silently pretend coverage exists.
- **D-12:** Reports must show limitations, missing-data warnings, unavailable
  windows, and the exact disclaimer language. Historical reports must never
  claim guaranteed profitability or future certainty.

### Activation Gates And Approval State

- **D-13:** Strategy activation gates must block Paper order eligibility by
  default until validation is explicitly passed.
- **D-14:** Activation approval state should be typed and auditable, with states
  such as `unvalidated`, `validation_failed`, `validation_passed`,
  `approved_for_shadow`, `approved_for_limited_paper`, and
  `approved_for_full_paper`.
- **D-15:** Default repository state after Phase 7 should remain not approved
  for Paper Trading unless a real, documented validation run satisfies the
  configured gates.
- **D-16:** Validation gates should include no-look-ahead pass, no fake results,
  minimum backtest coverage, benchmark comparison, drawdown/risk checks,
  fee/slippage assumptions present, and report completeness. Exact numeric
  thresholds may be conservative config defaults and are not profitability
  guarantees.

### Notifications And Backtest Artifacts

- **D-17:** Normal historical backtests must not send notifications. Backtest
  notification preview mode may emit typed preview events through the Phase 6
  fake collector only.
- **D-18:** Notification preview events must be labeled as preview/historical,
  transport-neutral, sanitized, and unable to control safety logic.
- **D-19:** Backtest artifacts must distinguish real QuantConnect outputs,
  offline deterministic fixtures, schemas, and examples. Fixture artifacts must
  be visibly labeled as fixtures and cannot look like real performance.
- **D-20:** Backtest reports and artifacts should be machine-readable where
  useful, but generated human-readable docs must be synchronized so another AI
  can understand exactly what was run and what was not run.

### The Agent's Discretion

The user explicitly gave the agent freedom to choose Phase 7 answers. The agent
selected the conservative safety-first defaults above. The agent may choose
exact class names, config key names, and file layout during planning if these
decisions and the existing codebase patterns are preserved.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Scope And Safety

- `.planning/PROJECT.md` - Core value, paper-only scope, QuantConnect source of
  truth, no real-money behavior, and user language preference.
- `.planning/REQUIREMENTS.md` - Requirement IDs `BT-01` through `BT-08`.
- `.planning/ROADMAP.md` - Phase 7 goal, success criteria, and planned plan
  breakdown.
- `.planning/STATE.md` - Current status and decisions from prior phases.
- `docs/safety.md` - No fake performance, no fake portfolio, no real-money
  behavior, and source-of-truth constraints.
- `docs/Dahan-MarketPilot-Master-Spec.md` - Product-level backtesting,
  validation, report, activation, and paper-only expectations.

### Inputs From Prior Phases

- `.planning/phases/04.1-multi-timeframe-signal-foundation/04.1-CONTEXT.md` -
  Strategy modes, completed-bar timing, and MTF validation expectations.
- `.planning/phases/05-relative-strength-and-unified-scoring/05-CONTEXT.md` -
  Score, classification, confidence, and ranking decisions.
- `.planning/phases/06-portfolio-risk-and-order-lifecycle/06-CONTEXT.md` -
  Risk, order lifecycle, exits, audit, and notification-domain decisions.
- `.planning/phases/06-portfolio-risk-and-order-lifecycle/06-VERIFICATION.md` -
  Verification that Phase 6 contracts are implemented.

### Existing Code Contracts

- `marketpilot/timeframes.py` - StrategyMode and completed-bar/timeframe
  contracts.
- `marketpilot/ranking.py` - RankedCandidate audit input boundary.
- `marketpilot/scoring.py` - MarketPilotScore, classification, confidence, and
  gate status contracts.
- `marketpilot/risk.py` - Risk decisions and sizing contracts.
- `marketpilot/order_lifecycle.py` - Order intent/lifecycle/idempotency
  contracts.
- `marketpilot/exits.py` - Exit obligation contracts.
- `marketpilot/audit_journal.py` - Append-only audit record contracts.
- `marketpilot/notification_events.py` - Typed fake notification-domain event
  contracts for preview mode.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets

- `SetupTiming` already records completed-bar timing, strategy mode, timeframe,
  bar start/end, freshness, and later-valid-execution requirement.
- `RankedCandidate` provides one candidate per symbol and remains an audit
  candidate, not an order request.
- `RiskDecision`, `OrderIntent`, `ExitPlan`, `AuditJournalRecord`, and
  `NotificationDomainEvent` are Phase 6 contracts that Phase 7 can compose for
  simulation and validation without Paper submission.
- `NotificationDomainEvent` and `FakeNotificationCollector` support historical
  preview events without Telegram delivery.

### Established Patterns

- Config files live under `config/`, use `paper_trading_only: true`, and fail
  closed on unsafe behavior flags.
- Tests are deterministic offline pytest suites.
- Documentation is updated in the same phase as code.
- Local code must never fabricate QuantConnect state or performance results.

### Integration Points

- Phase 7 should add backtest/validation contracts that consume the shared
  strategy pipeline and produce reports/activation-state outputs.
- Phase 8 should consume Phase 7 activation state before enabling Shadow,
  Limited Paper, or Full Approved Paper modes.
- Phase 9 should eventually display only real or clearly labeled validation
  artifacts in the read-only dashboard.

</code_context>

<specifics>
## Specific Ideas

- Add a deterministic local validation harness for no-look-ahead and
  same-bar-ambiguity tests.
- Add config for fees, slippage, fill model, execution timing, validation
  windows, benchmark symbols, and activation gates.
- Add typed validation approval state that defaults to not approved for Paper.
- Add report schemas that separate real QuantConnect outputs from fixtures and
  examples.
- Add notification preview mode using Phase 6 fake collector only.

</specifics>

<deferred>
## Deferred Ideas

- Actual QuantConnect Paper Trading remains Phase 8.
- Real Telegram delivery remains Phase 8.
- Render dashboard display of backtest and validation artifacts remains Phase 9.
- Any unverified profitability claim remains prohibited.

</deferred>

---

*Phase: 7-Backtesting and Validation*
*Context gathered: 2026-06-14*

