# Phase 5: Relative Strength and Unified Scoring - Context

**Gathered:** 2026-06-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 5 implements the Relative Strength Leader setup and introduces the first
unified MarketPilot scoring layer. It should consume the Phase 2 readiness,
indicator, SymbolData, and regime contracts plus the Phase 3 Trend Pullback and
Phase 4 Volume Breakout setup evidence. It may create Relative Strength Leader
contracts, scoring configuration, score component models, candidate ranking,
classification, confidence, setup comparison, tests, and documentation.

After the Phase 4.1 insertion, this phase must depend on the multi-timeframe
foundation. It should consume StrategyMode, daily context evidence, 4H setup
evidence, optional 1H confirmation evidence, timeframe alignment status, and
data-quality confidence. It must not invent final MTF scoring weights before
backtesting and sensitivity validation.

This phase must not create orders, position sizing, portfolio state mutation,
stops, targets, fills, Paper Trading deployment, Telegram delivery, backtest
results, live-trading behavior, or fake performance artifacts. Combined Swing
must remain disabled behind an explicit readiness gate.

</domain>

<decisions>
## Implementation Decisions

### Relative Strength Leader

- **D-01:** Relative Strength Leader operates both as an independent setup and
  as confirmation evidence for other setups. It must not create Combined Swing
  behavior in Phase 5.
- **D-02:** SPY relative strength is the hard benchmark gate. QQQ relative
  strength is always measured as numeric evidence, bonus, warning, or context,
  but weak QQQ relative strength must not reject a symbol by itself.
- **D-03:** Relative Strength Leader requires both 20-day and 60-day relative
  strength versus SPY to be positive.
- **D-04:** QQQ should be measured for every candidate, including
  non-technology and non-growth stocks, but sector relevance must not be used as
  a hard gate until sector/industry data is verified.

### MarketPilot Score

- **D-05:** MarketPilot Score is a 0-100 score using the master specification
  default weights: trend structure 25, relative strength 20, momentum 15, setup
  quality 20, volume confirmation 10, and risk quality 10. The weights must
  total 100 and be configurable/tested.
- **D-06:** All setups use the same score categories so candidates can be
  compared. Each setup may map different setup-specific evidence into those
  shared score categories.
- **D-07:** Hard rejection overrides score. Component evidence and component
  scores should be preserved where possible for audit, but final classification
  must be `REJECTED` when a hard rejection is present.
- **D-08:** Missing, invalid, or stale required scoring data fails closed. It
  must never become neutral or positive score.

### Classification And Confidence

- **D-09:** Phase 5 classifications are `BUY_CANDIDATE`, `WATCH`, `AVOID`, and
  `REJECTED`.
- **D-10:** Default classification boundaries follow the master specification:
  `BUY_CANDIDATE` requires score >= 75, confidence >= 75, hard filters passing,
  market regime permitting new positions, expected reward/risk at least 2.0,
  portfolio constraints passing, and setup approval by the strategy activation
  gate. `WATCH` covers score 60-74, strong setups awaiting confirmation, or
  valid setups not approved for Paper execution. `AVOID` covers score below 60
  without a hard rejection. `REJECTED` covers hard rejection or critical
  failure.
- **D-11:** Confidence is not a duplicate of total score. It reflects evidence
  reliability and completeness, including readiness, data quality, component
  agreement, completed daily-bar timing validity, and deferred unknowns.
- **D-12:** Phase 5 must not fake portfolio constraints or activation gates.
  Represent unavailable or not-evaluated gates explicitly. Missing later-phase
  approval gates can downgrade an otherwise strong candidate to `WATCH`, but
  must not create orders, Paper approval behavior, or live behavior.

### Setup Ranking And Combined Swing Gate

- **D-13:** Ranking should produce at most one candidate per symbol. The
  strongest setup becomes the primary setup; additional valid setups are
  retained as supporting setups, confirmations, and evidence.
- **D-14:** Score ties are broken by higher confidence, then better risk
  quality, then stronger relative strength.
- **D-15:** Combined Swing remains disabled behind an explicit readiness gate.
  It may not become active until Trend Pullback, Volume Breakout, and Relative
  Strength Leader are independently validated, each setup has independent
  backtest and out-of-sample results, score component contributions are
  understood, and combining setups does not create duplicate entries or
  overfitting.
