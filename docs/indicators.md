# Indicators and SymbolData

Phase 2 adds deterministic offline indicator helpers and a readiness-first
`SymbolData` lifecycle. These contracts have no signals and do not create
strategy signals, scoring, trade recommendations, orders, holdings, or portfolio
state.

## Indicator Families

`config/indicators.yaml` defines:

- EMA8, EMA20, EMA50, EMA200
- RSI14
- MACD 12/26/9
- ROC20 and ROC60
- ATR14
- Average volume 20/50
- Average dollar volume 20/50
- Relative strength windows 20/60
- 52-week high distance

Every helper returns readiness metadata before the value may be consumed.
Missing, invalid, NaN, infinite, stale, or insufficient history rejects future
signal eligibility.

## SymbolData Lifecycle

`SymbolData` owns symbol metadata, data-quality status, indicator readiness,
last update time, and cleanup state. Removed symbols are marked cleaned up and
their indicator references are cleared.

For future LEAN integration, dynamic universes require manual indicator and
consolidator cleanup when securities are removed. This behavior is documented
from official QuantConnect sources in `docs/quantconnect_verification.md`; it is
not executed against the LEAN runtime in Phase 2.

## Deferred Work

Strategy setup labels, scores, entry decisions, exits, orders, Paper deployment,
Telegram alerts, and live deployment remain deferred.
