---
phase: 04-volume-breakout
plan: "04"
subsystem: setups
tags: [python, pytest, volume-breakout, stale-data, gap-closure]

requires:
  - phase: 04-volume-breakout
    provides: Volume Breakout evaluator, evidence, and verification gap report from Plans 04-01 through 04-03
provides:
  - Volume Breakout stale-data rejection coverage
  - SymbolData stale readiness wiring in Volume Breakout
  - Updated Volume Breakout and testing documentation for stale readiness
affects: [phase-04-volume-breakout, phase-05-scoring, phase-07-backtesting]

tech-stack:
  added: []
  patterns:
    - "TDD gap closure with RED stale-data test before implementation"
    - "Setup evaluator delegates stale readiness to SymbolData.future_signal_ready(..., stale=...)"

key-files:
  created:
    - .planning/phases/04-volume-breakout/04-04-SUMMARY.md
  modified:
    - marketpilot/setups/volume_breakout.py
    - tests/test_volume_breakout_rejections.py
    - docs/volume_breakout.md
    - docs/testing.md

key-decisions:
  - "Volume Breakout stale data uses the existing SymbolData readiness gate instead of introducing wall-clock timestamp logic."
  - "Stale data rejects with the existing DATA_NOT_READY reason plus symbol_data_stale evidence, preserving setup-only output."

patterns-established:
  - "Gap-closure tests model staleness explicitly through setup input to keep deterministic offline coverage."
  - "Readiness-gate evidence is emitted before early returns so stale rejection remains auditable."

requirements-completed: [SET-04]

duration: 3 min
completed: 2026-06-13
---

# Phase 04 Plan 04: Stale-Data Gap Closure Summary

**Volume Breakout now rejects stale SymbolData readiness through the existing setup evidence gate**

## Performance

- **Duration:** 3 min
- **Started:** 2026-06-13T17:55:29Z
- **Completed:** 2026-06-13T17:58:06Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Added a RED test proving otherwise valid Volume Breakout inputs reject when `symbol_data_stale=True`.
- Added `symbol_data_stale: bool = False` to `VolumeBreakoutInput` and wired it into `SymbolData.future_signal_ready(REQUIRED_INDICATORS, stale=setup_input.symbol_data_stale)`.
- Added `symbol_data_stale` numeric evidence with failed audit status when stale readiness is present.
- Updated Volume Breakout and testing documentation to describe stale SymbolData readiness as a hard data-readiness gate.

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Add stale-data rejection test** - `5f00523` (test)
2. **Task 2 GREEN: Wire stale readiness into Volume Breakout** - `9f8fb11` (feat)

## Files Created/Modified

- `tests/test_volume_breakout_rejections.py` - Added deterministic stale-data rejection coverage.
- `marketpilot/setups/volume_breakout.py` - Added explicit stale input, stale readiness delegation, and audit evidence.
- `docs/volume_breakout.md` - Documented stale SymbolData readiness rejection.
- `docs/testing.md` - Added stale readiness coverage to Phase 4 testing scope.
- `.planning/phases/04-volume-breakout/04-04-SUMMARY.md` - Records this gap-closure execution.

## Decisions Made

- Used the existing `SymbolData.future_signal_ready(..., stale=...)` mechanism rather than deriving staleness from wall-clock time or timestamps in the evaluator.
- Kept stale rejection under `SetupRejectionReason.DATA_NOT_READY` to preserve the existing readiness vocabulary and avoid unnecessary enum expansion.
- Preserved Phase 4 setup-only boundaries: no scoring labels, orders, sizing, portfolio state, backtest output, Telegram behavior, Paper deployment, Live deployment, credentials, or performance claims.

## Deviations from Plan

None - plan executed exactly as written.

**Total deviations:** 0 auto-fixed.
**Impact on plan:** No scope changes.

## Issues Encountered

- The RED run failed as expected before implementation with `TypeError: VolumeBreakoutInput.__init__() got an unexpected keyword argument 'symbol_data_stale'`.

## Checks Run

- `python -m pytest tests/test_volume_breakout_rejections.py::test_rejects_stale_symbol_data_readiness -x` - RED failed before implementation as expected.
- `python -m pytest tests/test_volume_breakout_rejections.py::test_rejects_stale_symbol_data_readiness -x` - passed after implementation, 1 test.
- `python -m pytest tests/test_volume_breakout_contract.py tests/test_volume_breakout_detection.py tests/test_volume_breakout_rejections.py tests/test_volume_breakout_explanations.py tests/test_volume_breakout_safety.py -x` - passed, 25 tests.
- `python -m pytest` - passed, 119 tests.
- Static forbidden-behavior scan of `marketpilot/setups/volume_breakout.py` found no BUY/WATCH/AVOID, order APIs, sizing, portfolio state, backtest result, Telegram, deployment, credential, fake performance, or profitability behavior.

## Known Stubs

- `docs/volume_breakout.md` still documents `portfolio conflict placeholder` as an intentional Phase 6 handoff boundary. This is not a blocking stub for Plan 04-04.

## Threat Flags

None. The setup-input-to-evaluator stale readiness boundary was part of the plan threat model and is covered by deterministic tests.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Phase 4 verification gap is closed. Volume Breakout stale-data rejection is now deterministic, tested, documented, and ready for Phase 5 to consume as setup evidence only.

## Self-Check: PASSED

- Created file exists: `.planning/phases/04-volume-breakout/04-04-SUMMARY.md`.
- Modified files exist: `marketpilot/setups/volume_breakout.py`, `tests/test_volume_breakout_rejections.py`, `docs/volume_breakout.md`, and `docs/testing.md`.
- Task commits exist in git: `5f00523`, `9f8fb11`.
- Plan verification commands passed.

---
*Phase: 04-volume-breakout*
*Completed: 2026-06-13*
