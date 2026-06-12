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

## Detection Rules

A valid Trend Pullback requires:

- accepted data quality and ready required indicators
- market regime that allows future entries, with RISK_OFF rejected
- completed daily bars only
- pullback duration inside the configured 2-10 bar window
- EMA20/EMA50 proximity
- no close below EMA50
- broader trend structure with price above EMA200, EMA20 above EMA50, and EMA50
  above EMA200
- recovery close above prior completed bar high
- recovery volume ratio above the configured short average threshold
- ATR percentage at or below the configured risk threshold
- minimal reward/risk proxy at or above the configured threshold

RSI14 and MACD are recorded as supporting evidence only. They are not hard
gates in Phase 3.

## Rejection Rules

Trend Pullback rejects RISK_OFF, unready data, missing or invalid indicators,
EMA50 structure breaks, excessive ATR, weak reward/risk proxy, incomplete
completed daily-bar data, too-short or too-long pullbacks, missing EMA
proximity, broken broader trend, failed recovery trigger, and weak recovery
volume.

Earnings risk remains deferred until a verified source exists. Phase 3 records
that the source is unverified instead of inventing earnings data or fake
rejections.

## Deferred Boundaries

Earnings risk remains a deferred verified-source gate. Full MarketPilot Score
belongs to Phase 5. Full stop/target/order lifecycle and position sizing belong
to Phase 6. Backtests and activation gates belong to Phase 7.
