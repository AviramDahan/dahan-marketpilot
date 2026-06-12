# Phase 3: Trend Pullback - Context

**Gathered:** 2026-06-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 3 implements the Trend Pullback setup as an independently testable,
auditable setup module. It should identify strong liquid common-equity
candidates in established uptrends that pull back toward EMA20 or EMA50 and
begin to recover using completed daily bars.

This phase may create setup result models, evidence records, rejection reasons,
fixture tests, and documentation for Trend Pullback behavior. It must not create
orders, position sizing, portfolio state, BUY/WATCH/AVOID classifications, full
MarketPilot scoring, backtest results, Paper Trading deployment, Telegram
delivery, or live-trading behavior.

</domain>

<decisions>
## Implementation Decisions

### Pullback Structure

- **D-01:** A valid Trend Pullback is a pullback that touches or approaches
  EMA20 or EMA50 while the broader trend remains intact.
- **D-02:** The default pullback duration window is 2-10 completed daily bars.
  The planner may make exact thresholds configurable, but tests must prove the
  configured window is enforced.
- **D-03:** A close below EMA50 is a hard rejection for Phase 3 Trend Pullback.
  The implementation should fail closed rather than treating broken structure
  as a weak but acceptable setup.

### Recovery Confirmation

- **D-04:** Recovery is confirmed by a completed daily candle that closes above
  the prior candle high.
- **D-05:** Recovery volume must be above a short average volume threshold. This
  is a Trend Pullback quality gate, not a Volume Breakout implementation.
- **D-06:** RSI14 and MACD evidence should be recorded as numeric supporting
  evidence, but they are not hard gates and must not produce trade
  classifications.

### Hard Rejections

- **D-07:** The setup is rejected immediately when any of these are true:
  `RISK_OFF`, data-quality/readiness is not accepted, EMA50 structure is broken,
  ATR/risk is excessive, or the minimal reward/risk proxy is weak.
- **D-08:** Earnings risk remains a deferred verified-source gate. If no
  verified earnings data source exists, Phase 3 must not invent data and must
  not reject symbols based on unverified earnings assumptions.
- **D-09:** Phase 3 should calculate a minimal, deterministic reward/risk proxy
  and reject only when the proxy is invalid or very weak. This must not create a
  full stop/target/order lifecycle, which belongs to later phases.

### Signal Timing And Evidence

- **D-10:** A Trend Pullback result is valid only after a completed daily bar.
  Intrabar conditions are out of scope for Phase 3 and must not be treated as a
  valid signal.
- **D-11:** Every setup result must include numeric evidence, rejection reasons,
  readiness status, market regime state, and signal timing metadata.
- **D-12:** Phase 3 returns setup results with valid/rejected status and
  evidence. It must not return `BUY`, `WATCH`, or `AVOID` classifications.

### the agent's Discretion

The user accepted recommended choices for most decisions. The only corrected
answer was signal timing: the user initially selected intrabar validity, then
confirmed the safer completed-daily-bar interpretation after the conflict with
project constraints was explained. Routine implementation details such as exact
config key names, fixture shape, and dataclass names are left to the planner as
long as the decisions above are preserved.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Scope And Requirements

- `.planning/PROJECT.md` - Core value, paper-only constraints, completed daily
  bar signal constraint, source-of-truth rules, and out-of-scope live-money
  behavior.
- `.planning/REQUIREMENTS.md` - Phase 3 requirement IDs `SET-01`, `SET-02`,
  and `SET-07`; relevant carried requirements include `IND-05`, `REG-03`, and
  safety requirements.
- `.planning/ROADMAP.md` - Phase 3 goal, dependencies, success criteria, and
  planned plan breakdown.
- `.planning/STATE.md` - Current project state and Phase 3 focus.
- `docs/Dahan-MarketPilot-Master-Spec.md` - Master strategy and safety
  specification.

### Phase 2 Contracts To Reuse

- `.planning/phases/02-quantconnect-foundation-and-universe/02-CONTEXT.md` -
  Locked decisions for universe, data-quality, indicator readiness, SymbolData,
  and market regime boundaries.
