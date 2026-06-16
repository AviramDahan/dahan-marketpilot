---
phase: 16-production-scheduler
plan: "01"
subsystem: scheduler-calendar
tags: [scheduler, apscheduler, nyse, dst, safety]

requires:
  - phase: 16-production-scheduler
    provides: Phase 16 planning decisions and safety constraints
provides:
  - APScheduler dependency and configuration boundary
  - NYSE/ET DST-aware market-session guard
  - Offline tests for open, closed, holiday, early close, stale, and naive timestamp cases
affects: [phase-16-production-scheduler, render-worker, paper-safety]

key-files:
  created:
    - marketpilot/scheduler_calendar.py
    - marketpilot/scheduler_config.py
    - tests/test_scheduler_calendar.py
  modified:
    - pyproject.toml
    - requirements.txt

key-decisions:
  - "APScheduler owns wakeups; MarketPilot code owns market-session eligibility."
  - "`America/New_York` session semantics are tested independently of a running scheduler."
  - "Stale scheduled cycles skip order creation."

requirements-completed: [SCHED-01, SCHED-05, SAFE-03]

commit: e0a07d4c69b08d7fa382c715fb16d060cc0041ab
completed: 2026-06-17T02:35:00+03:00
---

# Phase 16 Plan 01 Summary: Scheduler Clock And NYSE/ET Guard

## Accomplishments

- Added `APScheduler>=3.10,<4` to runtime dependencies.
- Added `SchedulerConfig`, environment loading, and APScheduler cron kwargs.
- Added `evaluate_market_session()` with DST-aware ET conversion, weekend/holiday handling, early-close handling, and stale-cycle rejection.
- Added deterministic tests proving summer EDT, winter EST, weekend, Juneteenth, early close, stale catch-up, and naive timestamp behavior.

## Verification

- `python -m pytest tests/test_scheduler_calendar.py -q` - passed.
- `python -m pytest -q` - passed after Phase 16 close-out fixes.

## Deviations From Plan

None - plan executed as written.

