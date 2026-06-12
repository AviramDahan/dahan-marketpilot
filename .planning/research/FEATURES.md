# Research: Features

## Table Stakes

### Safety And Compliance

- Central paper-only guard.
- Unsafe configuration rejection.
- No real broker path.
- No leverage, margin, short selling, options, futures, crypto, Forex, or intraday primary signals.
- Mandatory disclaimer on dashboard pages and reports.
- Credential and secret masking.

### QuantConnect Core

- Minimal non-trading `QCAlgorithm` foundation.
- Daily data handling.
- Dynamic US equity universe.
- Benchmark symbols SPY and QQQ.
- Indicator readiness and cleanup.
- Market regime calculation.
- Backtesting and Paper Trading compatibility.
- Restart and reconciliation behavior.

### Strategy Research

- Trend Pullback setup.
- Volume Breakout setup.
- Relative Strength Leader setup.
- Unified scoring and explanation layer.
- Hard rejections for invalid data, stale data, bad reward/risk, and unsafe portfolio constraints.
- Exact same strategy logic for Backtesting and Paper Trading.

### Validation

- No-look-ahead tests.
- Same-bar ambiguity handling.
- Slippage and fee assumptions.
- Year-by-year reporting.
- In-Sample and Out-of-Sample validation.
- Walk-Forward or equivalent chronological validation.
- Sensitivity analysis.
- Activation gates before Paper Trading.

### Notifications

- Signal, watch, paper order, fill, stop, target, close, regime, system, and daily summary alerts.
- Duplicate suppression and rate limiting.
- Fake transports for tests.
- Telegram failures isolated from trading safety.

### Dashboard

- Password-protected mobile Streamlit interface on Render.
- Read-only QuantConnect-sourced portfolio, orders, signals, backtests, alerts, and system health.
- USD and NIS display with stale FX warning.
- Caching and stale-data handling.
- Secret masking and user-safe error presentation.

### Operations

- GitHub Actions.
- QuantConnect sync/backtest workflows.
- Weekly validation.
- Dashboard health checks.
- Report artifacts.
- Incident and recovery documentation.
- Licensing, NOTICE, third-party notices, and disclaimer.

## Explicitly Deferred Or Excluded

- Real-money trading.
- Real broker integrations.
- Manual order controls.
- AI-driven unauditable decisions.
- Intraday primary signal generation.
- Profitability claims.
- Production strategy implementation during initialization.

## Feature Dependencies

- Phase 1 must establish safety, configuration, licensing, and test foundation before any trading logic.
- Universe and market regime must exist before setup signals.
- Individual setups must be implemented and validated before Combined Swing.
- Risk and order lifecycle must exist before Paper Trading.
- Backtesting validation gates must exist before Paper Trading activation.
- Dashboard must remain read-only and use QuantConnect-sourced state.
