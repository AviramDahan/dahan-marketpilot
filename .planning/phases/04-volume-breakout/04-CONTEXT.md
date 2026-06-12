# Phase 4: Volume Breakout - Context

**Gathered:** 2026-06-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 4 implements the Volume Breakout setup as an independently testable,
auditable setup module. It should identify completed daily-bar closes that
break above prior resistance using a current-bar-excluded resistance window,
volume confirmation, extension/risk filters, and numeric evidence.

This phase may create Volume Breakout configuration, setup input/result
contracts, evaluator logic, rejection reasons, deterministic tests, and
documentation. It must not create orders, position sizing, portfolio state,
BUY/WATCH/AVOID classifications, full MarketPilot scoring, backtest results,
Paper Trading deployment, Telegram delivery, or live-trading behavior.

</domain>

<decisions>
## Implementation Decisions

### Prior Resistance Calculation

- **D-01:** Prior resistance is calculated as the highest high from a
  configurable completed daily-bar lookback window, excluding the current bar.
- **D-02:** The default resistance lookback window is 20 completed daily bars.
- **D-03:** Breakout validity requires the completed daily close to be above
  prior resistance. An intraday high above resistance is not enough.
- **D-04:** A small configurable percentage buffer above resistance is required
  to avoid treating borderline closes as valid breakouts.

### Breakout Confirmation

- **D-05:** Volume confirmation uses the breakout bar's volume compared against
  a 20-day average volume baseline.
- **D-06:** The default volume confirmation threshold is at least 1.5x the
  average volume.
- **D-07:** Breakouts are rejected when price is overextended from EMA20 above a
  configurable threshold.
- **D-08:** `RISK_OFF` rejects Volume Breakout validity, matching the Phase 3
  Trend Pullback entry-gate behavior.

### Risk And Rejection Gates

- **D-09:** Excessive ATR% is a hard rejection using a configurable threshold.
- **D-10:** Phase 4 should calculate a conservative reward/risk proxy using the
  broken resistance area as the base/stop proxy. This must not create orders,
  real stops, targets, or position lifecycle behavior.
- **D-11:** Earnings risk remains a deferred verified-source gate. If no
  verified earnings data source exists, Phase 4 must not invent data and must
  not reject symbols based only on unverified earnings assumptions.
- **D-12:** Portfolio conflicts are represented only as future-compatible
  evidence/rejection placeholders. Phase 4 must not calculate real portfolio
  constraints before Phase 6.

### Evidence, Explanations, And Boundaries

- **D-13:** Every Volume Breakout result should include numeric evidence for
  resistance level, lookback window, breakout buffer, breakout close, volume
  ratio, EMA20 extension, ATR%, reward/risk proxy, and market regime.
- **D-14:** Phase 4 returns setup results with valid/rejected status, evidence,
  explanations, and rejection reasons only. It must not add score or
  classification behavior before Phase 5.
- **D-15:** Phase 4 code must exclude `BUY`, `WATCH`, `AVOID`, orders, position
  sizing, portfolio state, backtest result creation, Telegram delivery, and
  live/Paper deployment behavior.
- **D-16:** Prefer a module parallel to Trend Pullback:
  `config/volume_breakout.yaml`, `marketpilot/setups/volume_breakout.py`,
  matching tests, and documentation. Do not generalize `trend_pullback.py` into
  a broader framework during this phase unless planning proves it necessary.

### the agent's Discretion

The user selected the recommended option for every discussed decision except
the excessive ATR handling question, where the user chose "You choose." The
locked agent choice is the recommended conservative policy: excessive ATR% is a
hard rejection with a configurable threshold, consistent with SET-04 and Phase
3 Trend Pullback.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Scope And Requirements

- `.planning/PROJECT.md` - Core value, paper-only constraints, completed daily
  bar signal constraint, source-of-truth rules, and out-of-scope live-money
  behavior.
- `.planning/REQUIREMENTS.md` - Phase 4 requirement IDs `SET-03` and `SET-04`;
  relevant carried requirements include `IND-03`, `IND-04`, `IND-05`,
  `REG-03`, `SET-07`, and safety requirements.
- `.planning/ROADMAP.md` - Phase 4 goal, dependency on Phase 3, success
  criteria, and plan breakdown.
- `.planning/STATE.md` - Current project state and Phase 4 focus.
- `docs/Dahan-MarketPilot-Master-Spec.md` - Master strategy and safety
  specification.

### Prior Phase Contracts To Reuse

- `.planning/phases/02-quantconnect-foundation-and-universe/02-CONTEXT.md` -
  Locked decisions for data quality, indicator readiness, SymbolData lifecycle,
  and market regime boundaries.
- `.planning/phases/03-trend-pullback/03-CONTEXT.md` - Locked setup result,
  completed-bar timing, evidence, rejection, reward/risk proxy, and forbidden
  behavior boundaries to mirror for Volume Breakout.
