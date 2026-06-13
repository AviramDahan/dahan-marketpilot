---
phase: 04-volume-breakout
plan: "01"
subsystem: setups
tags: [python, pytest, yaml, volume-breakout, no-look-ahead]

requires:
  - phase: 03-trend-pullback
    provides: shared setup result contracts, completed daily-bar setup timing, and setup-only safety boundaries
provides:
  - Volume Breakout fail-closed configuration contract
  - Volume Breakout rejection vocabulary
  - Current-bar-excluded prior-resistance helper
  - Contract tests for SET-03 no-look-ahead behavior
affects: [phase-04-volume-breakout, phase-05-scoring, phase-07-backtesting]

tech-stack:
  added: []
  patterns:
    - "Parallel setup module using yaml.safe_load and fail-closed safety checks"
    - "Explicit prior-bar slice ending before the signal bar"

key-files:
  created:
    - config/volume_breakout.yaml
    - marketpilot/setups/volume_breakout.py
    - tests/test_volume_breakout_contract.py
  modified:
    - marketpilot/setups/base.py

key-decisions:
  - "Volume Breakout mirrors Trend Pullback as a separate setup module instead of refactoring shared evaluator behavior in this plan."
  - "Prior resistance is calculated with bars[-lookback_bars - 1 : -1], so the signal bar never participates in the resistance window."

patterns-established:
  - "Volume Breakout config must require paper_trading_only: true, completed_daily_bar timing, and disabled intrabar validity."
  - "Volume Breakout contract results return setup evidence only through SetupResult."

requirements-completed: [SET-03]

duration: 6 min
completed: 2026-06-13
---

# Phase 04 Plan 01: Breakout Window and Prior-Resistance Contract Summary

**Volume Breakout contract with fail-closed configuration and current-bar-excluded prior-resistance calculation**

## Performance

- **Duration:** 6 min
- **Started:** 2026-06-13T16:54:23Z
- **Completed:** 2026-06-13T17:00:10Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Added `config/volume_breakout.yaml` with completed daily-bar defaults, 20-bar resistance lookback, 1.5x volume threshold, and disabled trading/deployment behaviors.
- Added Volume Breakout rejection reasons without removing existing Trend Pullback vocabulary.
- Added `marketpilot/setups/volume_breakout.py` with the Volume Breakout contract, input dataclasses, and `calculate_prior_resistance()` using previous completed bars only.
- Added deterministic contract tests proving config safety, rejection vocabulary, setup-only contract output, invalid input rejection, and current-bar high exclusion.

## Task Commits

Each TDD task was committed atomically:

1. **Task 1 RED: Add Volume Breakout config and rejection vocabulary tests** - `51b0c0c` (test)
2. **Task 1 GREEN: Add Volume Breakout config and rejection vocabulary** - `8c9c59c` (feat)
3. **Task 2 RED: Add prior-resistance contract tests** - `f22ceb1` (test)
4. **Task 2 GREEN: Add prior-resistance contract helper** - `53f3f17` (feat)

## Files Created/Modified

- `config/volume_breakout.yaml` - Fail-closed Volume Breakout defaults and disabled behavior flags.
- `marketpilot/setups/base.py` - Added Volume Breakout rejection reasons.
- `marketpilot/setups/volume_breakout.py` - Added setup contract, config loader, input dataclasses, contract result, and prior-resistance helper.
- `tests/test_volume_breakout_contract.py` - Added config, vocabulary, setup-only result, and current-bar exclusion tests.

## Decisions Made

- Followed the plan-specified parallel module shape rather than introducing a broader setup framework.
- Kept `projected_target` and `portfolio_conflict` as future-compatible setup input fields only; this plan does not calculate orders, sizing, portfolio state, stops, targets, or lifecycle behavior.
- Used an explicit `bars[-lookback_bars - 1 : -1]` slice to make current-bar exclusion auditable in code and tests.

## Deviations from Plan

None - plan executed exactly as written.

**Total deviations:** 0 auto-fixed.
**Impact on plan:** No scope changes.

## Issues Encountered

- During the first RED run, the new test file was initially created outside the project root because the patch tool resolved paths from the outer workspace. It was removed before any commit and recreated under `dahan-marketpilot/tests/`; no out-of-repo artifact remains.

## Checks Run

- `python -m pytest tests/test_volume_breakout_contract.py::test_volume_breakout_config_contains_safety_bounded_defaults tests/test_volume_breakout_contract.py::test_rejection_reason_contract_covers_volume_breakout_gates -x` - passed, 2 tests.
- `python -m pytest tests/test_trend_pullback_contract.py::test_rejection_reason_contract_covers_phase_3_hard_rejections -x` - passed, 1 test.
- `python -m pytest tests/test_volume_breakout_contract.py -x` - passed, 6 tests.
- `python -m pytest tests/test_trend_pullback_contract.py tests/test_trend_pullback_safety.py -x` - passed, 7 tests.
- `python -m pytest` - passed, 100 tests.
- Forbidden behavior scan for `marketpilot/setups/volume_breakout.py` found no forbidden trading, deployment, credential, Telegram, or fake backtest strings.

## Known Stubs

None. `portfolio_conflict: bool | None = None` is an explicit future-compatible input required by the plan, not an unwired UI/data stub.

## Threat Flags

None. The new config-to-module and completed-bars-to-helper trust boundaries are covered by the plan threat model and contract tests.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Ready for Plan 04-02. The Volume Breakout evaluator can now consume the config contract, rejection vocabulary, input contract, and current-bar-excluded prior resistance helper without adding trading side effects.

## Self-Check: PASSED

- Created files exist: `config/volume_breakout.yaml`, `marketpilot/setups/volume_breakout.py`, `tests/test_volume_breakout_contract.py`.
- Modified file exists: `marketpilot/setups/base.py`.
- Task commits exist in git: `51b0c0c`, `8c9c59c`, `f22ceb1`, `53f3f17`.
- Plan verification commands passed.

---
*Phase: 04-volume-breakout*
*Completed: 2026-06-13*
