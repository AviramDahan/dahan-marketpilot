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
