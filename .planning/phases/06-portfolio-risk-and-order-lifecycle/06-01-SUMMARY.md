---
phase: 06-portfolio-risk-and-order-lifecycle
plan: "01"
requirements-completed: [SCO-04, RISK-01, RISK-02]
completed: 2026-06-14
---

# Phase 06 Plan 01 Summary

Implemented paper-only portfolio constraints and position sizing.

## Accomplishments

- Added `marketpilot/risk.py` with risk config, portfolio snapshot, sizing
  decision, risk decision, rejection reasons, and portfolio constraint checks.
- Replaced the Phase 1 risk placeholder config with `config/risk.yaml` Phase 6
  defaults: 1% per-trade risk, 10 max positions, 30% sector exposure, 3 new
  daily entries, 15% allocation cap, and minimum 2R.
- Added deterministic tests for config safety, stop-distance sizing,
  allocation/cash handling, sector/count/daily-entry constraints, and static
  safety.
- Added `docs/risk_management.md` and synchronized configuration, testing, and
  safety docs.

## Checks Run

- `python -m pytest tests/test_risk_contract.py tests/test_position_sizing.py tests/test_portfolio_constraints.py tests/test_risk_safety.py -q` - passed, 13 tests.
- `python -m pytest -q` - passed, 215 tests.
- `git diff --check` - passed.

## Deviations

The existing `config/risk.yaml` was a Phase 1 placeholder. It was replaced with
the Phase 6 validated config because the new loader correctly failed closed on
the placeholder.

