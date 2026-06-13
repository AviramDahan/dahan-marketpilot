---
phase: 04-volume-breakout
plan: "03"
subsystem: setups
tags: [python, pytest, volume-breakout, setup-evidence, safety-docs]

requires:
  - phase: 04-volume-breakout
    provides: Volume Breakout detection, rejection, and numeric evidence from Plan 04-02
provides:
  - Volume Breakout evidence completeness tests
  - Volume Breakout setup-only safety tests
  - Volume Breakout documentation covering contract, evidence, rejection gates, and deferred boundaries
  - Testing and safety documentation synchronized with Phase 4 behavior
affects: [phase-04-volume-breakout, phase-05-scoring, phase-06-risk, phase-07-backtesting]

tech-stack:
  added: []
  patterns:
    - "Evidence completeness tests assert future scoring inputs without implementing scores."
    - "Static setup safety tests scan production setup files for forbidden trading, credential, deployment, and notification behavior."

key-files:
  created:
    - tests/test_volume_breakout_explanations.py
    - tests/test_volume_breakout_safety.py
    - docs/volume_breakout.md
  modified:
    - marketpilot/setups/volume_breakout.py
    - docs/testing.md
    - docs/safety.md

key-decisions:
  - "Volume Breakout evidence is future-consumable by Phase 5, but Phase 4 still emits no score, confidence, ranking, classification, BUY/WATCH/AVOID labels, or trade instruction."
  - "Early rejected Volume Breakout results include core evidence for resistance lookback, breakout buffer, and regime so audit output is not lost before later gates."
  - "Volume Breakout documentation explicitly frames portfolio conflict as a placeholder input until Phase 6, not a calculated portfolio constraint."

patterns-established:
  - "Valid setup explanations use completed daily-bar breakout evidence wording."
  - "Rejected setup explanations include exact `Rejected: {reason.value}.` lines."
  - "Phase setup docs must state deferred scoring, risk, backtest, Telegram, Paper, and Live boundaries."

requirements-completed: [SET-04]

duration: 7 min
completed: 2026-06-13
---

# Phase 04 Plan 03: Volume Breakout Scoring Components, Explanations, and Tests Summary

**Volume Breakout audit evidence, explanations, static safety checks, and setup-only documentation without Phase 5 scoring behavior**

## Performance

- **Duration:** 7 min
- **Started:** 2026-06-13T17:25:52Z
- **Completed:** 2026-06-13T17:32:00Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- Added Volume Breakout explanation tests proving required D-13 evidence names exist for valid results.
- Added rejected-result tests proving explanations include exact rejection reason values and failed evidence remains visible.
- Added setup-only safety tests proving no order, score, classification, Telegram, deployment, credential, or fake backtest behavior appears in production setup files or result attributes.
- Added `docs/volume_breakout.md` covering contract, default config, evidence, fixture design, detection rules, rejection rules, deferred boundaries, and Phase 5/6 handoff notes.
- Updated `docs/testing.md` and `docs/safety.md` with Phase 4 Volume Breakout coverage and paper-only setup boundaries.

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Add failing Volume Breakout explanation tests** - `e17879a` (test)
2. **Task 1 GREEN: Complete Volume Breakout explanation evidence** - `874d8b1` (feat)
3. **Task 2 RED: Add failing Volume Breakout safety tests** - `ce28114` (test)
4. **Task 2 GREEN: Document Volume Breakout safety boundaries** - `9afab1e` (docs)

## Files Created/Modified

- `tests/test_volume_breakout_explanations.py` - Valid/rejected evidence and explanation tests, including no score/confidence/ranking/classification assertions.
- `tests/test_volume_breakout_safety.py` - Static forbidden-behavior scan, setup-result-only behavior test, and documentation synchronization checks.
- `docs/volume_breakout.md` - Volume Breakout setup contract, evidence, rules, rejections, deferred boundaries, and handoff notes.
- `marketpilot/setups/volume_breakout.py` - Added core evidence before early rejected results and clarified valid setup explanation wording.
- `docs/testing.md` - Added Phase 4 Volume Breakout deterministic offline test coverage.
- `docs/safety.md` - Added Volume Breakout setup-only safety boundary.

