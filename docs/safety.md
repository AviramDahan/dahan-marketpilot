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
