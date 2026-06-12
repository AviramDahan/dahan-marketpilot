# Configuration

Configuration must fail closed. Any attempt to disable the paper-only boundary
or add real-money trading capability must be rejected.

Planned Phase 1 configuration files:

- `config/strategy.yaml`
- `config/risk.yaml`
- `config/notifications.yaml`
- `config/dashboard.yaml`
- `config/environments/backtest.yaml`
- `config/environments/shadow.yaml`
- `config/environments/paper.yaml`

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
