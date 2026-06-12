# Research: Architecture

## System Boundary

Dahan MarketPilot is a research, backtesting, and simulated Paper Trading system. It is not a brokerage system and must never provide a real-money trading path.

## Authoritative Components

### QuantConnect LEAN

Responsibilities:

- Algorithm engine.
- Historical data processing.
- Dynamic universe selection.
- Indicators and signal evaluation.
- Strategy execution logic.
- Backtesting.
- Portfolio and order modeling.
- Fee, slippage, fill, and risk models.
- Paper Trading compatibility.

### QuantConnect Cloud Paper Trading

Responsibilities:

- Authoritative simulated cash.
- Authoritative simulated holdings and portfolio value.
- Authoritative open positions, orders, and fills.
- Authoritative Paper Trading state and live algorithm status.
- Continuous cloud execution while the user's computer is off.
- Restart behavior and paper algorithm status.

### GitHub

Responsibilities:

- Source control.
- Pull requests and review.
- GitHub Actions.
- Tests and CI.
- LEAN CLI sync workflows.
- Cloud Backtest workflows.
- Report artifacts.
- Configuration and strategy-version history.

### Render And Streamlit

Responsibilities:

- Password-protected read-only dashboard.
- Mobile-friendly presentation of QuantConnect-sourced data.
- Backtest and Paper Trading presentation.
- System health and Telegram health presentation.
- Cached reads with staleness warnings.

Render must never maintain independent active paper portfolio state.

### Telegram

Responsibilities:

- Signal and watch alerts.
- Paper order, fill, stop, target, and close alerts.
- Market regime alerts.
- System and error alerts.
- Daily summaries.

Telegram is not authoritative state and delivery failure must not disable trading safety logic.

## Data Authority Rules

- QuantConnect is authoritative for cash, equity, holdings, positions, orders, fills, paper state, algorithm status, paper performance, and QuantConnect Backtest results.
- Render may cache presentation data but must show staleness and must not mutate paper portfolio state.
- Reports may archive snapshots and analysis, but reports are not active state.
- Excel, CSV, JSON, SQLite, GitHub, and Render local storage must never replace QuantConnect as active paper state.

## Planned Data Flow

1. GitHub stores source, configuration, tests, reports, and documentation.
2. LEAN CLI and GitHub Actions synchronize code to QuantConnect only after relevant validation gates.
3. QuantConnect runs backtests and simulated Paper Trading.
4. QuantConnect/Object Store/API exports or exposes approved paper/backtest/report data.
5. Render Streamlit dashboard reads and caches approved QuantConnect-sourced data.
6. Telegram alerting sends event notifications without becoming authoritative state.

## Architecture Risks

- QuantConnect Cloud API details and permissions must be re-verified during implementation.
- Paper Trading Live Node availability may depend on QuantConnect subscription.
- Object Store sharing, caching, and permissions require careful design.
- Dashboard caching can create stale display risk; staleness indicators are mandatory.
- Notification quotas and failures must not block trading safety logic.
- Backtest-to-paper parity must be tested rather than assumed.
