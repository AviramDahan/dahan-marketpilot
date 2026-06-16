---
phase: 16-production-scheduler
plan: "04"
subsystem: scheduler-health
tags: [heartbeat, github-actions, monitoring, system-health]

requires:
  - phase: 16-production-scheduler
    provides: Scheduler storage and run lifecycle
provides:
  - Scheduler heartbeat records
  - Monitor-only heartbeat checker script
  - GitHub Actions scheduled heartbeat monitor
affects: [phase-16-production-scheduler, ops-monitoring]

key-files:
  created:
    - marketpilot/scheduler_health.py
    - scripts/check_scheduler_heartbeat.py
    - .github/workflows/marketpilot-heartbeat-monitor.yml
    - tests/test_scheduler_health.py

key-decisions:
  - "GitHub Actions checks heartbeat freshness only."
  - "The monitor workflow must not run scans, signals, QuantConnect commands, or order code."
  - "Workflow actions are pinned to the same full SHAs already approved by CI tests."

requirements-completed: [SCHED-03, SCHED-04, SCHED-05, SAFE-03]

commit: e0a07d4c69b08d7fa382c715fb16d060cc0041ab
completed: 2026-06-17T02:35:00+03:00
---

# Phase 16 Plan 04 Summary: Heartbeat, System Health, And Missed-Run Monitoring

## Accomplishments

- Added heartbeat records and freshness evaluation.
- Added system-health notification event generation for heartbeat checks.
- Added `scripts/check_scheduler_heartbeat.py`, returning nonzero for missing or stale heartbeat.
- Added `.github/workflows/marketpilot-heartbeat-monitor.yml` as monitor-only scheduled workflow with pinned actions.
- Added tests proving missing, fresh, and stale heartbeat behavior.

## Verification

- `python -m pytest tests/test_scheduler_health.py tests/test_ci_workflows.py -q` - passed.
- `python scripts/check_scheduler_heartbeat.py --help` - passed during import/CLI validation.
- `python -m pytest -q` - passed.

## Deviations From Plan

None - plan executed as written.
