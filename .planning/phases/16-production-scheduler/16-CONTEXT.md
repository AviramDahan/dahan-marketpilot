# Phase 16 Context: Production Scheduler

## Phase

- Phase: 16 - Production Scheduler
- Goal: Full pipeline runs autonomously on US market schedule with fault tolerance, no overlapping executions, and zero v1.0 test regressions.
- Depends on: Phase 15 Paper Trading & Order Flow. Phase 15's `/live/orders/read` authoritative order/fill/rejection gate remains pending until the next valid US market-hours or next-open observation window.
- Requirements: SCHED-01, SCHED-02, SCHED-03, SCHED-04, SCHED-05, SCHED-06, SAFE-03.
- Mode: Planning-only while Phase 15 waits for market hours.

## Locked Decisions

- D-01: Phase 16 is scheduler and runtime-runner planning for v1.1 only. It must not start implementation until explicitly executed later.
- D-02: Phase 16 must not close, bypass, fake, or mark complete the Phase 15 `/live/orders/read` order/fill/rejection authority gate.
- D-03: Runtime scheduling uses APScheduler inside a Render Background Worker boundary. The worker must not depend on the local computer being on.
- D-04: Scheduling uses NYSE/US market-session semantics in `America/New_York` and must be DST-aware. UTC-only cron approximations are not sufficient for the production runner.
- D-05: APScheduler is the in-process scheduler, but market-window eligibility remains a MarketPilot guard around jobs so DST, holidays, early closes, and stale-data handling can be tested independently.
- D-06: The production runner is a single explicit orchestration boundary that invokes existing pure/callable components. It must not duplicate strategy rules already held in setup, scoring, ranking, risk, reconciliation, or paper-order modules.
- D-07: Job boundaries are dependency-aware: market calendar check -> QuantConnect sync/reconciliation -> strategy/runtime evaluation -> Paper order-intent/delivery gate -> order/fill polling -> dashboard export -> notification emission -> heartbeat.
- D-08: Upstream job failure skips downstream dependent jobs with a typed reason and emits a system-health/notification event. Failure isolation must preserve safety gates.
- D-09: Overlapping runs are forbidden. The scheduler requires a durable lock contract with lease/owner/started_at/expires_at/run_id semantics. The Phase 16 implementation may use a local JSONL/file-backed adapter for tests, but the interface must be ready for Phase 16.1 shared durable storage.
- D-10: Idempotency is required at run, job, signal, order-intent, and notification-delivery boundaries. Retries must reuse stable correlation/run ids and must not create duplicate orders.
- D-11: Catch-up behavior is conservative: missed scheduled cycles can be recorded and reconciled, but stale market data or missed execution windows must skip order creation rather than backfill unsafe orders.
- D-12: GitHub Actions is a monitor only. It may check heartbeat freshness and alert on missed runs, but must never run scans, signals, QC commands, or order paths.
- D-13: Render Background Worker is the Phase 16 deployment boundary. Render Web Service dashboard deployment belongs to Phase 16.1, but Phase 16 must expose the worker interfaces Phase 16.1 needs.
- D-14: Phase 16 must define stable interfaces for Phase 16.1 durable shared storage, dashboard exports, Telegram delivery, and system-health data. It must not require those production backends to be live during Phase 16 planning.
- D-15: `PAPER_TRADING_ONLY`, no-real-money brokerage paths, no dashboard order entry, no secret leakage, and all existing safety gates remain mandatory.
- D-16: Existing tests and prior v1.0/v1.1 behavior must remain passing. New dependencies must be lazy or optional where possible and must not break local deterministic tests.
- D-17: No new strategies, v1.2 work, or unrelated features are allowed.

## The Agent's Discretion

- Choose exact Python module names during planning as long as they preserve the boundaries above and existing code style.
- Use small dataclasses/enums for scheduler events, locks, job results, heartbeat records, and run manifests.
- Prefer JSON/JSONL-compatible data contracts because current sync, audit, dashboard, and tests already use that pattern.
- Prefer deterministic unit tests with fake clocks, fake locks, fake QCApiClient, fake notification transport, and fake storage.

