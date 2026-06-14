# Phase 6: Portfolio Risk and Order Lifecycle - Context

**Gathered:** 2026-06-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 6 builds paper-only portfolio risk, position sizing, order-intent
lifecycle, exit modeling, persistence, audit, and notification-domain event
contracts. It consumes Phase 5 ranked audit candidates but must not treat
classification labels as order instructions. QuantConnect remains the future
source of truth for Paper orders, fills, holdings, cash, and portfolio equity.

This phase may create deterministic offline models, validators, config files,
audit journal contracts, fake transports, tests, and documentation. It must not
submit QuantConnect Paper orders, connect to a broker, send Telegram messages,
create real Backtest results, fabricate portfolio values, or introduce any
real-money path.

</domain>

<decisions>
## Implementation Decisions

### Risk Budget And Portfolio Limits

- **D-01:** Default per-trade risk is 1% of simulated equity.
- **D-02:** Default maximum open positions is 10.
- **D-03:** Default maximum sector exposure is 30% of simulated equity.
- **D-04:** Default maximum new entries per Paper trading day is 3.

### Position Sizing And Cash Handling

- **D-05:** Position sizing uses `risk_amount / stop_distance`, not fixed dollar
  allocation and not MarketPilot Score scaling.
- **D-06:** Missing, zero, negative, non-finite, or otherwise invalid stop
  distance rejects fail-closed.
- **D-07:** Default maximum allocation per position is 15% of simulated equity.
- **D-08:** If available cash is insufficient, quantity may be reduced only when
  the reduced order still satisfies minimum risk/reward and minimum quantity
  rules; otherwise the candidate is rejected. Negative cash, margin, leverage,
  and borrowing remain forbidden.

### Order Lifecycle States

- **D-09:** Order lifecycle states should cover `planned`, `submitted`,
  `partially_filled`, `filled`, `rejected`, `canceled`,
  `protective_orders_pending`, `open`, `partially_closed`, and `closed`.
- **D-10:** QuantConnect is the source of truth for order/fill state. Local
  models are audit mirrors, intent records, and recovery context only.
- **D-11:** Duplicate-order prevention uses an idempotency key derived from
  symbol, strategy mode, primary setup, signal time, and portfolio epoch.
- **D-12:** Phase 6 does not submit real Paper orders. It creates models,
  intents, lifecycle transitions, and events only. QuantConnect Paper submission
  remains deferred to Phase 8 after Phase 7 validation.

### Stops And Exits

- **D-13:** Initial stop comes from setup evidence, such as structural
  invalidation, swing low, or breakout level, with an ATR sanity cap.
- **D-14:** Initial target must be at least 2R, with target price calculated from
  risk per share.
- **D-15:** Partial exits are supported as models and events only. Default
  partial exit behavior is configurable, such as partial at 1R or 2R; execution
  remains deferred.
- **D-16:** Trailing stop is modeled and configurable but disabled by default
  until validation proves it should be enabled.
- **D-17:** Exit obligations remain authoritative for existing positions even
  if market regime later turns `RISK_OFF`. `RISK_OFF` blocks new long entries
  but does not erase stop, target, partial-close, full-close, or recovery
  obligations.

### Persistence And Restart Recovery

- **D-18:** Phase 6 persists an append-only audit journal of intents, decisions,
  lifecycle events, config versions, and strategy versions. It is not the
  authoritative portfolio store.
- **D-19:** The audit journal format is JSONL.
- **D-20:** On restart mismatch, QuantConnect wins; local state is marked as a
  mismatch and a recovery event is emitted.
- **D-21:** Split and delisting handling is modeled through safe placeholder
  events and rejection/recovery states until QuantConnect integration is
  verified.

### Notification-Domain Events

- **D-22:** Phase 6 emits internal notification-domain events for risk
  rejection, sizing decision, order intent, lifecycle transition, stop/target
  update, partial close, full close, and recovery mismatch.
- **D-23:** Notification-domain events are typed dataclasses with stable
  `event_type` values and sanitized payloads. They must not be Telegram strings
  or transport-specific payloads.
- **D-24:** Future notification delivery failure must never block risk logic,
  order safety, protective exits, or lifecycle progression.
- **D-25:** Phase 6 includes a fake transport or collector for deterministic
  tests only. Real Telegram integration remains deferred to later phases.

### The Agent's Discretion