- `.planning/phases/03-trend-pullback/03-VERIFICATION.md` - Phase 3
  verification results and next-phase readiness.
- `docs/universe.md` - Strict universe and data-quality behavior.
- `docs/indicators.md` - Indicator readiness and invalid-data rejection.
- `docs/market_regime.md` - SPY/QQQ regime as a future-entry gate only.
- `docs/trend_pullback.md` - Existing setup documentation pattern.
- `docs/testing.md` - Offline deterministic test policy.
- `docs/safety.md` - Paper-only and no-fake-performance rules.

### Existing Code

- `marketpilot/setups/base.py` - Shared `SetupResult`, `SetupTiming`,
  `NumericEvidence`, `SetupStatus`, and rejection reason patterns.
- `marketpilot/setups/trend_pullback.py` - Existing setup evaluator shape,
  completed daily-bar input model, config loader pattern, and evidence style.
- `config/trend_pullback.yaml` - Existing setup config structure and disabled
  behavior guardrails to mirror.
- `marketpilot/symbol_data.py` - Readiness boundary for setup eligibility.
- `marketpilot/indicators.py` - Indicator readiness and invalid-value handling.
- `marketpilot/regime.py` - Market regime entry-gate behavior.
- `tests/test_trend_pullback_contract.py`,
  `tests/test_trend_pullback_detection.py`,
  `tests/test_trend_pullback_rejections.py`,
  `tests/test_trend_pullback_explanations.py`, and
  `tests/test_trend_pullback_safety.py` - Existing setup test patterns to
  extend or mirror.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets

- `SetupResult`, `SetupTiming`, and `NumericEvidence` already support setup
  validity, completed daily-bar timing, evidence, explanations, and rejection
  reasons without trading side effects.
- `CompletedDailyBar` from Trend Pullback provides a simple completed daily-bar
  fixture shape that Phase 4 can reuse or mirror.
- `SymbolData.future_signal_ready()` provides the readiness boundary before
  setup evaluation.
- `MarketRegime` and `RegimeResult.future_entries_allowed` provide the
  reusable `RISK_OFF` gate.
- The Trend Pullback config loader provides a fail-closed pattern for
  `paper_trading_only: true` and disabled behavior checks.

### Established Patterns

- Setup modules live under `marketpilot/setups/` and use deterministic offline
  pytest coverage.
- Setup configuration lives under `config/` and must keep
  `paper_trading_only: true` plus explicit disabled behaviors.
- Setup evaluators return valid/rejected setup results with evidence; they do
  not return trade instructions or classifications.
- Docs must be updated in the same phase as implementation.
- Safety tests should prove forbidden behavior is absent from production setup
  files.
- English is required for repository files and GSD artifacts; Hebrew is only
  for user-facing chat.

### Integration Points

- Volume Breakout should consume Phase 2 readiness, indicator, data-quality,
  SymbolData, and regime concepts instead of duplicating them.
- Future Phase 5 scoring should be able to consume Volume Breakout evidence,
  but Phase 4 must not implement final MarketPilot Score.
- Future Phase 6 risk/order lifecycle should be able to replace the
  placeholder portfolio-conflict and reward/risk proxy behavior with full
  portfolio constraints, stops, targets, and order lifecycle logic.

</code_context>

<specifics>
## Specific Ideas

- The user chose a 20 completed daily-bar prior-resistance window.
- The user chose current-bar exclusion for resistance calculation.
- The user chose close-based breakout confirmation, not intraday high validity.
- The user chose a small configurable breakout buffer.
- The user chose 20-day average volume and a 1.5x default volume threshold.
- The user chose EMA20 overextension rejection.
- The user chose `RISK_OFF` as a hard rejection.
- The user delegated excessive ATR handling to the agent; the agent locked the
  conservative hard-rejection policy.
- The user chose a conservative reward/risk proxy based on the broken
  resistance area without creating stop/order behavior.
- The user chose earnings source status as evidence/deferred until a verified
  source exists.
- The user chose portfolio-conflict placeholder evidence/rejection only until
  Phase 6.
- The user chose a module parallel to Trend Pullback rather than refactoring the
  existing setup implementation now.

</specifics>

<deferred>
## Deferred Ideas

- Verified earnings-risk source and live earnings calendar integration are
  deferred to a later phase.
- Real portfolio constraints, position sizing, stop/target/order lifecycle, and
  portfolio conflict calculation are deferred to Phase 6.
- BUY/WATCH/AVOID classifications and full MarketPilot scoring are deferred to
  Phase 5.
- Backtest results and activation gates are deferred to Phase 7.
- Telegram alerts are deferred to notification phases.
- Live/Paper deployment behavior is deferred to Paper Trading phases.

</deferred>

---

*Phase: 4-Volume Breakout*
*Context gathered: 2026-06-13*
