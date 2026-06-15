# Stack Research: v1.1 QuantConnect Live Paper Trading

**Researched:** 2026-06-15
**Confidence:** HIGH — QuantConnect API is well-documented; scheduling/sync patterns are mature.
**Supersedes:** v1.0 stack research (retained decisions still apply; this adds v1.1 specifics)

## New Dependencies Required

### 1. `requests` (HTTP Client for QC REST API)
- **Version:** 2.32.x (latest stable)
- **Purpose:** QuantConnect Cloud REST API calls — deploy algorithm, submit orders, retrieve fills, check live status, pull portfolio state. The QC REST API is a standard JSON/REST interface at `https://www.quantconnect.com/api/v2/`.
- **Integration:** New `src/qc_api/` module wrapping authenticated endpoints. Called by the orchestrator after signal generation to submit orders and by the reconciliation module to pull fills/portfolio.
- **Alternative considered:** `httpx` — async support is nice but unnecessary here; the pipeline is sequential and `requests` is already the de facto standard. The project doesn't need async HTTP.
- **Note:** QuantConnect does NOT have an official Python SDK for their REST API (their `lean-cli` is for local LEAN, not cloud API calls). Raw `requests` with their userId + apiToken auth header is the documented approach.

### 2. `APScheduler` (Advanced Python Scheduler)
- **Version:** 3.10.x (stable; v4.x is alpha — avoid)
- **Purpose:** Cron-based scheduling of the full pipeline during US market hours. Supports cron expressions, timezone-aware scheduling, job persistence, and graceful shutdown.
- **Integration:** New `src/scheduler/` module. Wraps the existing orchestrator entry point (`run_pipeline()`) with cron triggers. Runs as a long-lived process on the deployment target (Render Background Worker or GitHub Actions scheduled workflow).
- **Alternative considered:**
  - `schedule` — simpler but no timezone support, no cron expressions, no persistence. Insufficient for market-hours scheduling.
  - GitHub Actions `cron` — viable for triggering but limited to 5-min granularity, no state between runs without artifacts, cold-start latency. Better as a backup/fallback than primary scheduler.
  - `celery` + `celery-beat` — massive overkill for a single-pipeline scheduler. Requires Redis/RabbitMQ.
- **Decision:** Use APScheduler 3.x as the in-process scheduler. Deploy as a Render Background Worker (already on Render for dashboard). GitHub Actions cron serves as a health-check/fallback trigger only.

### 3. `pytz` (Timezone Definitions)
- **Version:** 2024.x (latest)
- **Purpose:** US/Eastern timezone handling for market hours logic (open 9:30 ET, close 16:00 ET). APScheduler's cron trigger requires timezone-aware scheduling.
- **Integration:** Used by the scheduler module and market-hours utility. Already an indirect dependency of many libraries but should be explicitly declared.
- **Alternative considered:** `zoneinfo` (stdlib in 3.9+) — viable, but APScheduler 3.x integrates natively with `pytz`. Use `zoneinfo` only if moving to APScheduler 4.x later.

### 4. `tenacity` (Retry Logic)
- **Version:** 9.0.x (latest stable)
- **Purpose:** Resilient retries for QC API calls. Network failures, rate limits (HTTP 429), and transient 5xx errors need exponential backoff without custom retry loops.
- **Integration:** Decorates QC API wrapper methods. Configurable retry count, backoff strategy, and exception filtering.
- **Alternative considered:**
  - `urllib3.util.retry` — works at transport level but less flexible for application-level retry decisions.
  - `backoff` — similar to tenacity but less maintained and fewer features.
  - Manual retry loops — error-prone, inconsistent.

### 5. `deepdiff` (Data Comparison)
- **Version:** 8.x (latest stable)
- **Purpose:** Reconciliation module — detect discrepancies between local audit state and QC cloud state (positions, cash, orders). Provides structured diffs with paths to changed values.
- **Integration:** `src/reconciliation/` module compares local portfolio mirror against QC API response. Discrepancies trigger alerts via existing notification events.
- **Alternative considered:**
  - Manual dict comparison — fragile for nested structures, no structured output.
  - `dictdiffer` — less maintained, fewer features.
  - Custom dataclass comparison — would work for simple cases but `deepdiff` handles edge cases (floats, nested lists, type changes) cleanly.

### 6. `python-dotenv` (Environment Variables)
- **Version:** 1.0.x (latest stable)
- **Purpose:** Load QC API credentials (`QC_USER_ID`, `QC_API_TOKEN`) and scheduler config from `.env` files in local development. Production uses Render/GitHub environment variables directly.
- **Integration:** Loaded at startup in `src/config/`. Already a common pattern in the project's config loading — add if not already present as an explicit dependency.
- **Alternative considered:** Direct `os.environ` only — works in production but painful for local dev. `python-dotenv` is the standard solution.

