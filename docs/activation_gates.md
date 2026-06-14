# Activation Gates

Activation state is typed and auditable:

- `unvalidated`
- `validation_failed`
- `validation_passed`
- `approved_for_shadow`
- `approved_for_limited_paper`
- `approved_for_full_paper`

The repository default remains not approved for Paper Trading. A `not_run`
backtest, fixture, schema, or example cannot make Paper eligible.

Gate evaluation blocks activation unless all required checks pass:

- real documented QuantConnect results
- no-look-ahead validation
- no synthetic result artifacts
- complete coverage
- SPY benchmark comparison available
- risk checks passed
- fees, slippage, fill, timing, and partial-fill assumptions present
- report completeness

Passing validation alone returns `validation_passed`, which is still not Paper
eligible. Paper eligibility requires an explicit approved Paper state after all
gates pass.

## Paper Mode Mapping

Phase 8 maps activation state to Paper Trading mode with fail-closed defaults:

- `unvalidated`, `validation_failed`, and `validation_passed` map to
  `inactive` and cannot submit Paper orders.
- `approved_for_shadow` maps to `shadow`, which allows signal and Telegram
  previews only.
- `approved_for_limited_paper` maps to `limited_paper`, which can be eligible
  for capped QuantConnect Paper orders after Phase 6 risk and exit checks.
- `approved_for_full_paper` maps to `full_paper`, which can use the configured
  Phase 6 risk limits after Phase 6 checks.

Limited Paper is intentionally stricter than Phase 6 defaults: 0.5% per-trade
risk, at most 3 open Paper positions, and at most 1 new Paper entry per trading
day. Allocation, sector exposure, reward/risk, stop, and target checks remain
required in every Paper-order-eligible mode.

Stale, unavailable, fixture-only, example-only, not-run, or Phase-7-inconsistent
validation evidence fails closed to `inactive`; it never creates Paper order
eligibility.
