# Phase 16 Discussion Log: Production Scheduler

**Command:** `/gsd-discuss-phase 16 --all`

**Mode:** All gray areas resolved from explicit user-provided constraints.

## Decisions Captured

- Use APScheduler inside a Render Background Worker boundary.
- Make NYSE/ET market-session eligibility a testable MarketPilot guard, not a raw UTC cron approximation.
- Preserve Phase 15 `/live/orders/read` order/fill/rejection authority as pending.
- Define one production runtime runner boundary that composes existing pure components rather than duplicating strategy logic.
- Require durable lock semantics and idempotent retries/catch-up behavior.
- Make job failure dependency-aware with typed skip reasons.
- Restrict GitHub Actions to heartbeat/missed-run monitoring only.
- Prepare Phase 16 interfaces for Phase 16.1 shared durable storage, dashboard export, Telegram delivery, and system-health data.
- Preserve all paper-only and no-real-money safety gates.
- Do not start Phase 16 execution, Phase 16.1, Phase 16.2, Phase 17, v1.2, or unrelated strategy work.

## Deferred

- Render dashboard go-live, durable production shared storage backend, and real production dashboard data source are Phase 16.1.
- Multi-session burn-in and final operational-readiness report are Phase 16.2.
- MTF backtest validation remains Phase 17.

## Next GSD Step

Run `/gsd-plan-phase 16` as planning-only work.
