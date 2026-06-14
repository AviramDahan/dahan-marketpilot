# Dashboard

SIMULATED PAPER TRADING ONLY - NOT FINANCIAL ADVICE

Phase 9 adds a read-only Render Streamlit dashboard for monitoring the Paper
Trading system. The dashboard is display-only. It must not submit orders,
cancel orders, edit QuantConnect projects, change Paper Trading modes, approve
recovery, send Telegram messages, or mutate QuantConnect Object Store data.

## Data Authority

QuantConnect is the dashboard authority for Paper Trading cash, equity,
holdings, orders, fills, algorithm status, deployment status, and dashboard
exports. Render, Streamlit session state, local files, cache entries, and
deterministic fixtures are display-only context.

Every dashboard section must expose source metadata:

- `source`
- `source_timestamp`
- `cache_timestamp`
- `freshness_status`
- `authority`
- optional `fixture_label`
- optional degraded-state reasons

The dashboard must show `not_configured`, `not_available`, `stale`, or `error`
when source data is missing or unclear. It must not invent holdings, portfolio
totals, backtest results, strategy activity, notifications, or system health.

## Authentication And Navigation

The dashboard uses a single strong password loaded from the `DASHBOARD_PASSWORD`
environment variable. Repository configuration may name this environment
variable, but it must never store the raw dashboard password.

No dashboard data is rendered before login. Authentication failures are
fail-visible and redacted. The only allowed actions are view, refresh, login,
and logout.

The mobile layout is Overview-first, followed by Positions, Trades, Signals,
Backtests, Strategies, Risk, Notifications, Activity, and System. The layout is
operational and compact so the Paper Trading state can be scanned quickly.

## Approved QuantConnect Read Paths

The approved production QuantConnect Cloud API read paths are:

- `/live/list`
- `/live/portfolio/read`
- `/live/orders/read`
- `/live/insights/read`
- `/live/logs/read`
- `/object/list`
- `/object/properties`
- `/object/get`

The approved Object Store dashboard export keys are:

- `dashboard/portfolio.json`
- `dashboard/positions.json`
- `dashboard/trades.json`
- `dashboard/signals.json`
- `dashboard/backtests.json`
- `dashboard/strategies.json`
- `dashboard/risk.json`
- `dashboard/notifications.json`
- `dashboard/activity.json`
- `dashboard/system.json`

Mutation paths are forbidden for the dashboard boundary, including live create,
update, stop, order create/cancel/update, project update, backtest create, and
Object Store set/delete paths.

## Fixtures

Deterministic fixtures are test-only and must carry an explicit fixture label.
Fixtures are test-only display inputs and must never be labeled as live
QuantConnect state. Offline dashboard tests must not require QuantConnect,
Telegram, Render, internet access, broker credentials, market data, or real
secrets.

## Secret Masking

Dashboard diagnostics must redact secret-like keys and values before rendering
or logging. This includes token, password, credential, api key, user id,
account, secret, and chat-like values. Repository files may name required
environment variables, but must not contain credential values.
