# Phase 16 Verification: Production Scheduler

## Automated Verification

Targeted Phase 16 suite:

```powershell
python -m pytest tests/test_scheduler_calendar.py tests/test_scheduler_jobs.py tests/test_scheduler_lock.py tests/test_scheduler_storage.py tests/test_scheduler_health.py tests/test_production_runner.py tests/test_production_scheduler_regression.py -q
```

Expected coverage:

- Market-session guard is `America/New_York` aware and handles DST.
- Weekend, holiday, early close, and stale catch-up cases skip order creation.
- Job graph skips dependent jobs on upstream failure or skip.
- Lock lease prevents overlapping runs and allows expired lease recovery.
- Scheduler JSONL storage persists run/job/missed-cycle records.
- Heartbeat checker returns failure for missing/stale heartbeat and success for fresh heartbeat.
- Production runner can execute signal -> paper command -> order poll with fake dependencies.
- Production runner skips closed-market cycles before QuantConnect calls.

Full regression:

```powershell
python -m pytest -q
```

## Manual/Operational Verification

Monitor-only heartbeat command:

```powershell
python scripts/check_scheduler_heartbeat.py --heartbeat-path data/scheduler_heartbeat.jsonl --max-age-seconds 900
```

Dry runner config check:

```powershell
python -m marketpilot.production_runner once --dry-run
```

Render blueprint review:

- Confirm `dahan-marketpilot-scheduler` exists as a `worker`.
- Confirm start command is `python -m marketpilot.production_runner scheduler`.
- Confirm secrets are `sync: false`.
- Confirm dashboard deployment and shared production storage remain Phase 16.1.

## Verification Boundaries

Phase 16 local tests use fakes for QuantConnect, Telegram, and dashboard sinks. They prove scheduler behavior, not external Paper Trading authority.

Do not mark Phase 15 complete from Phase 16 tests. Phase 15 still requires authoritative `/live/orders/read` evidence during a valid US market-hours or next-open observation window.

