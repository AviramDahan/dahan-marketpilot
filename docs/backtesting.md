# Backtesting

Backtesting is a validation surface, not a Paper Trading approval switch.
QuantConnect Cloud/LEAN is the official source of truth for real backtest
results. The local Python harness is deterministic and offline; it verifies
contracts such as no-look-ahead, signal/fill separation, same-bar ambiguity,
and conservative execution assumptions.

Default assumptions live in `config/backtesting.yaml`:

- `paper_trading_only: true`
- official authority: `quantconnect_cloud_lean`
- local harness enabled
- conservative next-bar fill model
- next valid open fill timing
- explicit fees and slippage
- Paper submission, broker behavior, external delivery, synthetic results, and
  synthetic portfolio authority disabled

If QuantConnect, Docker, LEAN CLI, cloud login, or organization access is not
available, record the cloud backtest as `not_run` with the prerequisite or
command. Do not invent result artifacts, portfolio values, performance metrics,
or profitability statements.

The default timing rule is completed-bar signal evaluation followed by the next
valid tradable fill. Same-bar entry/exit ambiguity fails closed by being marked
ambiguous. Strategy mode timing must align with the selected signal timeframe:

- `daily_only`: daily completed bars
- `daily_filter_4h_setup`: 4H completed bars
- `daily_filter_4h_setup_1h_optional`: 4H or optional 1H completed bars

Backtest adapters and future Paper Trading adapters must reuse the same
strategy-rule pipeline: setup, scoring, ranking, risk, lifecycle, and exits.
Adapters may translate inputs and outputs, but they must not fork strategy logic.
