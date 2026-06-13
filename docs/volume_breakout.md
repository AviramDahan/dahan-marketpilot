# Volume Breakout

Phase 4 implements Volume Breakout as an independently testable setup module.
It identifies completed daily-bar closes that break above prior resistance with
volume confirmation and records auditable evidence and rejection reasons.

## Contract

The setup uses completed daily bars only. Prior resistance is calculated from a
configured window of previous completed bars and applies current-bar exclusion.
The signal bar can confirm a breakout only with its completed close.

Default configuration in `config/volume_breakout.yaml`:

- `resistance.lookback_bars: 20`
- `resistance.breakout_buffer_pct: 0.25`
- `resistance.require_close_above_buffered_resistance: true`
- `volume.average_volume_period: 20`
- `volume.min_volume_ratio: 1.5`
- `volume.min_dollar_volume: 20000000`
- `risk.max_atr_pct: 8.0`
- `risk.max_ema20_extension_pct: 10.0`
- `risk.min_reward_risk_proxy: 1.5`

## Result Vocabulary

Volume Breakout returns setup results with:

- `valid` or `rejected` status
- numeric evidence
- rejection reasons
- completed daily timing metadata
- human-readable explanation fields

There is no BUY, WATCH, or AVOID output. There are no orders, no portfolio
sizing, no backtest result creation, no Telegram delivery, and no live or Paper
deployment behavior in Phase 4.

## Evidence And Explanations

Volume Breakout evidence includes prior resistance, resistance lookback length,
breakout buffer, buffered resistance, breakout close, average volume, volume
ratio, EMA20 extension percentage, ATR percentage, average dollar volume,
projected setup evidence, reward/risk proxy components, market regime,
symbol data staleness, earnings-source status, earnings-conflict status, and
explicit portfolio conflict input.

These fields are evidence components only. They are not a MarketPilot Score,
not a confidence score, not a rank, not a classification, and not a trade
instruction.

Valid explanations state that the setup is valid on completed daily-bar
breakout evidence. Rejected explanations include `Rejected: {reason}.` lines
using the exact rejection reason values.

## Fixture Design

Tests use deterministic completed daily bar fixtures. Fixtures cover:

- valid close-based breakout confirmation
- current-bar exclusion from prior resistance
- intraday high without completed-close breakout rejection
- weak volume rejection
- RISK_OFF and future-entry blocked rejection
- unready data and invalid indicator rejection
- excessive ATR and excessive EMA20 extension rejection
- insufficient average dollar volume rejection
- weak evaluator-calculated reward/risk proxy rejection
- deferred earnings source evidence and explicit earnings conflict rejection
- explicit portfolio conflict placeholder rejection
- stale SymbolData readiness rejection

## Detection Rules

A valid Volume Breakout requires:

- accepted data quality and ready required indicators
- non-stale SymbolData readiness
- market regime that allows future entries, with RISK_OFF rejected
- completed daily bars only
- prior resistance from previous completed bars only
- completed close above buffered prior resistance
- volume confirmation versus the configured average volume baseline
- ATR percentage at or below the configured maximum
- EMA20 extension at or below the configured maximum
- average dollar volume at or above the configured minimum
- reward/risk proxy at or above the configured minimum

## Rejection Rules

Volume Breakout SET-04 hard gates reject invalid prior resistance, missing or
incomplete completed-bar history, unready or stale data, RISK_OFF or blocked
future entries, unconfirmed completed-close breakout, weak volume confirmation,
excessive EMA20 extension, excessive ATR, insufficient average dollar volume,
weak reward/risk proxy, verified explicit earnings conflict, and explicit
portfolio conflict.

Earnings risk remains deferred until a verified source exists. Phase 4 records
unverified earnings source status as evidence instead of inventing earnings data
or fake rejections.

## Deferred Boundaries

Full MarketPilot Score belongs to Phase 5. Full portfolio constraints, stops,
targets, position sizing, orders, and order lifecycle belong to Phase 6.
Backtests and activation gates belong to Phase 7. Telegram alerts and Paper
Trading deployment belong to later phases.

Phase 4 contains no fake backtest results, no fake portfolio values, no
profitability claims, no credential examples, no same-close fill assumption, and
no real order path. In short, Phase 4 has no profitability claims.

## Handoff Notes

Phase 5 may consume Volume Breakout evidence when implementing full scoring and
classifications. Phase 6 may replace the setup-level reward/risk proxy and
explicit portfolio-conflict placeholder with full portfolio risk and order
lifecycle behavior.

## Phase 4.1 Multi-Timeframe Adaptation

`daily_only` preserves the existing completed daily-bar Volume Breakout
behavior. In MTF modes, Daily provides structure and hard rejection context, 4H
becomes the primary breakout timeframe, and 1H may only support confirmation
that the breakout is holding and not overextended.

1H cannot independently create a trade and cannot override failed Daily,
invalid 4H, `RISK_OFF`, stale data, hard rejection, or invalid reward/risk.
