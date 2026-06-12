# Phase 3 Research: Trend Pullback

## Scope

Phase 3 implements the Trend Pullback setup as a deterministic offline setup
module. It must consume Phase 2 universe, data-quality, indicator readiness,
SymbolData, and market-regime contracts. It must not create orders, portfolio
state, full MarketPilot scoring, BUY/WATCH/AVOID classifications, backtest
results, Paper Trading deployment, Telegram delivery, or live deployment.

## Sources Reviewed

This research is grounded in repository artifacts rather than new external API
research. Phase 3 does not introduce a new third-party API surface.

- `.planning/phases/03-trend-pullback/03-CONTEXT.md`
- `.planning/REQUIREMENTS.md`
- `.planning/ROADMAP.md`
- `docs/Dahan-MarketPilot-Master-Spec.md`
- `.planning/phases/02-quantconnect-foundation-and-universe/02-CONTEXT.md`
- `.planning/phases/02-quantconnect-foundation-and-universe/02-VERIFICATION.md`
- `docs/universe.md`
- `docs/indicators.md`
- `docs/market_regime.md`
- `docs/testing.md`
- `docs/safety.md`
- `marketpilot/data_quality.py`
- `marketpilot/universe.py`
- `marketpilot/indicators.py`
- `marketpilot/symbol_data.py`
- `marketpilot/regime.py`

## Reusable Contracts

- `DataQualityStatus.ACCEPTED` is the eligibility boundary for setup
  evaluation.
- `SymbolData.future_signal_ready()` already combines data-quality state,
  indicator readiness, invalid values, stale state, and cleanup state.
- `IndicatorResult` provides numeric value, readiness status, required points,
  and available points.
- `MarketRegime.RISK_OFF` and `RegimeResult.future_entries_allowed` provide the
  future-entry gate. RISK_OFF must reject Trend Pullback validity without
  triggering liquidation or exits.
- `UniverseSnapshot` and `UniverseDecision` provide accepted/rejected universe
  context but should not become strategy signals by themselves.

## Planning Implications

1. Start with a setup contract and fixture vocabulary. This gives later tasks a
   stable result shape and prevents signal/classification drift.
2. Implement detection and rejection rules separately from any explanation or
   score-like presentation. The evaluator should return valid/rejected setup
   results with evidence, not trade instructions.
3. Add setup-quality components only as evidence/explanation fields. Do not
   implement global MarketPilot Score, confidence, BUY/WATCH/AVOID, ranking, or
   portfolio fit in Phase 3.
4. Completed daily bars are mandatory. Intrabar validity is explicitly deferred.
5. Earnings risk remains a documented deferred gate until a verified data source
   exists.
6. The reward/risk proxy should be deterministic and minimal. It may use
   fixture inputs such as close, structural low, and simple upside reference,
   but it must not create stops, targets, orders, or position sizing.

## Suggested Plan Boundaries

- `03-01`: Trend Pullback contract, configuration, fixture shape, and
  documentation skeleton.
- `03-02`: Detection, hard rejections, recovery behavior, and evidence records.
- `03-03`: Setup-quality evidence components, human-readable explanations, docs,
  and final phase verification guardrails.

## Risks

- **Classification creep:** Plan 03-03 can sound like scoring. Keep it limited
  to component evidence and explanations.
- **Risk/order creep:** Reward/risk proxy must not become stop/target/order
  lifecycle.
- **Look-ahead risk:** The evaluator must only consume completed daily bars and
  must record timing assumptions.
- **Data fabrication risk:** Earnings risk must remain deferred instead of using
  fake data.