- **D-16:** Phase 5 output should be auditable `RankedCandidate` objects with
  symbol, primary setup, supporting setups, total score, component scores,
  classification, confidence, evidence, hard rejections, timing, and
  explanation. It must not include entry, stop, target, quantity, order intent,
  or broker/Paper behavior.
- **D-17:** Phase 5 consumes Phase 4.1 StrategyMode and timeframe-aware timing
  contracts. It must preserve `daily_only` compatibility and record the active
  `strategy_mode` in scoring/ranking evidence.
- **D-18:** Phase 5 evidence concepts include `daily_context_score`,
  `four_hour_setup_score`, `one_hour_confirmation_score`,
  `timeframe_alignment_status`, and `data_quality_confidence`.
- **D-19:** In MTF modes, Daily remains a mandatory gate, 4H is the primary
  setup/signal timeframe, and 1H is supporting confirmation only. Missing 1H
  alone must not reject a valid Daily+4H candidate.
- **D-20:** MTF component weights are not locked in Phase 5 planning. Backtesting
  and sensitivity analysis must validate any later MTF weighting scheme.

### The Agent's Discretion

The user delegated several choices to the agent with "you choose." The locked
agent choices are the recommended conservative options: always measure QQQ as
evidence without a QQQ hard rejection; use master specification score weights;
use shared score categories with setup-specific evidence mapping; let hard
rejection override score; fail closed on required missing/invalid/stale scoring
data; calculate confidence as evidence reliability, not score duplication; use
explicit unavailable/not-evaluated placeholders for later portfolio and
activation gates; use confidence, risk quality, and relative strength as
tie-breakers; keep Combined Swing disabled behind an explicit readiness gate;
and output audit candidates only, not trade/order objects.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Scope And Requirements

- `.planning/PROJECT.md` - Core value, safety constraints, paper-only rules,
  completed daily-bar constraint, source-of-truth rules, and out-of-scope
  live-money behavior.
- `.planning/REQUIREMENTS.md` - Phase 5 requirement IDs `SET-05`, `SET-06`,
  `SCO-01`, `SCO-02`, and `SCO-03`; carried requirements include `IND-02`,
  `IND-05`, `REG-03`, `SET-07`, `SET-MTF-03`, and safety requirements.
- `.planning/ROADMAP.md` - Phase 5 goal, dependency on Phase 4.1, success
  criteria, and plan breakdown.
- `.planning/STATE.md` - Current project state, Phase 5 focus, and Phase 2-4
  readiness/evidence contracts.
- `.planning/phases/04.1-multi-timeframe-signal-foundation/04.1-CONTEXT.md` -
  StrategyMode, timeframe responsibilities, 4H alignment recommendation, and
  Phase 5 handoff constraints.
- `.planning/phases/04.1-multi-timeframe-signal-foundation/04.1-VALIDATION.md` -
  Required tests for completed-bar models, generalized timing, readiness, and
  forbidden behavior.
- `docs/Dahan-MarketPilot-Master-Spec.md` - Master strategy specification,
  including Relative Strength Leader requirements, MarketPilot Score weights,
  classification boundaries, confidence, Combined Swing prerequisites, and MTF
  strategy-mode constraints.

### Prior Phase Contracts To Reuse

- `.planning/phases/02-quantconnect-foundation-and-universe/02-CONTEXT.md` -
  Locked decisions for data quality, indicator readiness, SymbolData lifecycle,
  relative strength indicator foundations, and market regime boundaries.
- `.planning/phases/03-trend-pullback/03-CONTEXT.md` - Locked Trend Pullback
  setup evidence, rejection, completed daily-bar timing, and no-classification
  boundaries.
- `.planning/phases/04-volume-breakout/04-CONTEXT.md` - Locked Volume Breakout
  evidence, current-bar exclusion, volume confirmation, stale-data rejection,
  and no-scoring-before-Phase-5 boundaries.
- `.planning/phases/04-volume-breakout/04-VERIFICATION.md` - Phase 4
  verification result confirming the stale-data gap is closed and Phase 4 is
  ready for Phase 5 consumption.
- `docs/indicators.md` - Indicator readiness and invalid-data rejection rules.
- `docs/market_regime.md` - SPY/QQQ regime as a future-entry gate only.
- `docs/trend_pullback.md` - Existing setup documentation and evidence pattern.
- `docs/volume_breakout.md` - Existing setup documentation and evidence pattern.
- `docs/testing.md` - Offline deterministic test policy.
- `docs/safety.md` - Paper-only, no-real-money, and no-fake-performance rules.

### Existing Code

