---
phase: 04-volume-breakout
plan: "02"
subsystem: setups
tags: [python, pytest, volume-breakout, setup-evidence, no-look-ahead]

requires:
  - phase: 04-volume-breakout
    provides: Volume Breakout prior-resistance contract and fail-closed config from Plan 04-01
provides:
  - Close-confirmed Volume Breakout evaluator
  - Volume confirmation and current-bar-excluded detection tests
  - SET-04 rejection gates with numeric evidence
  - Evaluator-calculated reward/risk proxy from projected setup evidence
affects: [phase-04-volume-breakout, phase-05-scoring, phase-06-risk, phase-07-backtesting]

tech-stack:
  added: []
  patterns:
    - "Evidence-first setup evaluator returning SetupResult only"
    - "TDD RED/GREEN commits for detection and rejection gates"

key-files:
  created:
    - tests/test_volume_breakout_detection.py
    - tests/test_volume_breakout_rejections.py
  modified:
    - marketpilot/setups/volume_breakout.py

key-decisions:
  - "Volume Breakout confirms breakouts only with completed daily close above buffered prior resistance."
  - "Reward/risk proxy is calculated inside the evaluator from projected setup evidence, latest close, and prior resistance."
  - "Earnings and portfolio conflict behavior remains explicit-input evidence only; no earnings calendar or real portfolio constraints were introduced."

patterns-established:
  - "Volume Breakout failed and passed gates both emit NumericEvidence before SetupResult is returned."
  - "SET-04 gates remain setup evidence only and do not create orders, stops, sizing, classifications, backtests, Telegram, Paper, or Live behavior."

requirements-completed: [SET-03, SET-04]

duration: 6 min
completed: 2026-06-13
---

# Phase 04 Plan 02: Volume Breakout Detection, Rejection, and Evidence Summary

**Close-confirmed Volume Breakout evaluator with SET-04 hard gates, numeric evidence, and evaluator-calculated reward/risk proxy**

## Performance

- **Duration:** 6 min
- **Started:** 2026-06-13T17:06:05Z
- **Completed:** 2026-06-13T17:12:04Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Added `evaluate_volume_breakout()` with current-bar-excluded prior resistance, buffered close confirmation, volume confirmation, completed daily-bar timing, and setup-only `SetupResult` output.
- Added deterministic detection tests for valid completed-close breakouts, high-only rejection, current-bar high exclusion, and weak volume rejection.
- Added SET-04 rejection gates for readiness, RISK_OFF, blocked future entries, incomplete history, invalid indicators, excessive ATR, excessive EMA20 extension, insufficient dollar volume, weak calculated reward/risk, explicit earnings conflict, and explicit portfolio conflict.
- Added numeric evidence for resistance, buffered resistance, breakout close, volume ratio, EMA20 extension, ATR, average dollar volume, projected setup evidence, reward/risk proxy components, regime, earnings source status, earnings conflict, and portfolio conflict.

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Add failing Volume Breakout detection tests** - `c7a9835` (test)
2. **Task 1 GREEN: Implement close-confirmed detection and volume confirmation** - `09d6a43` (feat)
3. **Task 2 RED: Add failing Volume Breakout rejection tests** - `e3061fe` (test)
4. **Task 2 GREEN: Implement SET-04 rejection gates and evidence** - `773a932` (feat)

## Files Created/Modified

- `marketpilot/setups/volume_breakout.py` - Added `evaluate_volume_breakout()` and supporting validation/evidence helpers.
- `tests/test_volume_breakout_detection.py` - Added completed-close breakout, high-only rejection, current-bar exclusion, and weak volume tests.
- `tests/test_volume_breakout_rejections.py` - Added SET-04 hard-gate, proxy calculation, deferred earnings, and explicit portfolio-conflict tests.

## Decisions Made

- Followed the plan-specified setup-only boundary and reused `SetupResult`, `SetupTiming`, `NumericEvidence`, and `SetupRejectionReason`.
- Kept `projected_target` as setup evidence for proxy math only. It is not an order target, stop, lifecycle target, fill assumption, or trade instruction.
- Kept portfolio conflict as an explicit input gate only; the evaluator does not inspect account, holdings, orders, cash, sector exposure, or position sizing.

## Deviations from Plan

None - plan executed exactly as written.

**Total deviations:** 0 auto-fixed.
**Impact on plan:** No scope changes.

## Issues Encountered

- The first Task 1 test patch was initially written by the patch tool to the outer workspace path instead of the repository path. It was removed before any commit and recreated under `dahan-marketpilot/tests/`; no out-of-repo test artifact remains.

## Checks Run

- `python -m pytest tests/test_volume_breakout_detection.py -x` - passed, 4 tests.
- `python -m pytest tests/test_volume_breakout_rejections.py -x` - RED failed before implementation on missing ATR gate, as expected for TDD.
- `python -m pytest tests/test_volume_breakout_detection.py tests/test_volume_breakout_rejections.py -x` - passed, 11 tests.
- `python -m pytest tests/test_volume_breakout_rejections.py::test_calculates_reward_risk_proxy_from_projected_target_and_resistance -x` - passed, 1 test.
- `python -m pytest tests/test_volume_breakout_contract.py tests/test_trend_pullback_detection.py tests/test_trend_pullback_rejections.py -x` - passed, 18 tests.
- `python -m pytest` - passed, 111 tests.
- Forbidden behavior scan on `marketpilot/setups/volume_breakout.py`, `tests/test_volume_breakout_detection.py`, and `tests/test_volume_breakout_rejections.py` found no order APIs, sizing fields, same-close fill assumptions, fake backtest behavior, Telegram behavior, credentials, deployment behavior, or BUY/WATCH/AVOID classifications.

## Known Stubs

None. `portfolio_conflict: bool | None = None` remains an explicit future-compatible setup input from the plan, not an unwired UI/data stub.

## Threat Flags

None. The setup-input-to-evaluator and readiness/regime-to-validity trust boundaries were covered by planned validation and tests.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Ready for Plan 04-03. Volume Breakout now emits complete detection and rejection evidence that Phase 04 scoring/explanation tests can consume without adding trading side effects.

## Self-Check: PASSED

- Created files exist: `tests/test_volume_breakout_detection.py`, `tests/test_volume_breakout_rejections.py`.
- Modified file exists: `marketpilot/setups/volume_breakout.py`.
- Task commits exist in git: `c7a9835`, `09d6a43`, `e3061fe`, `773a932`.
- Plan verification commands passed.

---
*Phase: 04-volume-breakout*
*Completed: 2026-06-13*
