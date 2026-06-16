# Phase 16 UAT: Production Scheduler

## Status

Phase 16 implementation is locally verifiable. External deployment and multi-session operation remain downstream gates for Phase 16.1 and Phase 16.2.

Phase 15 `/live/orders/read` order/fill/rejection authority remains pending.

## UAT Checklist

- [x] Scheduler calendar evaluates NYSE/ET regular sessions with DST-aware timestamps.
- [x] Scheduler calendar rejects weekends, holidays, before-open, after-close, and stale scheduled cycles.
- [x] Production runtime runner composes existing sync, runtime, paper signal, order-poll, dashboard export, and notification boundaries.
- [x] Dependency-aware job graph skips downstream jobs when upstream jobs fail or skip.
- [x] Lease lock prevents overlapping runs before QuantConnect or order paths execute.
- [x] Run ledger writes append-only JSONL records with stable run and job idempotency keys.
- [x] Catch-up behavior records stale cycles without creating orders.
- [x] Heartbeat records are written and can be checked by monitor-only tooling.
- [x] GitHub Actions heartbeat workflow is monitor-only.
- [x] Render Background Worker boundary is defined in `render.yaml`.
- [x] `PAPER_TRADING_ONLY` remains required for scheduler startup and production runner execution.
- [x] Dashboard export, Telegram delivery, durable shared storage, and system-health interfaces are ready for Phase 16.1.

## External Gates Not Completed In Phase 16

- [ ] Phase 15 authoritative `/live/orders/read` order/fill/rejection evidence during a valid market-hours or next-open window.
- [ ] Phase 16.1 deployed Render dashboard URL with password protection.
- [ ] Phase 16.1 durable shared data transport between worker and dashboard.
- [ ] Phase 16.1 real Telegram delivery from runtime events.
- [ ] Phase 16.2 multiple consecutive real market-session burn-in.

## Operator Notes

- The local computer is not part of the intended production runtime. Render Background Worker is the scheduler boundary.
- If a scheduler run starts outside a valid market window, it must skip order creation.
- If a deployment must remain running for next-open observation, Phase 15's explicit `--keep-running` requirement still applies to that external smoke path.

