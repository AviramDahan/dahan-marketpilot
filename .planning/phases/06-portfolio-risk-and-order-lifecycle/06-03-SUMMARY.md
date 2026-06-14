---
phase: 06-portfolio-risk-and-order-lifecycle
plan: "03"
requirements-completed: [SCO-04, RISK-03, RISK-06]
completed: 2026-06-14
---

# Phase 06 Plan 03 Summary

Implemented modeled stops, targets, partial exits, trailing policy, and holding
periods.

## Accomplishments

- Added `config/exits.yaml` with structural stop policy, ATR sanity cap, minimum
  2R target, modeled partial exits, trailing stop disabled by default, and max
  holding period.
- Added `marketpilot/exits.py` with exit plan, stop, target, partial exit,
  trailing stop, and holding period domain models.
- Implemented stop selection from structural setup evidence and target
  calculation from risk per share.
- Added tests proving partial exits are model-only, trailing stops are disabled,
  ATR sanity cap rejects excessive stop distance, and `RISK_OFF` does not erase
  existing exit obligations.
- Added `docs/exits.md` and synchronized docs.

## Checks Run

- `python -m pytest tests/test_exit_contract.py tests/test_stops_targets.py tests/test_partial_trailing_holding_period.py tests/test_exit_regime_authority.py tests/test_exit_safety.py -q` - passed, 10 tests.
- `python -m pytest -q` - passed, 215 tests.
- `git diff --check` - passed.

## Deviations

None.