The user selected the recommended option for every Phase 6 decision. The agent
may choose final class names, module boundaries, enum names, and file layout
based on existing code patterns, provided the decisions above are preserved.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Scope And Safety

- `.planning/PROJECT.md` - Core value, paper-only scope, QuantConnect source of
  truth, no real-money behavior, strategy-mode constraints, and user language
  preference.
- `.planning/REQUIREMENTS.md` - Requirement IDs `SCO-04`, `RISK-01`,
  `RISK-02`, `RISK-03`, `RISK-04`, `RISK-05`, `RISK-06`, and `RISK-07`.
- `.planning/ROADMAP.md` - Phase 6 goal, dependency on Phase 5, success
  criteria, and planned plan breakdown.
- `.planning/STATE.md` - Current state and accumulated decisions from Phases
  1-5.
- `docs/safety.md` - Paper-only constraints, no fake portfolio/performance,
  QuantConnect source-of-truth policy, and Phase 5 audit-only boundaries.
- `docs/Dahan-MarketPilot-Master-Spec.md` - Product-level risk, order,
  Telegram, dashboard, and paper-only expectations.

### Inputs From Prior Phases

- `.planning/phases/04.1-multi-timeframe-signal-foundation/04.1-CONTEXT.md` -
  StrategyMode, timing, and MTF evidence contracts that Phase 6 must preserve.
- `.planning/phases/05-relative-strength-and-unified-scoring/05-CONTEXT.md` -
  Phase 5 ranking and audit-candidate decisions.
- `.planning/phases/05-relative-strength-and-unified-scoring/05-VERIFICATION.md`
  - Verification that RSL, scoring, ranking, and Combined Swing gate are
  complete.
- `docs/scoring.md` - Audit-only classification and ranking contract.
- `marketpilot/ranking.py` - `RankedCandidate` shape that Phase 6 consumes.
- `marketpilot/scoring.py` - `MarketPilotScore`, classifications, gates, and
  evidence objects.
- `marketpilot/models.py` - Existing money/currency/safety foundational models.
- `marketpilot/timeframes.py` - StrategyMode and setup timing metadata.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets

- `marketpilot.models.Money`, `CurrencyCode`, and `positive_decimal()` provide
  safe money/positive-number patterns for risk and sizing.
- `marketpilot.ranking.RankedCandidate` is the Phase 6 input boundary. It is an
  audit candidate, not an order request.
- `marketpilot.scoring.MarketPilotScore`, `CandidateClassification`, and
  `GateStatus` provide score and gate evidence, but classification labels must
  not directly authorize order intents.
- `marketpilot.setups.base.NumericEvidence` and `SetupTiming` preserve the
  evidence/timing trail needed for audit and idempotency.
- `marketpilot.safety.validate_safety_config()` and existing config loaders show
  the fail-closed config pattern.

### Established Patterns

- Config lives under `config/` and requires `paper_trading_only: true` plus
  explicit disabled unsafe behaviors.
- New domain logic lives under `marketpilot/` with deterministic offline pytest
  coverage.
- Docs are updated in the same phase as implementation.
- Local models must be explicit about deferred integration boundaries and must
  not fabricate QuantConnect state.

### Integration Points

- Phase 6 consumes ranked candidates and emits risk decisions, order intents,
  lifecycle events, and notification-domain events.
- Phase 7 consumes Phase 6 risk/order lifecycle contracts for backtesting and
  validation.
- Phase 8 consumes Phase 6 intents/lifecycle events when real QuantConnect
  Paper Trading and Telegram delivery are implemented.
- Phase 9 consumes audit/risk/order lifecycle state for read-only dashboard
  views.

</code_context>

<specifics>
## Specific Ideas

- Use 1% risk per trade, 10 max open positions, 30% max sector exposure, and 3
  max new entries per day.
- Use risk-based sizing with stop distance; invalid stop distance is a hard
  fail-closed rejection.
- Cap allocation per position at 15% of simulated equity.
- Use JSONL append-only audit journal for local trace/recovery context.
- Use typed notification-domain events and fake test transport only.

</specifics>

<deferred>
## Deferred Ideas

- Real QuantConnect Paper order submission remains Phase 8.
- Real Telegram delivery remains Phase 8.
- Real Backtest execution and activation gates remain Phase 7.
- Full split/delisting execution behavior remains deferred until QuantConnect
  integration is verified.

</deferred>

---

*Phase: 6-Portfolio Risk and Order Lifecycle*
*Context gathered: 2026-06-14*
