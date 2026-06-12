# Testing

Phase 1 and Phase 2 tests are deterministic and offline.

Run the local suite with:

```powershell
python -m pytest
```

Tests must not require:

- Internet access.
- QuantConnect credentials.
- Telegram credentials.
- Render credentials.
- Broker credentials.
- Real market data.

Phase 1 automated tests cover repository safety, configuration validation,
FX seed behavior, foundational models, static dashboard safety, and static LEAN
shell safety as those artifacts are introduced.

Current Phase 1 suites:

- `tests/test_safety.py`
- `tests/test_configuration.py`
- `tests/test_models.py`
- `tests/test_project_files.py`
- `tests/test_lean_static_safety.py`
- `tests/test_dashboard.py`
- `tests/test_quantconnect_verification_docs.py`
- `tests/test_data_quality.py`
- `tests/test_universe.py`
- `tests/test_indicators.py`
- `tests/test_symbol_data.py`

QuantConnect verification contracts are documented in
`docs/quantconnect_verification.md`.

LEAN compile verification is external and may require Docker, the LEAN CLI,
`lean login`, `lean init`, and QuantConnect organization access. When available,
run:

```powershell
lean build
```

If LEAN prerequisites are unavailable, record the check as not run. Do not store
credentials in this repository or paste them into chat.

The local dashboard preview is optional and must remain local-only:

```powershell
streamlit run dashboard/app.py
```

The Phase 1 dashboard shell must display `No live data connected` and must not
connect to QuantConnect, Render, Telegram, brokers, or live market data.

Phase 1 does not test strategy signals, order lifecycle, portfolio state,
Telegram delivery, Render deployment, QuantConnect Paper Trading, or real
market data access.

Phase 2 universe tests use offline fixtures only. They verify strict
data-quality rejection, accepted/rejected counts, additions, removals, sector
distribution, and QuantConnect API contract documentation without importing
QuantConnect runtime modules.

Phase 2 indicator and SymbolData tests verify readiness-first behavior,
invalid-data rejection, cleanup for removed symbols, and no strategy signal or
order behavior.