## Deferred Ideas

- Render Web Service dashboard deployment, dashboard password URL verification, and production shared storage backend are Phase 16.1.
- Multi-session external burn-in and final operational-readiness reporting are Phase 16.2.
- MTF backtest automation remains Phase 17.
- New strategies, v1.2, multi-algorithm management, and real-money trading are out of scope.

## Code Context

- `marketpilot/runtime_orchestrator.py` - pure runtime orchestration contracts and setup/risk/order-intent output.
- `marketpilot/sync.py` - single-cycle QuantConnect portfolio sync callable and JSONL persistence pattern.
- `marketpilot/qc_api.py` - authenticated paper-gated QuantConnect API wrappers.
- `marketpilot/dashboard_export.py` - dashboard export payload and Object Store source patterns.
- `marketpilot/notification_events.py` and `marketpilot/telegram.py` - transport-neutral notification events and Telegram adapter.
- `dashboard/data.py` - dashboard source boundary, approved read-only endpoints, Object Store export keys.
- `render.yaml` - existing Render web service blueprint; Phase 16 plans a background worker addition later, not now.
- `.github/workflows` does not yet contain the Phase 16 heartbeat monitor.

## Canonical References

- `.planning/REQUIREMENTS.md` - SCHED-01..06, SAFE-03, SAFE-06, PROD/UAT downstream readiness constraints.
- `.planning/ROADMAP.md` - Phase 16 boundary and v1.1 completion gate.
- `.planning/phases/15-paper-trading-order-flow/15-11-SUMMARY.md` - Phase 15 current external gate and auto-stop state.
- `.planning/phases/14-data-sync-dashboard-integration/14-CONTEXT.md` - sync callable and dashboard freshness decisions.
- `.planning/phases/15-paper-trading-order-flow/15-CONTEXT.md` - Paper order authority and safety decisions.
- `marketpilot/runtime_orchestrator.py`
- `marketpilot/sync.py`
- `marketpilot/dashboard_export.py`
- `marketpilot/notification_events.py`
- `marketpilot/telegram.py`
- `dashboard/data.py`
- `render.yaml`
- APScheduler official docs: `https://apscheduler.readthedocs.io/en/3.x/userguide.html`, `https://apscheduler.readthedocs.io/en/3.x/modules/triggers/cron.html`
- Render official docs: `https://render.com/docs/background-workers`, `https://render.com/docs/cronjobs`
- GitHub Actions official docs: `https://docs.github.com/actions/using-workflows/workflow-syntax-for-github-actions`

## Source Audit

| Source | ID | Feature or constraint | Phase 16 handling |
|--------|----|-----------------------|-------------------|
| ROADMAP | SCHED goal | Autonomous US market schedule with fault tolerance | Covered by scheduler, runner, lock, heartbeat plans |
| REQ | SCHED-01 | APScheduler on US market schedule | Locked to APScheduler + NYSE/ET guard |
| REQ | SCHED-02 | No overlapping runs; idempotent execution | Durable lock + idempotency run ledger |
| REQ | SCHED-03 | GitHub Actions heartbeat monitor only | Monitor-only plan, no trading action |
| REQ | SCHED-04 | Dependency-aware graph | Job graph result and skip semantics |
| REQ | SCHED-05 | Self-contained/catch-up/audit | Run manifest + heartbeat + JSONL audit |
| REQ | SCHED-06 | No new database; JSONL/QC authority | Local adapter now, durable storage interface for 16.1 |
| REQ | SAFE-03 | Existing tests pass unchanged | Dedicated regression and lazy import plan |
| USER | Planning-only | Do not execute Phase 16 yet | Only context/research/plan artifacts created |
| USER | Phase 15 pending | Do not close `/live/orders/read` gate | Explicit dependency and completion gate |