## Decisions Made

- Kept scoring components as numeric evidence only; no MarketPilot Score, score weights, confidence, rank, classification, or BUY/WATCH/AVOID label was introduced.
- Kept `projected_target` documented as setup evidence for evaluator-calculated proxy math only, not an order target or lifecycle target.
- Kept portfolio conflict documented as an explicit future-compatible placeholder input until Phase 6, not as real portfolio state or constraint logic.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Preserved core evidence on early rejected results**
- **Found during:** Task 1 (Add evidence completeness and explanation tests)
- **Issue:** A rejected result with no bars returned before evidence for `resistance_lookback_bars`, `breakout_buffer_pct`, and `regime` was attached, which weakened D-13 audit coverage.
- **Fix:** Added those core evidence items before the early return path and kept them single-sourced for later rejection paths.
- **Files modified:** `marketpilot/setups/volume_breakout.py`
- **Verification:** `python -m pytest tests/test_volume_breakout_explanations.py -x`; targeted Phase 4 suite; full pytest suite.
- **Committed in:** `874d8b1`

---

**Total deviations:** 1 auto-fixed (1 missing critical).
**Impact on plan:** The auto-fix was required for evidence completeness and did not expand scope beyond setup evidence.

## Issues Encountered

- The first Task 1 patch was initially written by the patch tool to the outer workspace path instead of the repository path. It was removed before any commit and recreated under `dahan-marketpilot/tests/`; no out-of-repo artifact remains.
- Documentation tests initially failed on exact required phrases (`SET-04 hard gates`, `no profitability claims`). The docs were updated to include those phrases as explicit safety wording.

## Checks Run

- `python -m pytest tests/test_volume_breakout_explanations.py -x` - passed, 3 tests.
- `python -m pytest tests/test_volume_breakout_detection.py tests/test_volume_breakout_rejections.py -x` - passed, 11 tests.
- `python -m pytest tests/test_volume_breakout_explanations.py tests/test_volume_breakout_safety.py -x` - passed, 7 tests.
- `python -m pytest tests/test_volume_breakout_contract.py tests/test_volume_breakout_detection.py tests/test_volume_breakout_rejections.py tests/test_volume_breakout_explanations.py tests/test_volume_breakout_safety.py -x` - passed, 24 tests.
- `python -m pytest` - passed, 118 tests.
- `python -m pytest tests/test_volume_breakout_safety.py -x` - passed, 4 tests.
- Static production scan for `MarketOrder`, `SetHoldings`, `Liquidate`, `send_telegram`, `BacktestResult`, `api_key`, `token`, `password`, `BUY`, `WATCH`, and `AVOID` in `marketpilot/setups/base.py` and `marketpilot/setups/volume_breakout.py` found no matches.
- Documentation scan found only negative safety wording for fake backtests, fake portfolio values, credential examples, same-close fills, real order paths, and profitability claims.

## Known Stubs

- `docs/volume_breakout.md` documents `portfolio_conflict` as an explicit future-compatible placeholder input until Phase 6. This is intentional and does not block Phase 4 because real portfolio constraints are out of scope until Phase 6.

## Threat Flags

None. The future scoring trust boundary is covered by tests that forbid total score, confidence, ranking, classification, BUY/WATCH/AVOID labels, orders, sizing, portfolio state, backtests, Telegram, and deployment behavior.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Phase 4 is complete. Volume Breakout now has current-bar-excluded detection, SET-04 rejection evidence, explanation coverage, setup-only safety tests, and documentation ready for Phase 5 scoring and setup comparison work.

## Self-Check: PASSED

- Created files exist: `tests/test_volume_breakout_explanations.py`, `tests/test_volume_breakout_safety.py`, `docs/volume_breakout.md`.
- Modified files exist: `marketpilot/setups/volume_breakout.py`, `docs/testing.md`, `docs/safety.md`.
- Task commits exist in git: `e17879a`, `874d8b1`, `ce28114`, `9afab1e`.
- Plan verification commands passed, including the full project pytest suite.

---
*Phase: 04-volume-breakout*
*Completed: 2026-06-13*
