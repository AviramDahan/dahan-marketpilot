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

Phase 1 tests are offline and must not require QuantConnect, Telegram, Render,
broker credentials, internet, or real market access.

## Secrets

Never commit `.env`, Streamlit `secrets.toml`, QuantConnect credentials,
Telegram tokens, Render secrets, dashboard passwords, or GitHub secret values.
Use approved secret stores when later phases require them.

## LEAN Prerequisites

Later QuantConnect verification may require Docker, the LEAN CLI, `lean login`,
`lean init`, and QuantConnect organization access. These are external user
setup actions. Keep credentials outside the repository.
