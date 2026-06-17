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

For personal Paper Trading UAT only, deployment can explicitly set
`DASHBOARD_AUTH_ENABLED=false` to expose the read-only dashboard without the
password gate. This must be recorded in UAT evidence and does not enable order
controls, broker mutation, Telegram send controls, recovery actions, or any
real-money behavior.

No dashboard data is rendered before login. Authentication failures are
fail-visible and redacted. The only allowed actions are view, refresh, login,
and logout.

The mobile layout is Overview-first, followed by Positions, Trades, Signals,
Backtests, Strategies, Risk, Notifications, Activity, and System Status. The
layout is operational and compact so the Paper Trading state can be scanned
quickly.

## Page Inventory

The dashboard page registry is:

- Overview
- Positions
- Trades
- Signals
- Backtests
- Strategies
- Risk
- Notifications
- Activity
- System Status

The Overview page is implemented first. It summarizes the paper-only warning,
QuantConnect source state, Paper mode, portfolio status, stale status, open
positions count, recent signal/activity counts, and system warnings. Dedicated
page modules for the remaining page entries are implemented by later Phase 9
plans and must render safe `not_available` states until then.

## Portfolio And Trading Pages

Positions renders QuantConnect-authoritative holdings/open-position state from
typed dashboard DTOs with authority and freshness labels. Missing source data
is shown as `not_configured`, `not_available`, `stale`, or `error`.

Trades renders observational trade, fill, and activity records from typed DTOs.
It labels QuantConnect authority and never provides controls that mutate Paper
Trading state.

Signals renders evidence/classification rows as observational status only.
Backtests renders real/not_run/fixture/unavailable report labels without fake
performance, portfolio fabrication, or profitability claims. Strategies renders
activation, Paper mode, and readiness as status only.

## Risk, Notifications, Activity, And System Pages

Risk renders constraints, exposure, mismatch, exit, and protective recovery
warnings as status only.

Notifications renders Telegram or other delivery outcomes as non-authoritative
status. Missing token, disabled delivery, missing chat target, rejected, and
failed outcomes remain notification status only and do not control safety
logic.

Activity renders recent events/log summaries with source timestamps and visible
empty/error states. It does not turn events into operator workflows.

System Status renders QuantConnect, cache, FX, Telegram, Render, auth, and
configuration health as redacted subsystem diagnostics.

## Cache, Stale Data, And FX Display

Dashboard cache copies are display-only. Every cached display must preserve the
original source timestamp, cache timestamp, freshness status, and authority
label. Manual refresh only clears/retries display reads; it does not mutate
QuantConnect, Paper Trading state, Telegram state, recovery state, or Object
Store data.

Fresh data is under the stale warning threshold. Around 10 minutes, the
dashboard shows a stale warning. Around 30 minutes, the dashboard shows a
strong stale/error state. If a source read fails and a last-good display cache
exists, the dashboard may show it with stale/error labeling. Without cache, the
section must render `not_available` or `error`.

USD remains the source/accounting currency. NIS is display-only and requires an
explicit FX rate, source, timestamp, and freshness status. Missing or stale FX
metadata preserves USD display and marks NIS as unavailable/stale without
inventing a conversion.

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

## Runtime Data Source

The Streamlit app loads dashboard data through `load_dashboard_snapshot()` after
authentication. The default configuration uses `data_source_kind: none`, which
returns an explicit `not_configured` dashboard state with reason
`dashboard_data_source`.

For an approved local/export JSON source, set:

```yaml
dashboard:
  data_source_kind: local_json
  data_source_path: path/to/dashboard-export.json
```

For an approved Object Store source (QuantConnect-authoritative), set:

```yaml
dashboard:
  data_source_kind: object_store
  data_source_path: dashboard/portfolio.json
```

The Object Store source uses `marketpilot.dashboard_export.ObjectStoreSourceLoader`
with an injected writer at runtime. The writer only accepts keys from the
approved `OBJECT_STORE_EXPORT_KEYS` set. QuantConnect remains the authority;
the dashboard never writes, deletes, or mutates Object Store data.

External QuantConnect Object Store reads remain `not_run` unless an operator
configures credentials and executes a real runtime session. Local/offline tests
use `FakeObjectStoreWriter` for deterministic coverage without QuantConnect,
internet, or credential access.

The configured file must be a read-only dashboard export payload using the same
typed DTO contract as the deterministic dashboard fixtures. Missing files render
`not_available`; malformed files render `error`; both paths are safe degraded
states and must not crash the dashboard. Remote URLs, mutation/write-like source
kinds, parent-directory traversal, and secret-like path values are rejected by
configuration validation.

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
