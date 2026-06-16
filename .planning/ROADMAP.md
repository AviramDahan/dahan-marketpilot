# Roadmap: Dahan MarketPilot

## Milestones

- ✅ **v1.0 Paper Trading Research Platform** — Phases 1-10.1 (shipped 2026-06-15)
- 🔄 **v1.1 QuantConnect Live Paper Trading** — Phases 13-17 (active)

## Phases

<details>
<summary>✅ v1.0 Paper Trading Research Platform (12 phases, 53 plans) — SHIPPED 2026-06-15</summary>

- [x] Phase 1: Foundation and Safety (4/4 plans) — completed 2026-06-12
- [x] Phase 2: QuantConnect Foundation and Universe (4/4 plans) — completed 2026-06-13
- [x] Phase 3: Trend Pullback (3/3 plans) — completed 2026-06-13
- [x] Phase 4: Volume Breakout (4/4 plans) — completed 2026-06-13
- [x] Phase 4.1: Multi-Timeframe Signal Foundation (4/4 plans) — completed 2026-06-14
- [x] Phase 5: Relative Strength and Unified Scoring (3/3 plans) — completed 2026-06-14
- [x] Phase 6: Portfolio Risk and Order Lifecycle (5/5 plans) — completed 2026-06-14
- [x] Phase 7: Backtesting and Validation (5/5 plans) — completed 2026-06-14
- [x] Phase 8: QuantConnect Paper Trading and Telegram (4/4 plans) — completed 2026-06-14
- [x] Phase 9: Render Dashboard (8/8 plans) — completed 2026-06-15
- [x] Phase 10: CI/CD, Security and Release (4/4 plans) — completed 2026-06-15
- [x] Phase 10.1: Close gap: runtime orchestrator (5/5 plans) — completed 2026-06-15

Full details archived: [milestones/v1.0-ROADMAP.md](milestones/v1.0-ROADMAP.md)

</details>

### v1.1 QuantConnect Live Paper Trading

- [x] **Phase 13: QC API Client & Safety Foundation** — Authenticated API client with defense-in-depth paper-only safety (completed 2026-06-15)
- [ ] **Phase 14: Data Sync & Dashboard Integration** — Reliable portfolio sync from QC with freshness-aware dashboard display
- [ ] **Phase 15: Paper Trading & Order Flow** — Signal delivery to live algorithm with full fill tracking and audit trail
- [ ] **Phase 16: Production Scheduler** — Autonomous market-hours pipeline execution with fault tolerance
- [ ] **Phase 17: MTF Backtest Validation** — Automated comparative backtesting with regression detection

## Overview

| Phase | Name | Goal | Requirements | Plans (est.) |
|-------|------|------|--------------|--------------|
| 13 | QC API Client & Safety Foundation | 4/4 | Complete   | 2026-06-15 |
| 14 | Data Sync & Dashboard Integration | 1/4 | In Progress|  |
| 15 | Paper Trading & Order Flow | Deliver signals to running algorithm; track fills with audit traceability | PTD-01..05, FT-01..04, SAFE-05 | 5 |
| 16 | Production Scheduler | Run pipeline autonomously on NYSE schedule with fault tolerance | SCHED-01..06, SAFE-03 | 4 |
| 17 | MTF Backtest Validation | Validate strategy modes through automated comparative backtests | MTF-01..05 | 3 |

## Phase Details

### Phase 13: QC API Client & Safety Foundation

**Goal:** System can authenticate and communicate with QuantConnect REST API with defense-in-depth safety preventing any real-money operations

**Depends on:** None (foundation for all v1.1 work)

**Requirements:** API-01, API-02, API-03, API-04, API-05, SAFE-01, SAFE-02

**Success Criteria** (what must be TRUE):

1. API client authenticates to QC and retrieves account/project info successfully
2. Any attempt to call a live/real-money endpoint is refused with explicit error before the request leaves the process
3. API calls automatically retry with exponential backoff + jitter on transient failures; rate limits are respected
4. No credentials appear in any log output, error message, or committed file (detect-secrets hook active)

**Plans:** 4/4 plans complete

Plans:

- [x] 13-01-PLAN.md — Dependencies and pre-commit hooks (detect-secrets, PAPER_TRADING_ONLY guard)
- [x] 13-02-PLAN.md — QCApiClient core (HMAC auth, safety gate, retry, credential redaction)
- [x] 13-03-PLAN.md — Typed endpoint wrappers (7 methods for live/backtest APIs)
- [x] 13-04-PLAN.md — Test suite with fixtures and meta-tests

---

### Phase 14: Data Sync & Dashboard Integration

**Goal:** Portfolio state from QC Cloud is reliably synchronized and displayed with freshness guarantees on the read-only dashboard

**Depends on:** Phase 13 (requires authenticated API client)

**Requirements:** SYNC-01, SYNC-02, SYNC-03, SYNC-04, SYNC-05, SYNC-06, DASH-01, DASH-02, DASH-03, DASH-04, DASH-05, SAFE-04

**Success Criteria** (what must be TRUE):

1. Dashboard displays current QC portfolio state (holdings, cash, P&L) refreshed approximately every 5 minutes during market hours
2. Data older than 10 minutes shows visible stale warning; data older than 30 minutes shows strong error state
3. Discrepancies between local mirror and QC authoritative state trigger Telegram SYNC_DISCREPANCY alert without auto-correcting
4. All timestamps are stored UTC internally and converted to ET only at display and market-hours-check boundaries
5. Dashboard never shows fabricated data; sync status, last sync time, and portfolio freshness indicator are always visible

