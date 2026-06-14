# Backtest Reports

Backtest reports must distinguish artifact source explicitly:

- `real_quantconnect`
- `fixture`
- `schema`
- `example`
- `not_run`

Only documented real QuantConnect artifacts may carry performance metrics.
Fixtures, schemas, examples, and not-run records may describe structure,
limitations, windows, and assumptions, but they must not present performance
claims.

Required report content:

- full-period window
- year-by-year windows
- in-sample window
- out-of-sample window
- chronological validation status
- sensitivity-analysis status
- SPY primary benchmark and QQQ secondary benchmark context
- fee, slippage, fill, timing, and partial-fill assumptions
- activation-gate outcome
- limitations, unavailable windows, and missing-data warnings
- `SIMULATED PAPER TRADING ONLY - NOT FINANCIAL ADVICE`

Small fixture datasets must mark unavailable windows explicitly. They cannot
silently pretend historical coverage exists.

Reports can be rendered as machine-readable dictionaries or human-readable
Markdown-style text using `marketpilot.backtest_reports`.
