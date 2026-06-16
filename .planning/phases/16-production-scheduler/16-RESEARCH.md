# Phase 16 Research: Production Scheduler

## Scope

Phase 16 plans the autonomous scheduler and production runtime runner only. It does not execute Phase 16, close Phase 15, start Phase 16.1, deploy the dashboard, or create a production shared storage backend.

Phase 15's authoritative `/live/orders/read` order/fill/rejection gate remains pending until the next valid US market-hours or next-open observation window.

## Official Reference Findings

### APScheduler

- APScheduler separates schedulers, job stores, executors, and triggers. Phase 16 should keep trigger configuration thin and put MarketPilot market eligibility in testable project code.
- `CronTrigger` supports timezone-aware cron-style triggers, but cron scheduling is wall-clock based. DST transitions can skip or duplicate apparent wall-clock times, so Phase 16 must not rely on raw UTC cron approximations for NYSE market behavior.
- The plan should use `America/New_York` configuration plus a separate NYSE/ET market-session guard that can be tested with fake clocks around DST, weekends, holidays, early closes, and stale data.

Sources:

- https://apscheduler.readthedocs.io/en/3.x/userguide.html
- https://apscheduler.readthedocs.io/en/3.x/modules/triggers/cron.html

### Render

- Render Background Workers are long-running processes suitable for an in-process APScheduler worker.
- Render Cron Jobs are separate scheduled jobs; they can inform operational tradeoffs but Phase 16's boundary is a Background Worker.
- Phase 16 should plan a Render Background Worker service definition and environment contract, while Phase 16.1 later verifies deployed product operation and shared dashboard data.

Sources:

- https://render.com/docs/background-workers
- https://render.com/docs/cronjobs

### GitHub Actions

- GitHub Actions scheduled workflows can run on cron intervals. Phase 16 must keep them monitor-only.
- The monitor may check heartbeat freshness and alert on missed runs. It must never run scans, strategy evaluation, QuantConnect commands, paper order submission, or any order path.

Source:

- https://docs.github.com/actions/using-workflows/workflow-syntax-for-github-actions

## Existing Codebase Findings

- `marketpilot/sync.py` already exposes a single-cycle callable sync boundary and JSONL persistence pattern. Scheduler planning should call this boundary rather than creating a sync loop inside the sync module.
- `marketpilot/runtime_orchestrator.py` holds pure runtime orchestration contracts for setup, scoring, risk, and order intent. The production runner should compose these contracts without duplicating strategy rules.
- `marketpilot/qc_api.py` contains authenticated paper-gated QuantConnect wrappers. Scheduler jobs must continue to use these wrappers and preserve paper-only constraints.
- `marketpilot/dashboard_export.py` and `dashboard/data.py` define existing dashboard export/read boundaries. Phase 16 should define interfaces needed by Phase 16.1 but avoid deploying the production dashboard data source now.
- `marketpilot/notification_events.py` and `marketpilot/telegram.py` define transport-neutral notification events and Telegram delivery. Phase 16 should emit events through the existing domain-event boundary, while Phase 16.1 later wires production delivery.
- `render.yaml` currently defines the dashboard web service. Phase 16 execution will add a background worker definition later; this planning step does not modify deployment files.

## Risks To Address In Plans

- DST, holiday, weekend, early-close, and next-open handling must be explicit and testable.
- Render restarts and local filesystem limitations can break naive file locks. Phase 16 needs a lock interface with a local JSONL/file adapter for tests and a later durable backend contract for Phase 16.1.
- Duplicate runs can duplicate order intent unless run ids, job ids, signal ids, order-intent ids, and notification correlation ids are stable across retries.
- Catch-up must be conservative. Missed cycles may be logged and reconciled, but stale market windows must skip order creation.
- A scheduler failure must not silently stop the product. Worker heartbeat plus GitHub Actions missed-run monitoring are required.
- Telegram and dashboard failures must be isolated from trading safety logic.
- No plan may add real-money trading, dashboard order entry, broker bypass, new strategies, v1.2 scope, or fake external verification.

## Planning Conclusion

Phase 16 should be split into five focused plans across four execution waves:

1. Scheduler clock, APScheduler configuration, and NYSE/ET market-session guard.
2. Production runtime runner and dependency-aware job graph.
3. Durable lock, run ledger, idempotent retries, and catch-up behavior.
4. Heartbeat, system-health records, and GitHub Actions missed-run monitor.
5. Render Background Worker boundary, Phase 16.1 interface contracts, documentation, and regression verification.

