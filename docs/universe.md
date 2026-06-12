# Universe Foundation

Phase 2 introduces a strict, auditable universe and data-quality contract. It
has no signals and does not introduce strategy signals, scoring, orders,
portfolio state, Paper deployment, or live deployment.

## Local Behavior

`config/universe.yaml` defines the offline thresholds used by
`marketpilot.universe`:

- `min_price_usd`
- `min_history_bars`
- `min_average_volume_20`
- `min_average_dollar_volume_20`
- `min_market_cap_usd`
- `common_equity_only`
- exclusions for ETF, ADR, OTC, preferred shares, warrants, stale data,
  critical missing data, and unsupported securities

`UniverseCandidate` records are evaluated into `UniverseDecision` records.
`UniverseSnapshot` records accepted symbols, rejected symbols, rejection
reasons, additions, removals, counts, update time, and sector distribution when
sector data is present.

The implementation fails closed: invalid, stale, missing, unsupported, or
insufficient data is rejected with explicit reason codes. The system never
silently falls back to a tiny hand-written list.

## QuantConnect Boundary

Current official QuantConnect documentation uses `add_universe` with
`Fundamental` records for fundamental universes. Legacy coarse/fine assumptions
must be treated with caution. `add_equity` remains appropriate for explicit
benchmark subscriptions such as SPY and QQQ.

Local tests do not import QuantConnect runtime modules. The integration contract
is recorded in `marketpilot/qc_contracts.py` and
`docs/quantconnect_verification.md`.

## Deferred Work

Later phases may consume accepted universe records only after readiness checks.
Strategy setup, signal generation, scoring, order lifecycle, Paper deployment,
and live deployment remain deferred.
