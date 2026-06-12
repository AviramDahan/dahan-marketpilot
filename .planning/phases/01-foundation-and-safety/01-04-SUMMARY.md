---
phase: 01-foundation-and-safety
plan: "04"
subsystem: shell-surfaces
tags: [quantconnect, lean, streamlit, dashboard, static-safety-tests]
requires:
  - phase: 01-02
    provides: Shared safety constants and package foundation
  - phase: 01-03
    provides: Safe foundational model/test guardrails
provides:
  - Benchmark-only QuantConnect LEAN shell
  - Read-only dashboard shell helpers and app entry point
  - Static safety tests for LEAN and dashboard shells
  - External LEAN compile and local dashboard documentation
affects: [phase-01, quantconnect, dashboard, testing, docs]
tech-stack:
  added: []
  patterns:
    - Test LEAN shell safety statically without importing QuantConnect locally.
    - Keep dashboard state testable through pure helpers.
key-files:
  created:
    - lean/main.py
    - lean/config.json
    - dashboard/__init__.py
    - dashboard/app.py
    - dashboard/models.py
    - dashboard/safety_view.py
    - tests/test_lean_static_safety.py
    - tests/test_dashboard.py
    - .planning/phases/01-foundation-and-safety/01-04-USER-SETUP.md
  modified:
    - docs/setup.md
    - docs/testing.md
key-decisions:
  - "LEAN compile is documented as external verification because the local environment does not have the LEAN CLI installed."
  - "Dashboard tests target pure helpers and static text, avoiding a Streamlit server requirement."
patterns-established:
  - "Shell surfaces must be protected by static tests before strategy or data integration phases."
requirements-completed: [SAF-03, SAF-05, SAF-06, CFG-01, QC-01]
duration: 6 min
completed: 2026-06-12
---

# Phase 01 Plan 04: Non-Trading Shell Surfaces Summary

**Benchmark-only LEAN compile shell and static read-only dashboard shell with safety tests**

## Performance

- **Duration:** 6 min
- **Started:** 2026-06-12T15:59:50Z
- **Completed:** 2026-06-12T16:05:00Z
- **Tasks:** 4
- **Files modified:** 11

## Accomplishments

- Added a minimal `QCAlgorithm` subclass that subscribes only to SPY and QQQ and contains no order/live-trading calls.
- Added a read-only Streamlit dashboard shell using shared disclaimer text and pure safety view helpers.
- Added static tests that fail on forbidden LEAN order/live-trading methods and fake dashboard trading language.
- Documented `lean build` and `streamlit run dashboard/app.py` boundaries without requiring credentials in the repository.

## Task Commits

1. **Tasks 1-4: Non-trading LEAN and dashboard shells** - `889f0fd` (feat)

**Plan metadata:** committed with this summary.

## Files Created/Modified

- `lean/main.py` - Benchmark-only LEAN shell.
- `lean/config.json` - Safe LEAN metadata.
- `dashboard/app.py` - Local Streamlit shell entry point.
- `dashboard/models.py` - Static dashboard safety state.
- `dashboard/safety_view.py` - Pure dashboard safety text helpers.
- `tests/test_lean_static_safety.py` - Static LEAN no-order safety checks.
- `tests/test_dashboard.py` - Dashboard disclaimer/read-only/no-fake-data checks.
- `docs/setup.md` - LEAN and dashboard local setup boundaries.
- `docs/testing.md` - Automated and external verification commands.
- `.planning/phases/01-foundation-and-safety/01-04-USER-SETUP.md` - Optional external LEAN setup checklist.

## Decisions Made

- Did not add Streamlit as a dependency in Phase 1 because automated tests do not need a running Streamlit server.
- Did not run `lean build` because the LEAN CLI is not installed in this environment.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Removed credential wording from LEAN config metadata**
- **Found during:** Task 3 (static LEAN safety tests)
- **Issue:** `lean/config.json` contained the word `credentials` in descriptive text, which violated the no-credential static guard.
- **Fix:** Reworded the description to safe metadata only.
- **Files modified:** `lean/config.json`
- **Verification:** `python -m pytest tests/test_lean_static_safety.py tests/test_dashboard.py` and full `python -m pytest` passed.
- **Committed in:** `889f0fd`

---

**Total deviations:** 1 auto-fixed (1 missing critical).
**Impact on plan:** Strengthened the credential guard without changing scope.

## Issues Encountered

- `lean build` was not run because the LEAN CLI is not available locally. This is recorded as external user setup in `01-04-USER-SETUP.md`.

## User Setup Required

External LEAN compile verification requires manual local setup. See `01-04-USER-SETUP.md`.

## Verification

- `python -m pytest tests/test_lean_static_safety.py tests/test_dashboard.py` passed: 7 tests.
- `python -m pytest` passed: 43 tests.
- Static forbidden-method check over `lean/main.py` returned no matches for order/live-trading APIs.
- `Select-String -Path docs/setup.md, docs/testing.md -Pattern "lean build", "Docker", "streamlit run", "No live data connected"` passed.
- `lean build` was not run: `LEAN_CLI_NOT_AVAILABLE`.

## Next Phase Readiness

All Phase 1 plans now have summaries. Phase 1 is ready for phase-level verification.

---
*Phase: 01-foundation-and-safety*
*Completed: 2026-06-12*
