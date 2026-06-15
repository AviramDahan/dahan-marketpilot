# Setup

Dahan MarketPilot starts with a local Python workflow and external setup notes.
Do not paste credentials into chat or repository files.

## Local Python

Use a virtual environment before installing dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

Phase 1 and Phase 2 tests are offline and must not require QuantConnect, Telegram, Render,
broker credentials, internet, or real market access.

## Secrets

Never commit `.env`, Streamlit `secrets.toml`, QuantConnect credentials,
Telegram tokens, Render secrets, dashboard passwords, or GitHub secret values.
Use approved secret stores when later phases require them.

## LEAN Prerequisites

QuantConnect verification contracts are documented in
`docs/quantconnect_verification.md`.

External LEAN verification may require Docker, the LEAN CLI, `lean login`,
`lean init`, and QuantConnect organization access. These are user setup actions.
Keep credentials outside the repository and outside chat.

When prerequisites are available, the external compile check is:

```powershell
lean build
```

Run it only from a properly initialized LEAN workspace. If prerequisites are
missing, record the check as not run. Do not store QuantConnect credentials in
repository files.

## Local Dashboard Preview

The Phase 1 dashboard is a local-only Streamlit shell. It does not connect to
QuantConnect, Render, Telegram, brokers, or live market data.

If Streamlit is installed in the local environment, preview it with:

```powershell
streamlit run dashboard/app.py
```

The shell must display `No live data connected`.

## GitHub Actions Setup

GitHub Actions default CI requires no QuantConnect, Telegram, Render, broker,
internet, or real market access beyond dependency installation. The default
workflow is `tests.yml` and runs deterministic offline pytest.

Optional guarded external workflows use GitHub Actions Secrets. Store values
only in the GitHub repository secret store and never in repository files:

- `QUANTCONNECT_USER_ID`
- `QUANTCONNECT_API_TOKEN`
- `QUANTCONNECT_PROJECT_ID`
- `DASHBOARD_HEALTH_URL`
- `DASHBOARD_PASSWORD`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

`quantconnect.yml` is manual and currently records QuantConnect sync/backtest
as `not_run` until a release operator approves a pinned Lean CLI package and
external execution procedure. `dashboard-health.yml` performs a read-only GET
only when `DASHBOARD_HEALTH_URL` is configured. Missing external prerequisites
must be recorded as `skipped` or `not_run`, not as passed checks.
