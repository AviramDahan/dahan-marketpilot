# Safety

SIMULATED PAPER TRADING ONLY - NOT FINANCIAL ADVICE

Dahan MarketPilot is simulated Paper Trading only. The central safety rule is
that `PAPER_TRADING_ONLY` must remain true and unsafe configuration must fail
closed.

Disallowed features:

- Real-money trading or instructions for activating it.
- Real broker adapters, real-money credentials, live-money order support, or
  hidden live-trading switches.
- Leverage, margin, short selling, options, futures, cryptocurrency, Forex, or
  unsupported asset classes.
- Manual dashboard order submission or any Render control that modifies orders.
- Fake Backtest results, fake Paper Trading results, fake portfolio values, or
  unverified profitability claims.

QuantConnect is the source of truth for simulated cash, portfolio equity,
holdings, open positions, orders, fills, Paper Trading state, algorithm status,
and QuantConnect Backtest results. Render must remain read-only and must not
maintain authoritative active portfolio state. Telegram is a notification channel only;
Telegram delivery failures must not control or block trading safety logic.

Phase 2 QuantConnect verification is documented in
`docs/quantconnect_verification.md`. That verification may reference LEAN CLI
and Cloud API documentation, but it does not authorize repository credentials,
broker settings, cloud backtest execution, Paper Trading deployment, or live
deployment.

Credentials and secrets must never appear in source files, logs, tests, reports,
planning artifacts, documentation examples, or chat. Use approved secret stores
for QuantConnect, GitHub Actions, Telegram, Render, and dashboard secrets.

Every user-facing dashboard page and generated report must display the exact
disclaimer phrase above.

Volume Breakout remains setup evidence only in Phase 4. It may emit valid or
rejected setup results, numeric evidence, explanations, and rejection reasons,
but it must not contain orders, sizing, portfolio state, backtest results,
Telegram delivery, live or Paper deployment, credentials, fake performance, or
profitability claims.

## Multi-Timeframe Safety

Phase 4.1 does not authorize production orders, Paper Trading, Telegram
delivery, real Backtests, broker adapters, portfolio mutation, stops, targets,
or fake performance artifacts.

Strategy modes are signal-evidence modes only:

- `daily_only`
- `daily_filter_4h_setup`
- `daily_filter_4h_setup_1h_optional`

They are separate from environment modes such as `backtest`, `shadow`, and
`paper`. 1H confirmation is optional support only and cannot independently
create a trade or override failed Daily, invalid 4H, `RISK_OFF`, stale data,
hard rejection, or invalid reward/risk.