- `.planning/phases/02-quantconnect-foundation-and-universe/02-VERIFICATION.md`
  - Phase 2 verification results and next-phase readiness.
- `docs/quantconnect_verification.md` - Verified QuantConnect/LEAN API
  contracts and external-check boundaries.
- `docs/universe.md` - Strict universe and data-quality behavior.
- `docs/indicators.md` - Indicator readiness, invalid-data rejection, and
  SymbolData cleanup rules.
- `docs/market_regime.md` - SPY/QQQ regime as a future-entry gate only.
- `docs/testing.md` - Offline deterministic test policy.
- `docs/safety.md` - Paper-only and no-fake-performance rules.

### Existing Code

- `marketpilot/data_quality.py` - Data-quality statuses, issues, candidates,
  decisions, and snapshots.
- `marketpilot/universe.py` - Strict offline universe filtering and snapshot
  construction.
- `marketpilot/indicators.py` - Offline indicator helpers and readiness
  results.
- `marketpilot/symbol_data.py` - SymbolData readiness and cleanup lifecycle.
- `marketpilot/regime.py` - Offline market-regime classifier and entry-gate
  result.
- `marketpilot/safety.py` - Fail-closed safety validation pattern.
- `tests/test_universe.py`, `tests/test_data_quality.py`,
  `tests/test_indicators.py`, `tests/test_symbol_data.py`, and
  `tests/test_regime.py` - Fixture and assertion patterns to extend.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets

- `UniverseSnapshot` and `UniverseDecision` provide accepted/rejected universe
  records and explicit rejection reasons.
- `DataQualityStatus` provides the accepted/rejected readiness boundary for
  setup eligibility.
- `IndicatorResult` and `ReadinessStatus` provide ready/not-ready/invalid
  indicator state and numeric values.
- `SymbolData.future_signal_ready()` provides a reusable readiness check before
  Trend Pullback evaluation.
- `MarketRegime` and `RegimeResult.future_entries_allowed` provide the regime
  gate. `RISK_OFF` should block Trend Pullback validity.

### Established Patterns

- New code should be pure Python under `marketpilot/` with deterministic offline
  pytest coverage.
- Configuration lives under `config/` and must keep `paper_trading_only: true`
  where relevant.
- Docs must be updated in the same phase as implementation.
- Tests should prove forbidden behavior is absent, especially order calls,
  fake backtests, live deployment, Telegram delivery, and classification names
  that belong to later scoring phases.
- English is required for repository files and GSD artifacts; Hebrew is only for
  user-facing chat.

### Integration Points

- Trend Pullback should consume Phase 2 readiness, indicator, universe, and
  regime concepts instead of duplicating them.
- Future Phase 5 scoring should be able to consume Trend Pullback evidence, but
  Phase 3 must not implement final MarketPilot Score.
- Future Phase 6 risk/order lifecycle should be able to replace the minimal
  reward/risk proxy with full stop/target behavior.

</code_context>

<specifics>
## Specific Ideas

- The user chose EMA20/EMA50 pullback structure.
- The user chose a 2-10 completed daily bar pullback window.
- The user chose EMA50 break as a hard rejection.
- The user chose prior-candle-high close as recovery confirmation.
- The user chose recovery volume above a short average.
- The user chose RSI/MACD as supporting evidence, not hard gates.
- The user chose strict hard rejections for regime, readiness, structure, ATR,
  and weak reward/risk proxy.
- The user chose earnings risk as deferred until a verified source exists.
- The user confirmed completed daily bars after a conflict with intrabar signal
  timing was identified.
- The user requested future choice questions include a clear recommended answer
  and use a more RTL-stable display format.

</specifics>

<deferred>
## Deferred Ideas

- Intrabar signal validity is deferred and out of scope for Phase 3.
- Verified earnings-risk source and live earnings calendar integration are
  deferred to a later phase.
- Full stop/target/order lifecycle and position sizing are deferred to Phase 6.
- BUY/WATCH/AVOID classifications and full MarketPilot scoring are deferred to
  Phase 5.
- Backtest results and activation gates are deferred to Phase 7.
- Telegram alerts are deferred to notification phases.

</deferred>

---

*Phase: 3-Trend Pullback*
*Context gathered: 2026-06-13*

