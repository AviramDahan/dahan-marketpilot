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
