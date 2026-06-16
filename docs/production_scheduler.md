# Production Scheduler

Phase 16 adds the autonomous Paper Trading scheduler boundary for Dahan MarketPilot.

This is still a paper-only system. `PAPER_TRADING_ONLY` must remain `True`, QuantConnect remains the source of authority for paper portfolio/order/fill state, and dashboard/Telegram failures must not control trading safety logic.

## Runtime Boundary

The production scheduler runs as a Render Background Worker:

```powershell
python -m marketpilot.production_runner scheduler
```

The worker uses APScheduler for wakeups and MarketPilot's own NYSE/ET guard for trading eligibility. The guard uses `America/New_York` session semantics so DST, weekends, holidays, early closes, and stale catch-up cycles are handled in project code and can be tested offline.

The scheduler executes one dependency-aware cycle:

1. Market-session guard.
2. QuantConnect sync and reconciliation.
3. Runtime evaluation through the existing pure runtime orchestrator.
4. Paper signal delivery through the existing paper order-flow boundary.
5. Authoritative order polling through QuantConnect `/live/orders/read`.
6. Dashboard export interface.
7. Notification event interface.
8. Heartbeat and system-health output.

## Environment Variables

Required in Render, configured as secrets or environment values outside the repository:

- `QUANTCONNECT_USER_ID`
- `QUANTCONNECT_API_TOKEN`
- `QUANTCONNECT_PROJECT_ID` or `QC_PROJECT_ID`
- `QUANTCONNECT_LIVE_DEPLOY_ID` or `QC_DEPLOY_ID`

Operational scheduler values:

- `MARKETPILOT_ENV=paper`
- `MARKETPILOT_DATA_DIR=data`
- `MARKETPILOT_SCHEDULER_CADENCE_MINUTES=5`
- `MARKETPILOT_SCHEDULER_STALE_AFTER_SECONDS=600`
- `MARKETPILOT_SCHEDULER_LOCK_TTL_SECONDS=900`

Telegram variables may be configured now, but production delivery verification belongs to Phase 16.1:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

## Data And Locks

Phase 16 uses append-only JSONL contracts:

- `data/scheduler_runs.jsonl` for run/job records.
- `data/scheduler_heartbeat.jsonl` for heartbeat records.
- `data/scheduler.lock.json` for the local worker lease lock.
- Existing sync, paper signal, and audit JSONL files remain append-only mirrors.

The lock contract includes `run_id`, `owner`, `acquired_at`, and `expires_at`. Overlapping runs are rejected before any QuantConnect or order path runs.

Phase 16.1 must replace or extend the local file-backed adapter with durable shared storage suitable for both the Render worker and the Render dashboard. Until then, local JSONL files are implementation/test artifacts, not the final shared production transport.

## Failure Behavior

- Market closed, weekend, holiday, early close after-hours, and stale catch-up cycles skip order creation.
- Failed upstream jobs skip dependent downstream jobs with typed reasons.
- QuantConnect sync failures prevent runtime/order jobs from running.
- Duplicate runs reuse stable run/idempotency keys and are blocked by the lease.
- Telegram and dashboard export failures are isolated from safety decisions.
- GitHub Actions checks heartbeat freshness only; it must not run scans, strategy evaluation, QuantConnect commands, or order code.

## Render Boundary

`render.yaml` now defines:

- `dahan-marketpilot-dashboard` as the existing Streamlit web service.
- `dahan-marketpilot-scheduler` as the APScheduler Background Worker.

Phase 16 does not prove the deployed dashboard is live, password-protected, or reading shared durable production data. That is Phase 16.1.

## External Gates

Phase 16 does not close Phase 15. The Phase 15 authoritative order/fill/rejection gate remains pending until `/live/orders/read` returns a tagged order, fill, or rejection during a valid US market-hours or next-open observation window.

v1.1 is not complete until Phase 15, Phase 16, Phase 16.1, and Phase 16.2 external gates are verified.

## Local Verification

Run the Phase 16 offline tests:

```powershell
python -m pytest tests/test_scheduler_calendar.py tests/test_scheduler_jobs.py tests/test_scheduler_lock.py tests/test_scheduler_storage.py tests/test_scheduler_health.py tests/test_production_runner.py tests/test_production_scheduler_regression.py -q
```

Run the heartbeat monitor locally:

```powershell
python scripts/check_scheduler_heartbeat.py --heartbeat-path data/scheduler_heartbeat.jsonl --max-age-seconds 900
```

Run a dry config check only when the required non-secret IDs are configured:

```powershell
python -m marketpilot.production_runner once --dry-run
```

