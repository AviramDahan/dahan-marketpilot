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
- `MARKETPILOT_TELEGRAM_ENABLED=1`

Telegram variables may be configured now, but production delivery verification belongs to Phase 16.1:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

`MARKETPILOT_TELEGRAM_ENABLED=1` is the production-only opt-in that lets the
runtime build a real Telegram notification sink while keeping
`config/notifications.yaml` disabled by default for repository safety.

Phase 16.2 UAT may temporarily enable an explicit operator-gated Paper-only
validation probe when no natural strategy signal appears:

- `MARKETPILOT_RUNTIME_INPUT_KIND=operator_paper_probe`
- `MARKETPILOT_OPERATOR_PAPER_PROBE_ENABLED=1`
- Optional non-secret sizing assumptions:
  `MARKETPILOT_OPERATOR_PAPER_PROBE_SYMBOL`,
  `MARKETPILOT_OPERATOR_PAPER_PROBE_SECTOR`,
  `MARKETPILOT_OPERATOR_PAPER_PROBE_ENTRY_PRICE`,
  `MARKETPILOT_OPERATOR_PAPER_PROBE_STOP_PRICE`, and
  `MARKETPILOT_OPERATOR_PAPER_PROBE_TARGET_PRICE`.

The probe is disabled unless both required flags are present. It reads only the
latest clean QuantConnect sync record, labels evidence as
`operator_gated_paper_probe`, preserves `PAPER_TRADING_ONLY`, and still routes
through scoring, ranking, risk, Paper command delivery, `/live/orders/read`,
dashboard export, and Telegram notification jobs. It must be turned off after
UAT evidence is captured unless another explicit operator-approved Paper
validation window is active.

Phase 16.1 production shared state:

- `REDIS_URL` is injected by Render from `dahan-marketpilot-state` and must not
  be committed or pasted into repository configuration.

## Data And Locks

Phase 16 uses append-only JSONL contracts:

- `data/scheduler_runs.jsonl` for run/job records.
- `data/scheduler_heartbeat.jsonl` for heartbeat records.
- `data/scheduler.lock.json` for the local worker lease lock.
- Existing sync, paper signal, and audit JSONL files remain append-only mirrors.

The lock contract includes `run_id`, `owner`, `acquired_at`, and `expires_at`. Overlapping runs are rejected before any QuantConnect or order path runs.

Phase 16.1 must replace or extend the local file-backed adapter with durable shared storage suitable for both the Render worker and the Render dashboard. Until then, local JSONL files are implementation/test artifacts, not the final shared production transport.

Phase 16.1 extends this with Render Key Value / Valkey shared state:

- The scheduler worker writes the latest dashboard mirror to
  `marketpilot:v1.1:dashboard:latest`.
- The scheduler worker also mirrors the latest scheduler heartbeat into the
  dashboard payload and the dedicated heartbeat key so deployed monitors can
  verify worker freshness without reading Redis directly.
- The dashboard web service reads that mirror using `data_source_kind:
  shared_state`.
- The scheduler can use the same shared state adapter as a deployment-wide
  lease lock, preventing overlap across Render worker restarts.
- Activity records are appended to `marketpilot:v1.1:activity`.
- QuantConnect remains authoritative for Paper portfolio, orders, fills, and
  rejections; shared state is only a display/audit/system-health mirror.
- Phase 16.2 UAT-01 fill evidence must come from sanitized `/live/orders/read`
  authority metadata. Generic `filled` fields or positive fill quantity alone
  are not sufficient.
- UAT-01 preflight requires sanitized reconciliation readiness:
  `sync_status=success`, `reconciliation_clean=true`, `source=quantconnect`, a
  timezone-aware source timestamp, and fresh-enough data for the market gate.
- Open Paper orders do not automatically fail preflight. The readiness check
  blocks only matching validation correlation/tag/idempotency, same symbol/side
  validation duplicates, leftover operator-probe orders, or ambiguous orders
  that cannot be safely distinguished from the planned probe.

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
- `dahan-marketpilot-state` as the shared Render Key Value instance.
- `dahan-marketpilot-heartbeat-health` as a read-only JSON health web service
  exposing only sanitized heartbeat status, dashboard shared-state freshness,
  timestamps, age, worker state, and paper-only/monitor-only flags.

Phase 16.1 proves the deployed dashboard is live, password-protected, reading
shared durable production data, and independent of the local computer only when
sanitized external evidence is captured. Local tests alone are not enough.

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

Run the deployed heartbeat monitor against the read-only health URL:

```powershell
python scripts/check_scheduler_heartbeat.py --heartbeat-url https://dahan-marketpilot-heartbeat-health.onrender.com/heartbeat --max-age-seconds 900
```

The URL-based monitor performs only a GET request and exits nonzero when the
sanitized heartbeat status is missing, stale, or malformed. It must never run
the scheduler, scans, signals, QuantConnect commands, orders, Telegram sends,
or recovery actions.

Run the Phase 16.2 deployed-session observer against both read-only health URLs:

```powershell
python scripts\phase16_2_observe_deployed_session.py --heartbeat-url https://dahan-marketpilot-heartbeat-health.onrender.com/heartbeat --shared-state-url https://dahan-marketpilot-heartbeat-health.onrender.com/dashboard-state --require-heartbeat --require-shared-state --timeout-seconds 30
```

The observer performs GET checks only. It treats missing, unsafe, or stale
shared-state evidence as `blocked_external_not_verified` and must not be used
to trigger scans, scheduler runs, QuantConnect mutations, orders, Telegram
sends, or recovery actions.

Run a dry config check only when the required non-secret IDs are configured:

```powershell
python -m marketpilot.production_runner once --dry-run
```

Run the Phase 16.1 production integration checks:

```powershell
python -m pytest tests/test_shared_state.py tests/test_dashboard_runtime_source.py tests/test_dashboard_render_config.py tests/test_production_runner.py tests/test_phase16_1_golive_scripts.py -q
```

Operator-run external checks:

```powershell
python scripts\verify_render_golive.py --require-dashboard-url --require-shared-state
$env:MARKETPILOT_RUNTIME_TELEGRAM_SMOKE_ENABLED="1"
python scripts\telegram_runtime_smoke.py
```

The Telegram smoke uses the production runtime notification dependency path.
It is disabled unless the explicit smoke env var is set, and it can deliver
only when `MARKETPILOT_TELEGRAM_ENABLED=1`, `TELEGRAM_BOT_TOKEN`, and
`TELEGRAM_CHAT_ID` are present in the environment.
