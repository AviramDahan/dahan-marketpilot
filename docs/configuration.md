# Configuration

Configuration must fail closed. Any attempt to disable the paper-only boundary,
including `PAPER_TRADING_ONLY`, or add real-money trading capability must be
rejected.

Planned Phase 1 configuration files:

- `config/strategy.yaml`
- `config/risk.yaml`
- `config/notifications.yaml`
- `config/dashboard.yaml`
- `config/environments/backtest.yaml`
- `config/environments/shadow.yaml`
- `config/environments/paper.yaml`

Phase 2 adds:

- `config/universe.yaml`
- `config/indicators.yaml`
- `config/regime.yaml`

Phase 3 adds:

- `config/trend_pullback.yaml`

Phase 4.1 defines and implements `config/strategy.yaml` as the central
strategy-mode contract.
Supported regular strategy modes are exactly:

- `daily_only`
- `daily_filter_4h_setup`
- `daily_filter_4h_setup_1h_optional`

`daily_only` is the default, compatibility mode, and backtesting benchmark.
Strategy mode is not an environment mode; it must not replace or be confused
with `backtest`, `shadow`, or `paper`. Missing, empty, invalid, or unsupported
strategy modes must fail validation.

Required safety and FX seed keys include:

- `paper_trading_only: true`
- `starting_budget_nis`
- `initial_usd_ils_rate`
- `starting_cash_usd`
- `trading_currency: USD`
- `display_currency: NIS`
- `fx_rate_timestamp`
- `fx_rate_source`

The starting USD cash formula is:

```text
starting_cash_usd = starting_budget_nis / initial_usd_ils_rate
```

Later FX-rate changes may update current NIS display values, but must not
rewrite historical USD accounting or historical USD results. Stale FX metadata
must be visible to users.

Unsafe keys such as real broker settings, live-money flags, leverage, margin,
short selling, options, futures, cryptocurrency, Forex, and manual order
controls must fail validation.

## Foundational Models

Phase 1 introduces safe foundational model concepts only:

- `TradingMode`
- `EnvironmentName`
- `CurrencyCode`
- `Money`
- `FxSeed`
- `SafetyStatus`
- `ReadOnlyStatus`
- `ValidationIssue`

These models support configuration, safety display, and validation messages.
Strategy entries, candidate scoring, execution lifecycle, active holdings, and
portfolio state remain deferred to later phases.

## Universe Configuration

`config/universe.yaml` is a Phase 2 offline filtering contract. Required keys
include:

- `paper_trading_only: true`
- `common_equity_only: true`
- `min_price_usd: 5`
- `min_history_bars: 250`
- `min_average_volume_20: 500000`
- `min_average_dollar_volume_20: 20000000`
- `min_market_cap_usd`
- exclusions for ETF, ADR, OTC, preferred shares, warrants, stale data,
  critical missing data, and unsupported securities

Universe configuration does not authorize strategy signals, scoring, orders,
portfolio state, broker settings, or credentials.

## Indicator Configuration

`config/indicators.yaml` defines EMA8/20/50/200, RSI14, MACD 12/26/9, ROC20/60,
ATR14, average volume 20/50, average dollar volume 20/50, relative strength
20/60, and 52-week high distance settings for offline readiness checks.

## Market Regime Configuration

`config/regime.yaml` defines SPY/QQQ benchmark inputs, EMA20/EMA50/EMA200
requirements, slope windows, 20-day and 60-day returns, RISK_ON/RISK_OFF/NEUTRAL
thresholds, and explicit safety boundaries:

- `entry_gate_only: true`
- `liquidate_on_risk_off: false`
- `override_exits: false`

Regime configuration does not add order routing, forced exits, or Telegram
delivery.

## Trend Pullback Configuration

`config/trend_pullback.yaml` defines the Phase 3 Trend Pullback setup contract.
It uses completed daily bars only, defaults to a 2-10 completed-bar pullback
window, checks EMA20/EMA50 proximity, requires recovery above the prior
completed bar high, and keeps reward/risk as a minimal proxy.

The config explicitly disables intrabar validity, order creation, portfolio
sizing, BUY/WATCH/AVOID classifications, backtest result creation, and Telegram
delivery.

## Multi-Timeframe Configuration

Phase 4.1 plans reusable timeframe-aware configuration and models for:

- `completed_daily_bar`
- `completed_four_hour_bar`
- `completed_one_hour_bar`

Daily is mandatory in all modes. 4H becomes the primary setup/signal timeframe
only in MTF modes. 1H is optional confirmation only in
`daily_filter_4h_setup_1h_optional`; missing 1H alone cannot reject a valid
Daily+4H candidate.

The recommended 4H policy is regular-hours, market-open anchoring in
`America/New_York`, with extended hours excluded. Because the US regular session
is 6.5 hours, remaining partial-session bars must be explicitly marked partial
and non-signal by default.

Implementation files:

- `marketpilot/configuration.py` exposes `load_strategy_config()`.
- `marketpilot/timeframes.py` defines `StrategyMode`, `BarTimeframe`,
  `CompletedBar`, `BarSessionMetadata`, and `TimeframeReadiness`.
- `tests/test_strategy_config.py` covers fail-closed strategy-mode loading.

Phase 5 adds:

- `config/relative_strength.yaml`
- `config/scoring.yaml`

`config/relative_strength.yaml` defines the setup-only Relative Strength Leader
contract with SPY hard gates, QQQ evidence-only measurement, structure,
liquidity, ATR, EMA20 extension, and 52-week-high distance thresholds.

`config/scoring.yaml` defines audit-only MarketPilot Score weights, candidate
classification thresholds, explicit not-evaluated later gates, and disabled
Combined Swing readiness settings.
