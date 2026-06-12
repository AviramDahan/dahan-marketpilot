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
