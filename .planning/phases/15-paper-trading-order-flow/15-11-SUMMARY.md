---
phase: 15-paper-trading-order-flow
plan: "11"
subsystem: quantconnect-paper-smoke-safety
tags: [quantconnect, paper-trading, smoke-tests, deployment-safety, gap-closure]

requires:
  - phase: 15-paper-trading-order-flow
    provides: "Phase 15-10 Object Store receipt and Submitted event evidence"
provides:
  - "Default auto-stop for temporary Paper deployments created by Object Store smoke"
  - "Explicit `--keep-running` override for operator-approved next-open observation"
  - "Documented order-authority follow-up gate"
affects: [phase-15-paper-trading-order-flow, quantconnect-paper-operations]

key-files:
  created:
    - .planning/phases/15-paper-trading-order-flow/15-11-SUMMARY.md
  modified:
    - scripts/qc_object_store_signal_smoke.py
    - tests/test_qc_api.py
    - docs/paper_trading_order_flow.md
    - docs/testing.md
    - .planning/phases/15-paper-trading-order-flow/15-UAT.md
    - .planning/phases/15-paper-trading-order-flow/15-VERIFICATION.md

key-decisions:
  - "Object Store fallback smokes stop temporary Paper deployments by default."
  - "`--keep-running` is required for next-open order/fill observation."
  - "Receipt/Submitted log evidence is not `/live/orders/read` or fill authority."

requirements-completed: []

duration: 15min
completed: 2026-06-16T22:38:00Z
---

# Phase 15 Plan 11: Paper Smoke Auto-Stop Summary

**Temporary Paper deployments now stop automatically after Object Store smokes.**

## Accomplishments

- Added `stop_after_deploy` to `run_smoke()`, defaulting to `True`.
- Added CLI flag `--keep-running` for explicit operator-approved long
  observation windows.
- Added result fields:
  - `stop_after_deploy`
  - `stop_attempted`
  - `stop_success`
- Added tests proving:
  - default full smoke stops the created deployment;
  - `stop_after_deploy=False` skips auto-stop.

## External Auto-Stop Check

Status: `object_store_written_no_algorithm_receipt_observed` for the short
auto-stop check, with stop verified.

Sanitized external evidence:

- Project: `32900381`.
- Organization: `ed947707222a7b9aeb5de9d0974e5994`.
- Key:
  `32900381/marketpilot/signals/object-store-smoke-20260616223659.json`.
- Compile:
  `afa175c1bfd2ec3fbe9761e785d36564-3a1e17366ee80c002632e087f0b2adc5`,
  `BuildSuccess`.
- Paper deploy: `L-d54a7a1b3ffb938b43db9cab1a0f2560`.
- The one-poll smoke was intentionally too short to prove receipt.
- Object cleanup returned `true`.
- `stop_attempted=true`.
- `stop_success=true`.

## Verification

- `python -m pytest tests/test_qc_api.py -q` - passed.
- Dry-run:
  `python scripts\qc_object_store_signal_smoke.py --dry-run --skip-deploy` -
  passed.
- Credentialed short smoke verified external auto-stop.

## Residual Risk

- `/live/orders/read` order/fill/rejection evidence remains pending.
- A future market-hours or next-open observation must pass `--keep-running`
  explicitly if the deployment needs to remain active beyond the smoke window.

## Next Step

Run the next external order-authority gate during US market hours or with an
operator-approved next-open observation window. The expected evidence is a
tagged order, fill, or rejection from `/live/orders/read`, not just live logs.

---
*Phase: 15-paper-trading-order-flow*
*Completed: auto-stop safety for Object Store Paper smokes on 2026-06-16*
