---
phase: 16-production-scheduler
plan: "05"
subsystem: render-worker-docs-regression
tags: [render, docs, regression, phase-16.1-interface]

requires:
  - phase: 16-production-scheduler
    provides: Scheduler runtime, lock, storage, and heartbeat
provides:
  - Render Background Worker blueprint
  - Production scheduler documentation
  - Phase 16 UAT and verification records
  - Full local regression pass
affects: [phase-16-production-scheduler, phase-16.1-production-integration]

key-files:
  created:
    - docs/production_scheduler.md
    - .planning/phases/16-production-scheduler/16-UAT.md
    - .planning/phases/16-production-scheduler/16-VERIFICATION.md
    - tests/test_production_scheduler_regression.py
  modified:
    - render.yaml
    - docs/testing.md
    - tests/test_dashboard_render_config.py

key-decisions:
  - "Render Background Worker is added as `dahan-marketpilot-scheduler`."
  - "Dashboard go-live, durable shared production storage, real Telegram delivery, and password-protected URL verification remain Phase 16.1."
  - "Phase 15 `/live/orders/read` order/fill/rejection authority remains pending."

requirements-completed: [SCHED-01, SCHED-02, SCHED-03, SCHED-04, SCHED-05, SCHED-06, SAFE-03]

commit: e0a07d4c69b08d7fa382c715fb16d060cc0041ab
completed: 2026-06-17T02:35:00+03:00
---

# Phase 16 Plan 05 Summary: Render Worker Boundary, Docs, And Regression Gate

## Accomplishments

- Added Render worker service `dahan-marketpilot-scheduler` with `python -m marketpilot.production_runner scheduler`.
- Documented scheduler runtime, environment variables, lock/data files, failure behavior, Render boundary, and external gates.
- Added Phase 16 UAT and verification artifacts.
- Updated testing docs with the Phase 16 test suite.
- Updated Render blueprint tests to validate both dashboard web service and scheduler worker.

## Verification

- `python -m pytest tests/test_scheduler_calendar.py tests/test_scheduler_jobs.py tests/test_scheduler_lock.py tests/test_scheduler_storage.py tests/test_scheduler_health.py tests/test_production_runner.py tests/test_production_scheduler_regression.py -q` - passed.
- `python -m pytest tests/test_runtime_orchestrator.py tests/test_sync.py tests/test_paper_order_flow.py tests/test_paper_order_flow_e2e.py tests/test_qc_api.py -q` - passed.
- `python -m pytest tests/test_ci_workflows.py tests/test_dashboard_render_config.py -q` - passed.
- `python -m pytest -q` - passed.

## Residual External Gates

- Phase 15 authoritative `/live/orders/read` order/fill/rejection evidence remains pending.
- Phase 16.1 must verify the deployed dashboard, durable shared storage, real Telegram delivery, and operation while the local computer is off.
- Phase 16.2 must verify multi-session burn-in.

## Deviations From Plan

None - plan executed as written.

