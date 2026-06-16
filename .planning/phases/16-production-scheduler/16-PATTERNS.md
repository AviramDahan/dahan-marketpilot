# Phase 16 Patterns: Production Scheduler

## Patterns To Reuse

- Single-cycle callable modules: `sync_portfolio` and runtime orchestration should remain callable units. The scheduler owns timing; domain modules do not become daemons.
- Frozen dataclasses and JSON-compatible records: scheduler events, lock leases, run manifests, heartbeat records, and job results should serialize cleanly to JSON/JSONL.
- Append-only audit mirrors: local scheduler state is an audit/display mirror. QuantConnect remains authoritative for Paper portfolio, order, and fill state.
- Atomic JSONL writes: use existing temp-file plus replace patterns for local deterministic tests and audit files.
- Transport-neutral notifications: emit domain events and let Telegram delivery remain an adapter.
- Lazy or optional dependencies: scheduler dependencies must not break existing local tests or imports when Phase 16 is not running.
- Explicit paper gates: `PAPER_TRADING_ONLY` and existing QuantConnect safety checks stay in the scheduler entrypoint, runner, and order-related jobs.

## Phase 16 Boundary Rules

- The scheduler may trigger the complete paper workflow, but it must not introduce new strategy logic.
- The production runner composes existing setup, scoring, risk, order-intent, QuantConnect, dashboard-export, and notification boundaries.
- GitHub Actions is a monitor only. It cannot execute trading, scanning, QuantConnect, or order code.
- Render Background Worker is the autonomous runtime boundary. The local computer must not be part of production operation.
- Durable shared storage, deployed dashboard URL verification, real dashboard production data source, and multi-session burn-in are Phase 16.1 and Phase 16.2.

## Interfaces To Define For Phase 16.1

- `SchedulerStorage`: append run/job/heartbeat/system-health records and read latest status.
- `LockStore`: acquire, renew, release, and inspect a run lock with lease expiration.
- `DashboardExportSink`: publish scheduler/run/order/fill/system-health summaries for the dashboard.
- `NotificationSink`: deliver scheduler/system events through the existing notification-event model.
- `ProductionRuntimeRunner`: run one self-contained pipeline cycle with typed job results and stable correlation ids.

## Testing Patterns

- Use fake clocks for DST, weekend, holiday, early-close, stale-data, and catch-up cases.
- Use fake `LockStore` and `SchedulerStorage` adapters for overlap and retry tests.
- Use fake QuantConnect clients and notification sinks for dependency-aware job graph tests.
- Assert skipped jobs include typed reasons and do not call downstream dependencies.
- Assert duplicate run ids do not create duplicate order intent or duplicate notification delivery.

