# Render Dashboard

SIMULATED PAPER TRADING ONLY - NOT FINANCIAL ADVICE

Phase 9 deploys the read-only Streamlit dashboard as a Render Python Web
Service. The service starts only the dashboard shell and must not run
QuantConnect deployment commands, Telegram delivery commands, Paper mode
changes, recovery actions, or Object Store write/delete operations.

## Package Checkpoint

The deployment dependency checkpoint approved `streamlit` as the official
Streamlit runtime package. The package is declared conservatively as
`streamlit>=1.51,<2` in `requirements.txt` and `pyproject.toml`.

Phase 16.1 adds `redis>=5.0,<6` for Render Key Value / Valkey shared state.
No additional auth package, Render CLI package, HTTP client package, database
client, or optional `streamlit[auth]` package was added.

## Render Blueprint

`render.yaml` defines a Python Web Service, Background Worker, and shared Render
Key Value instance:

- Build command: `pip install -r requirements.txt && pip install -e .`
- Start command: `streamlit run dashboard/app.py --server.address=0.0.0.0 --server.port=$PORT`
- Python version: `3.11.9`
- Health path: `/`
- Shared state: `dahan-marketpilot-state`, `type: keyvalue`,
  `persistenceMode: journal-snapshot`, `maxmemoryPolicy: noeviction`,
  `ipAllowList: []`.

The start command binds Streamlit to `0.0.0.0` and the `$PORT` value provided by
Render. This keeps the service reachable by Render without exposing any
mutation workflow.

Both dashboard and scheduler receive `REDIS_URL` from the Key Value service's
private `connectionString`. Do not paste a Redis URL into repository files.

## Cache And Stale Data

The dashboard cache is display-only. Cache TTL is 60 seconds. Stale warning
appears around 10 minutes, and a strong stale/error state appears around
30 minutes. Render cold starts or failed source reads must show source/cache
timestamps and stale/error labels when last-good display cache exists, or safe
`not_available`/`error` states when no cache exists.

Streamlit auto-refresh is controlled by `gentle_poll_seconds` and uses
Streamlit's fragment refresh helper when available. It is display-only and must
not trigger scans, QuantConnect commands, Telegram delivery, or order logic.

FX display is also display-only. USD remains the source/accounting currency.
NIS display requires FX rate, source, timestamp, and freshness metadata; missing
or stale FX marks NIS unavailable/stale.

## Runtime Data Source

The Render dashboard uses the same read-only runtime source loader as local
Streamlit. Phase 16.1 sets `config/dashboard.yaml` to
`data_source_kind: shared_state`, which reads the latest dashboard export mirror
from Render Key Value through `REDIS_URL`.

If `REDIS_URL` is absent, or the scheduler has not written
`dashboard:latest`, authenticated users see a clear `not_available` degraded
state. This is intentional; the dashboard must not fabricate data.

Supported Phase 9 runtime source:

- `local_json` - a read-only dashboard export JSON file available to the Render
  service filesystem.

Supported Phase 10.1 runtime source:

- `object_store` - a read-only QuantConnect Object Store dashboard key fetched
  through `ObjectStoreSourceLoader`. Requires an injected writer at runtime.
  External QuantConnect Object Store execution remains `not_run` unless
  operator-configured credentials exist outside repository files. Local/offline
  tests use `FakeObjectStoreWriter` and deterministic fixtures.

Supported Phase 16.1 production source:

- `shared_state` - a read-only Render Key Value mirror written by the scheduler
  worker and read by the dashboard web service. QuantConnect remains
  authoritative; shared state is for display, activity, and system-health
  visibility only.

The source path is configuration, not a credential. It must not contain tokens,
passwords, account IDs, parent-directory traversal, remote URLs, deploy hooks,
or mutation/write semantics. Missing or malformed sources render degraded
dashboard states instead of crashing the Streamlit app.

## Environment Variables

Set these values in Render as environment variables or Blueprint prompts. Store
real values only in Render or another approved external secret store:

- `DASHBOARD_PASSWORD`
- `QUANTCONNECT_USER_ID`
- `QUANTCONNECT_API_TOKEN`
- `QUANTCONNECT_PROJECT_ID`
- `QUANTCONNECT_LIVE_DEPLOY_ID`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `MARKETPILOT_TELEGRAM_ENABLED`

The Render Blueprint marks secret-bearing values with `sync: false`, so the
repository names the required variables without committing their values.

`REDIS_URL` is not a manually entered secret. Render injects it from
`dahan-marketpilot-state` using `fromService.property: connectionString`.

Non-secret runtime variables:

- `PYTHON_VERSION=3.11.9`
- `PYTHONPATH=.`
- `MARKETPILOT_ENV=paper`
- `MARKETPILOT_CONFIG_DIR=config`
- `MARKETPILOT_TELEGRAM_ENABLED=1`

`MARKETPILOT_TELEGRAM_ENABLED=1` is non-secret. It is required in the Render
runtime to activate Telegram delivery after the token and chat ID are stored as
external secrets.

## Deployment Evidence

2026-06-17 Render deployment:

- Blueprint: `dahan-marketpilot-production`
- Dashboard service: `dahan-marketpilot-dashboard`
- Dashboard URL: `https://dahan-marketpilot-dashboard.onrender.com`
- Scheduler worker: `dahan-marketpilot-scheduler`
- Shared state: `dahan-marketpilot-state`
- Public dashboard GET check: HTTP 200 with Streamlit shell returned.

The deployment evidence above proves that the Render dashboard endpoint is
reachable. It does not, by itself, prove shared-state freshness, Telegram
runtime delivery, QuantConnect order authority, or multi-session burn-in.
Those gates require a running QuantConnect Paper deployment and sanitized
runtime evidence.

## Verification

Before deploying, run:

```powershell
python -m pytest tests/test_dashboard_render_config.py tests/test_dashboard_auth.py tests/test_dashboard_read_only.py -q
```

These tests are static and offline. They do not contact Render, QuantConnect,
Telegram, brokers, market data providers, or the internet.

After deployment, run read-only go-live checks from a configured environment:

```powershell
python scripts\verify_render_golive.py --require-dashboard-url --require-shared-state
```

This script does not mutate QuantConnect, Render, Telegram, dashboard data, or
orders. Missing external evidence is reported as blocked/not-run, not passed.

## Dashboard Health Workflow

GitHub Actions `dashboard-health.yml` can run on schedule or by manual dispatch.
It reads `DASHBOARD_HEALTH_URL` from GitHub Actions Secrets and performs a
read-only GET check only when the URL is configured.

If `DASHBOARD_HEALTH_URL` is missing, the workflow writes `not_run` evidence.
The check must not print the URL, POST to Render, call a deploy hook, submit
orders, approve recovery, mutate dashboard state, mutate QuantConnect state, or
send Telegram messages.

Dashboard health evidence is operational context only. QuantConnect remains
authoritative for Paper Trading state, and dashboard cache remains display-only.
