# Trend Pullback

Phase 3 implements Trend Pullback as an independently testable setup module.
It detects pullbacks toward EMA20 or EMA50 in an established uptrend and records
evidence and rejection reasons.

## Contract

The setup uses completed daily bars only. Intrabar validity is deferred and out
of scope.

Default configuration in `config/trend_pullback.yaml`:

- `min_pullback_bars: 2`
- `max_pullback_bars: 10`
- EMA20 and EMA50 proximity thresholds
- close above prior completed bar high as the recovery trigger
- recovery volume above a short average
- ATR/risk threshold fields
- minimal reward/risk proxy threshold

## Result Vocabulary

Trend Pullback returns setup results with:

- `valid` or `rejected` status
- numeric evidence
- rejection reasons
- completed daily timing metadata
- human-readable explanation fields

There is no BUY, WATCH, or AVOID output. There are no orders, no portfolio
sizing, no backtest result creation, no Telegram delivery, and no live
deployment behavior in Phase 3.

## Fixture Design

Tests should use deterministic completed daily bar fixtures. Fixtures should
cover:

- valid pullback toward EMA20
- valid pullback toward EMA50
- pullback window boundaries of 2-10 completed bars
- EMA50 break rejection
- prior-high recovery trigger
- recovery volume support
- readiness and RISK_OFF rejection
- reward/risk proxy rejection

## Deferred Boundaries

Earnings risk remains a deferred verified-source gate. Full MarketPilot Score
belongs to Phase 5. Full stop/target/order lifecycle and position sizing belong
to Phase 6. Backtests and activation gates belong to Phase 7.