**Plans:** 1/4 plans executed

Plans:
- [x] 14-01-PLAN.md — Sync module & JSONL persistence (poll → reconcile → atomic persist → alert)
- [ ] 14-02-PLAN.md — Dashboard data layer (3-state freshness + sync_jsonl loader)
- [ ] 14-03-PLAN.md — Dashboard display (freshness banner, metrics, holdings, sync status)
- [ ] 14-04-PLAN.md — Test suite (sync module + dashboard loader + regression)

**UI hint**: yes

---

### Phase 15: Paper Trading & Order Flow

**Goal:** Pipeline signals are delivered to a running QC paper algorithm and fill results are tracked with full audit traceability

**Depends on:** Phase 14 (pre-submission reconciliation check requires sync)

**Requirements:** PTD-01, PTD-02, PTD-03, PTD-04, PTD-05, FT-01, FT-02, FT-03, FT-04, SAFE-05

**Success Criteria** (what must be TRUE):

1. A paper trading algorithm can be deployed to QC Cloud and receive signal commands via Commands API without redeployment
2. Signal-to-order-to-fill chain is fully traceable in the append-only audit journal
3. Partial fills, order rejections, and their reasons are tracked and queryable
4. Stale signals triggered outside valid execution window are safely skipped with logged reason
5. Duplicate deploy requests are rejected via idempotent keys; retry-safe operations throughout

**Plans**: TBD

---

### Phase 16: Production Scheduler

**Goal:** Full pipeline runs autonomously on US market schedule with fault tolerance, no overlapping executions, and zero v1.0 test regressions

**Depends on:** Phase 15 (scheduler wraps the complete pipeline including order submission)

**Requirements:** SCHED-01, SCHED-02, SCHED-03, SCHED-04, SCHED-05, SCHED-06, SAFE-03

**Success Criteria** (what must be TRUE):

1. Pipeline triggers automatically on NYSE market schedule (ET timezone, DST-aware) via APScheduler in Render Background Worker
2. Concurrent/overlapping runs are prevented via file lock; each run is idempotent and catch-up capable
3. Upstream job failure skips downstream dependent jobs with logged reason and appropriate alert
4. All 433+ existing v1.0 tests pass unchanged after full v1.1 implementation (lazy imports, optional params)
5. GitHub Actions monitors heartbeat and sends failure alert if scheduled run is missed

**Plans**: TBD

---

### Phase 17: MTF Backtest Validation

**Goal:** Strategy modes are continuously validated through automated comparative backtesting with human-gated activation decisions

**Depends on:** Phase 13 (requires API client for Cloud Backtest API; independent of sync/scheduler)

**Requirements:** MTF-01, MTF-02, MTF-03, MTF-04, MTF-05

**Success Criteria** (what must be TRUE):

1. System runs comparative backtests across all three strategy modes (daily_only, daily_filter_4h_setup, daily_filter_4h_setup_1h_optional) via QC Cloud API
2. Reports include Sharpe, drawdown, win rate, and mode-vs-mode divergence metrics with configuration/version metadata
3. Material regressions trigger alerts but never automatically approve strategies, change modes, or submit orders
4. Activation decisions require explicit human approval through validation gate before mode promotion

**Plans**: TBD

---

## Requirement Coverage

| Requirement | Phase | Status |
|-------------|-------|--------|
| API-01 | 13 | Pending |
| API-02 | 13 | Pending |
| API-03 | 13 | Pending |
| API-04 | 13 | Pending |
| API-05 | 13 | Pending |
| SAFE-01 | 13 | Pending |
| SAFE-02 | 13 | Pending |
| SYNC-01 | 14 | Pending |
| SYNC-02 | 14 | Pending |
| SYNC-03 | 14 | Pending |
| SYNC-04 | 14 | Pending |
| SYNC-05 | 14 | Pending |
| SYNC-06 | 14 | Pending |
| DASH-01 | 14 | Pending |
| DASH-02 | 14 | Pending |
| DASH-03 | 14 | Pending |
| DASH-04 | 14 | Pending |
| DASH-05 | 14 | Pending |
| SAFE-04 | 14 | Pending |
| PTD-01 | 15 | Pending |
| PTD-02 | 15 | Pending |
| PTD-03 | 15 | Pending |
| PTD-04 | 15 | Pending |
| PTD-05 | 15 | Pending |
| FT-01 | 15 | Pending |
| FT-02 | 15 | Pending |
| FT-03 | 15 | Pending |
| FT-04 | 15 | Pending |
| SAFE-05 | 15 | Pending |
| SCHED-01 | 16 | Pending |
| SCHED-02 | 16 | Pending |
| SCHED-03 | 16 | Pending |
| SCHED-04 | 16 | Pending |
| SCHED-05 | 16 | Pending |
| SCHED-06 | 16 | Pending |
| SAFE-03 | 16 | Pending |
| MTF-01 | 17 | Pending |
| MTF-02 | 17 | Pending |
| MTF-03 | 17 | Pending |
| MTF-04 | 17 | Pending |
| MTF-05 | 17 | Pending |

**Coverage:** 41/41 requirements mapped ✓ (8 categories, 0 orphans)

## Progress

| Milestone | Phases | Plans | Status | Shipped |
|-----------|--------|-------|--------|---------|
| v1.0 | 12 | 53 | Complete | 2026-06-15 |
| v1.1 | 5 | ~21 est. | Active | — |
