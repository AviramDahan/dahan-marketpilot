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

No additional auth package, Render CLI package, HTTP client package, database
client, cache service client, or optional `streamlit[auth]` package was added.

## Render Blueprint

`render.yaml` defines one Python Web Service:

- Build command: `pip install -r requirements.txt`
- Start command: `streamlit run dashboard/app.py --server.address=0.0.0.0 --server.port=$PORT`
- Python version: `3.11.9`
- Health path: `/`

The start command binds Streamlit to `0.0.0.0` and the `$PORT` value provided by
Render. This keeps the service reachable by Render without exposing any
mutation workflow.

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

The Render Blueprint marks secret-bearing values with `sync: false`, so the
repository names the required variables without committing their values.

Non-secret runtime variables:

- `PYTHON_VERSION=3.11.9`
- `MARKETPILOT_ENV=paper`
- `MARKETPILOT_CONFIG_DIR=config`

## Verification

Before deploying, run:

```powershell
python -m pytest tests/test_dashboard_render_config.py tests/test_dashboard_auth.py tests/test_dashboard_read_only.py -q
```

These tests are static and offline. They do not contact Render, QuantConnect,
Telegram, brokers, market data providers, or the internet.