---

## Libraries Evaluated but NOT Recommended

### `lean-cli` (QuantConnect CLI)
- **Why not:** `lean-cli` is for running LEAN locally and managing local projects. It does NOT provide a Python API for QuantConnect Cloud REST endpoints. The v1.1 features need direct REST API access (deploy, orders, fills, live status), not local LEAN execution.

### `websocket-client` or `websockets`
- **Why not:** QC streaming APIs exist but are unnecessary for swing trading. Polling fills every 5-15 minutes via REST is sufficient for 3-30 day holding periods. WebSockets add complexity (reconnection, heartbeat, state management) with zero benefit for this use case.

### `sqlalchemy` or database upgrade
- **Why not:** The project already uses file-based state (JSON/YAML). Adding a database for sync state is over-engineering at this scale. A simple JSON file tracking last-sync timestamps and known fills is sufficient. Revisit only if reconciliation state grows beyond ~10K records.

### `celery` / `dramatiq` (Task Queues)
- **Why not:** Single pipeline, single schedule. No distributed workers needed. APScheduler handles this cleanly without infrastructure dependencies.

### `asyncio` / `aiohttp`
- **Why not:** The pipeline is sequential (universe → setups → signals → scoring → portfolio → orders → submit to QC → wait). There's no I/O concurrency benefit. Adding async would require rewriting the entire pipeline for zero gain.

---

## Configuration Changes

### New Environment Variables

| Variable | Purpose | Where Set |
|----------|---------|-----------|
| `QC_USER_ID` | QuantConnect account user ID | Render env, GitHub Secrets, `.env` local |
| `QC_API_TOKEN` | QuantConnect API token | Render env, GitHub Secrets, `.env` local |
| `QC_PROJECT_ID` | Target QC project for algorithm deployment | Config YAML or env |
| `QC_LIVE_ALGORITHM_ID` | Running live algorithm ID (set after first deploy) | Config YAML or env |
| `SCHEDULER_ENABLED` | Enable/disable APScheduler (disable in CI) | Render env, `.env` |
| `SCHEDULER_TIMEZONE` | Timezone for cron (default: `US/Eastern`) | Config YAML |
| `SYNC_INTERVAL_MINUTES` | How often to poll QC for fills/state (default: 15) | Config YAML |
| `RECONCILIATION_TOLERANCE` | Max acceptable discrepancy before alert (e.g., $0.01) | Config YAML |

### New Config Sections (in existing YAML config)

```yaml
quantconnect:
  base_url: "https://www.quantconnect.com/api/v2"
  project_id: "${QC_PROJECT_ID}"
  live_algorithm_id: "${QC_LIVE_ALGORITHM_ID}"
  retry:
    max_attempts: 3
    backoff_factor: 2
    retry_on: [429, 500, 502, 503, 504]

scheduler:
  enabled: true
  timezone: "US/Eastern"
  jobs:
    - name: "morning_pipeline"
      cron: "45 9 * * mon-fri"  # 9:45 AM ET (15 min after open)
      function: "run_full_pipeline"
    - name: "fill_sync"
      cron: "*/15 9-16 * * mon-fri"  # Every 15 min during market hours
      function: "sync_fills"
    - name: "eod_reconciliation"
      cron: "30 16 * * mon-fri"  # 4:30 PM ET (30 min after close)
      function: "run_reconciliation"

reconciliation:
  tolerance_usd: 0.01
  alert_on_discrepancy: true
  max_acceptable_position_drift: 1  # shares
```

### Secrets Management
- **Local:** `.env` file (gitignored, already in `.gitignore` pattern)
- **CI/CD:** GitHub Actions Secrets (already used for existing workflows)
- **Production:** Render Environment Variables (already used for dashboard password)
- **No new secret stores needed** — existing infrastructure handles this.

---

## QuantConnect REST API Key Endpoints (v1.1 scope)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/authenticate` | GET | Verify credentials work |
| `/projects/read` | GET | List projects, get project ID |
| `/live/create` | POST | Deploy algorithm to live paper node |
| `/live/read` | GET | Get live algorithm status, portfolio |
| `/live/update/order` | POST | Submit/update orders on live algorithm |
| `/orders/read` | GET | Retrieve order history and fills |
| `/backtests/create` | POST | Launch cloud backtest (MTF comparison) |
| `/backtests/read` | GET | Read backtest results |

**Authentication:** Basic Auth with `userId:apiToken` base64-encoded in `Authorization` header. Simple, well-documented.

---

## New Module Structure