- `marketpilot/setups/base.py` - Shared `SetupResult`, `SetupTiming`,
  `NumericEvidence`, `SetupStatus`, and rejection reason contracts.
- `marketpilot/setups/trend_pullback.py` - Existing completed daily-bar setup
  evaluator and evidence style to consume for scoring.
- `marketpilot/setups/volume_breakout.py` - Existing breakout evaluator,
  volume/risk evidence, stale-data evidence, and rejection style to consume for
  scoring.
- `marketpilot/indicators.py` - Existing EMA, RSI, MACD, ROC, ATR, average,
  relative strength, and 52-week high distance helpers.
- `marketpilot/symbol_data.py` - Readiness boundary for setup eligibility,
  including stale data rejection.
- `marketpilot/regime.py` - Market regime future-entry permission behavior.
- `config/trend_pullback.yaml` and `config/volume_breakout.yaml` - Existing
  setup config and disabled behavior guardrail patterns.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets

- `SetupResult` already carries setup name, symbol, validity/rejection status,
  completed daily-bar timing, numeric evidence, rejection reasons, and
  explanation without trading side effects.
- `NumericEvidence` can be consumed by scoring and ranking without changing the
  setup modules into order or portfolio modules.
- `marketpilot.indicators.relative_strength()` already provides deterministic
  relative strength evidence over configurable windows.
- `SymbolData.future_signal_ready()` provides a fail-closed readiness boundary
  for required indicators and stale data.
- `MarketRegime` and `RegimeResult.future_entries_allowed` provide the
  reusable market-regime gate for candidate classification.

### Established Patterns

- New strategy logic lives under `marketpilot/` with deterministic offline
  pytest coverage.
- Configuration lives under `config/` and should preserve `paper_trading_only:
  true` plus explicit disabled behavior guardrails.
- Setup modules return evidence and rejection reasons; they do not create
  orders, portfolio state, Paper deployment, Telegram messages, or fake
  backtest artifacts.
- Documentation must be updated in the same phase as implementation.
- English is required for repository files, tests, docs, GSD artifacts, and
  commit messages; Hebrew is only for user-facing chat.

### Integration Points

- Relative Strength Leader should consume Phase 2 indicator/readiness/regime
  contracts instead of duplicating validation logic.
- MarketPilot scoring should consume existing Trend Pullback and Volume
  Breakout evidence without changing their setup-only boundaries.
- Candidate ranking should prepare clean inputs for future Phase 6 risk/order
  lifecycle, Phase 7 validation/backtesting, and Phase 9 dashboard views while
  avoiding any order intent or fake portfolio behavior.
- Combined Swing should be represented only as a disabled/readiness-gated
  future capability.

</code_context>

<specifics>
## Specific Ideas

- The user selected Relative Strength Leader as both independent setup and
  confirmation evidence for other setups.
- The user selected SPY as the hard relative strength gate.
- The user selected RS20 and RS60 positive versus SPY as required.
- The user delegated QQQ handling to the agent; the locked choice is to always
  measure QQQ as evidence without making weak QQQ a standalone rejection.
- The user delegated several MarketPilot Score mechanics to the agent; the
  locked choices preserve the master specification defaults and safety-first
  fail-closed behavior.
- The user selected the full classification label set:
  `BUY_CANDIDATE`, `WATCH`, `AVOID`, and `REJECTED`.
- The user selected master specification classification thresholds.
- The user selected one candidate per symbol, with secondary setups retained as
  supporting evidence rather than duplicate entries.

</specifics>

<deferred>
## Deferred Ideas

- Full portfolio constraints, position sizing, stops, targets, orders, fills,
  exits, duplicate-order prevention, and portfolio conflict calculation remain
  deferred to Phase 6.
- Independent backtests, out-of-sample results, activation gates, MTF strategy
  mode comparisons, 4H alignment comparisons, optional mandatory-1H experiment,
  2H alternative evaluation, and Combined Swing validation remain deferred to
  Phase 7.
- Telegram candidate and classification alerts remain deferred to notification
  phases.
- Paper Trading deployment and any approved Paper behavior remain deferred to
  Phase 8.
- Dashboard presentation of ranked candidates remains deferred to Phase 9.
- Breakout Retest and Volatility Contraction / Base Breakout are future setup
  ideas only and are not part of Phase 4.1 or Phase 5.

</deferred>

---

*Phase: 5-Relative Strength and Unified Scoring*
*Context gathered: 2026-06-13*
