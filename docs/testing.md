# Testing

Phase 1 tests are deterministic and offline.

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

LEAN compile verification is external and may require Docker, the LEAN CLI,
`lean login`, `lean init`, and QuantConnect organization access. When available,
use the documented LEAN compile command from the relevant phase summary. Do not
store credentials in this repository.

Phase 1 does not test strategy signals, order lifecycle, portfolio state,
Telegram delivery, Render deployment, QuantConnect Paper Trading, or real
market data access.