```
src/
├── qc_api/                    # NEW — QuantConnect Cloud API client
│   ├── __init__.py
│   ├── client.py              # Authenticated HTTP client with retries
│   ├── endpoints.py           # Typed endpoint wrappers
│   ├── models.py              # Response dataclasses
│   └── exceptions.py          # QC-specific errors
├── reconciliation/            # NEW — Data sync & reconciliation
│   ├── __init__.py
│   ├── sync.py                # Pull QC state, update local mirror
│   ├── compare.py             # Diff local vs cloud state
│   └── alerts.py              # Discrepancy notification triggers
├── scheduler/                 # NEW — Production scheduling
│   ├── __init__.py
│   ├── engine.py              # APScheduler setup and lifecycle
│   ├── jobs.py                # Job definitions (pipeline, sync, reconcile)
│   └── market_hours.py        # US market calendar awareness
└── backtest/                  # EXTEND — MTF comparison backtesting
    ├── mtf_comparison.py      # NEW — Run daily_only vs MTF, compare results
    └── ...existing...
```

---

## What NOT to Add

| Temptation | Why Skip |
|------------|----------|
| QuantConnect `lean-cli` as dependency | It's for local LEAN, not cloud API. We need REST calls. |
| Database (PostgreSQL, SQLite upgrade) | File-based JSON state is sufficient for ~50 positions max. |
| Redis/RabbitMQ | No message queue needed for single-process scheduler. |
| WebSocket streaming | Swing trading doesn't need real-time fills. 15-min polling is fine. |
| `asyncio` rewrite | Pipeline is sequential. No concurrency benefit. |
| Docker for scheduler | Render Background Worker handles this natively. |
| Separate microservice for API | Single Python process handles everything at this scale. |
| Market calendar library (`exchange_calendars`) | Only need US market hours (9:30-16:00 ET, Mon-Fri). Simple utility + holiday list suffices. |
| OAuth / JWT for QC API | QC uses simple Basic Auth with userId + apiToken. No OAuth flow needed. |

---

## MTF Backtest Comparison Approach

No new libraries needed — uses existing QuantConnect Cloud Backtest API via the new `qc_api` module.

**Pattern:**
1. Upload/compile algorithm with `strategy_mode = "daily_only"` → run cloud backtest → store results
2. Upload/compile algorithm with `strategy_mode = "daily_filter_4h_setup"` → run cloud backtest → store results
3. Compare metrics (Sharpe, drawdown, win rate, trade count) locally using existing Python

**Key insight:** The comparison logic is pure Python (already have the analysis code from v1.0 backtesting). The only new piece is triggering QC cloud backtests via API instead of running locally.

---

## Deployment Topology Change

```
Current (v1.0):
  GitHub Actions → run tests, deploy dashboard
  Render Web Service → Streamlit dashboard (read-only)

New (v1.1):
  GitHub Actions → run tests, deploy dashboard, fallback cron trigger
  Render Web Service → Streamlit dashboard (read-only) [unchanged]
  Render Background Worker → APScheduler process (pipeline + sync + reconcile)
                           → Calls QC REST API
                           → Updates local state files
                           → Triggers Telegram alerts via existing notification system
```

**Cost:** Render Background Worker on Starter plan (~$7/mo) — sufficient for a Python process that wakes on cron, runs pipeline (~2-5 min), then idles.

---

## Installation (new dependencies only)

```bash
pip install requests>=2.32.0 tenacity>=9.0.0 APScheduler>=3.10.0 pytz>=2024.1 deepdiff>=8.0.0 python-dotenv>=1.0.0
```

Add to `requirements.txt` or `pyproject.toml` under `[project.dependencies]`.

---

## Summary

| Category | Decision | Rationale |
|----------|----------|-----------|
| HTTP Client | `requests` 2.32.x | QC REST API is simple JSON; no official SDK exists |
| Retry | `tenacity` 9.x | Resilient API calls without custom retry loops |
| Scheduling | `APScheduler` 3.10.x | Cron + timezone + persistence; avoids Celery overkill |
| Timezone | `pytz` 2024.x | APScheduler 3.x native integration for US/Eastern |
| Reconciliation | `deepdiff` 8.x | Structured comparison of portfolio state dicts |
| Env loading | `python-dotenv` 1.0.x | Local dev credential loading |
| Deployment | Render Background Worker | Long-lived scheduler process; same platform as dashboard |
| Architecture | Single process, file-based state | Matches v1.0 simplicity; no DB/queue/microservice needed |

**Total new dependencies: 5-6 packages** (requests may already be transitive). All are mature, well-maintained, and have no heavy sub-dependencies. No architectural changes to existing v1.0 code — only new modules that call existing pipeline functions.
