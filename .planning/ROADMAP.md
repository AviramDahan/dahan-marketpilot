# Roadmap: Dahan MarketPilot

## Milestones

- âœ… **v1.0 Paper Trading Research Platform** â€” Phases 1-10.1 (shipped 2026-06-15)
- ðŸ”„ **v1.1 QuantConnect Live Paper Trading** â€” Phases 13-17, including 16.1 and 16.2 production readiness gates (active)

## Phases

<details>
<summary>âœ… v1.0 Paper Trading Research Platform (12 phases, 53 plans) â€” SHIPPED 2026-06-15</summary>

- [x] Phase 1: Foundation and Safety (4/4 plans) â€” completed 2026-06-12
- [x] Phase 2: QuantConnect Foundation and Universe (4/4 plans) â€” completed 2026-06-13
- [x] Phase 3: Trend Pullback (3/3 plans) â€” completed 2026-06-13
- [x] Phase 4: Volume Breakout (4/4 plans) â€” completed 2026-06-13
- [x] Phase 4.1: Multi-Timeframe Signal Foundation (4/4 plans) â€” completed 2026-06-14
- [x] Phase 5: Relative Strength and Unified Scoring (3/3 plans) â€” completed 2026-06-14
- [x] Phase 6: Portfolio Risk and Order Lifecycle (5/5 plans) â€” completed 2026-06-14
- [x] Phase 7: Backtesting and Validation (5/5 plans) â€” completed 2026-06-14
- [x] Phase 8: QuantConnect Paper Trading and Telegram (4/4 plans) â€” completed 2026-06-14
- [x] Phase 9: Render Dashboard (8/8 plans) â€” completed 2026-06-15
- [x] Phase 10: CI/CD, Security and Release (4/4 plans) â€” completed 2026-06-15
- [x] Phase 10.1: Close gap: runtime orchestrator (5/5 plans) â€” completed 2026-06-15

Full details archived: [milestones/v1.0-ROADMAP.md](milestones/v1.0-ROADMAP.md)

</details>

### v1.1 QuantConnect Live Paper Trading

- [x] **Phase 13: QC API Client & Safety Foundation** â€” Authenticated API client with defense-in-depth paper-only safety (completed 2026-06-15)
- [x] **Phase 14: Data Sync & Dashboard Integration** â€” Reliable portfolio sync from QC with freshness-aware dashboard display (completed 2026-06-16)
- [x] **Phase 15: Paper Trading & Order Flow** â€” Signal delivery to live algorithm with full fill tracking and audit trail (completed 2026-06-17)
- [x] **Phase 16: Production Scheduler** â€” Autonomous market-hours pipeline execution with fault tolerance (local implementation complete 2026-06-17; deployed product gates remain Phase 16.1/16.2)
- [x] **Phase 16.1: Production Integration & Dashboard Go-Live** â€” Local implementation for deployed personal autonomous Paper Trading product is complete; external deployment evidence remains pending
- [ ] **Phase 16.2: End-to-End UAT & Operational Burn-in** â€” Multi-session deployed-system proof under real QuantConnect Paper Trading conditions
- [ ] **Phase 17: MTF Backtest Validation** â€” Automated comparative backtesting with regression detection

## Overview

| Phase | Name | Goal | Requirements | Plans (est.) |
|-------|------|------|--------------|--------------|
| 13 | QC API Client & Safety Foundation | 4/4 | Complete   | 2026-06-15 |
| 14 | Data Sync & Dashboard Integration | 4/4 | Complete    | 2026-06-16 |
| 15 | Paper Trading & Order Flow | Deliver signals to running algorithm; track fills with audit traceability | PTD-01..05, FT-01..04, SAFE-05 | 12/12 complete; external order authority passed |
| 16 | Production Scheduler | Run pipeline autonomously on NYSE schedule with fault tolerance | SCHED-01..06, SAFE-03 | 5/5 complete |
| 16.1 | Production Integration & Dashboard Go-Live | Deploy a working personal autonomous Paper Trading product on Render with real dashboard data and Telegram delivery | PROD-01..10, SAFE-06..07 | TBD |
| 16.2 | End-to-End UAT & Operational Burn-in | Prove the deployed product operates continuously across real market sessions | UAT-01..09, OPS-01 | TBD |
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

- [x] 13-01-PLAN.md â€” Dependencies and pre-commit hooks (detect-secrets, PAPER_TRADING_ONLY guard)
- [x] 13-02-PLAN.md â€” QCApiClient core (HMAC auth, safety gate, retry, credential redaction)
- [x] 13-03-PLAN.md â€” Typed endpoint wrappers (7 methods for live/backtest APIs)
- [x] 13-04-PLAN.md â€” Test suite with fixtures and meta-tests

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

**Plans:** 4/4 plans complete

Plans:

- [x] 14-01-PLAN.md â€” Sync module & JSONL persistence (poll â†’ reconcile â†’ atomic persist â†’ alert)
- [x] 14-02-PLAN.md â€” Dashboard data layer (3-state freshness + sync_jsonl loader)
- [x] 14-03-PLAN.md â€” Dashboard display (freshness banner, metrics, holdings, sync status)
- [x] 14-04-PLAN.md â€” Test suite (sync module + dashboard loader + regression)

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

**Plans:** 12/12 plans complete; `/live/orders/read` current-tag Submitted/Filled evidence passed on 2026-06-17

Plans:

- [x] 15-01-PLAN.md - QC API paper deployment, command, stop/liquidate, and live-orders wrappers
- [x] 15-02-PLAN.md - Signal command builder, deployment idempotency, pre-submit sync gate, and stale-window skips
- [x] 15-03-PLAN.md - LEAN `on_command` receiver, internal stale/duplicate safety gates, and tagged paper orders
- [x] 15-04-PLAN.md - Authoritative QC order/fill polling, audit JSONL mirror, and signal-order-fill trace queries
- [x] 15-05-PLAN.md - Offline E2E tests, docs, UAT/verification, QC sync/compile/deploy/command API verified
- [x] 15-06-PLAN.md - Gap closure: smoke helper and payload diagnostics complete; callback-to-order smoke rerouted to Object Store fallback
- [x] 15-07-PLAN.md - Gap closure: isolated command-dispatch probe deployed successfully; generic command marker not observed, fallback selected
- [x] 15-08-PLAN.md - Gap closure: Object Store signal inbox implemented locally
- [x] 15-09-PLAN.md - Gap closure: Object Store preflight/diagnose-only implemented; multipart upload fixed and external write passes
- [x] 15-10-PLAN.md - Gap closure: live-log API pagination corrected; Object Store receipt and submitted paper order event observed
- [x] 15-11-PLAN.md - Gap closure: temporary Paper deployments auto-stop by default
- [x] 15-12-PLAN.md - Gap closure: market-hours Object Store smoke observed authoritative `/live/orders/read` current-tag Submitted/Filled evidence after snapshot wait

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

**Plans**: 5/5 plans complete across 4 execution waves. Local implementation and full regression passed; deployed product verification remains Phase 16.1/16.2.

**Execution Waves:**

- Wave 1:
  - [x] 16-01-PLAN.md - Scheduler clock, APScheduler configuration, and NYSE/ET market-session guard
  - [x] 16-02-PLAN.md - Production runtime runner and dependency-aware job graph
- Wave 2:
  - [x] 16-03-PLAN.md - Durable lock, run ledger, idempotent retries, and conservative catch-up
- Wave 3:
  - [x] 16-04-PLAN.md - Heartbeat, system-health records, and monitor-only GitHub Actions missed-run check
- Wave 4:
  - [x] 16-05-PLAN.md - Render Background Worker boundary, Phase 16.1 interfaces, docs, and regression gate

**External Gates Still Open:**

- Phase 15 authoritative `/live/orders/read` current-tag order/fill evidence passed on 2026-06-17.
- Phase 16.1 must verify deployed dashboard, durable shared data, real Telegram delivery, secure secrets, and operation while the local computer is off.
- Phase 16.2 must verify multi-session operational burn-in.

---

### Phase 16.1: Production Integration & Dashboard Go-Live

**Goal:** Deploy Dahan MarketPilot as a fully operational personal autonomous Paper Trading product.

**Depends on:** Phase 16 (scheduler runtime exists); Phase 15 authoritative order/fill verification passed for simulated Paper Trading on 2026-06-17.

**Requirements:** PROD-01, PROD-02, PROD-03, PROD-04, PROD-05, PROD-06, PROD-07, PROD-08, PROD-09, PROD-10, SAFE-06, SAFE-07

**Success Criteria** (what must be TRUE):

1. One production runtime runner connects the complete pipeline end-to-end without relying on the local computer.
2. Streamlit dashboard is deployed as a Render Web Service with a working password-protected URL.
3. Autonomous scheduler is deployed as a Render Background Worker.
4. Worker and dashboard share durable production data transport/storage, and the dashboard no longer runs with `data_source_kind=none`.
5. Dashboard displays real portfolio, signals, orders, fills, activity, and system-health data with controlled auto-refresh.
6. Runtime notification events are delivered through real Telegram, with failures isolated from safety logic.
7. Production secrets are configured securely in Render/QuantConnect/Telegram environments and are never committed.
8. The system continues operating while the local computer is off.

**Plans**: 6/6 plans complete across 4 execution waves. Local implementation and regression passed; deployed go-live evidence remains pending.

**Execution Waves:**

- Wave 1:
  - [x] 16.1-01-PLAN.md - Shared Render Key Value production state store
  - [x] 16.1-02-PLAN.md - Production runner wiring for shared state, durable lock, dashboard export, and Telegram
- Wave 2:
  - [x] 16.1-03-PLAN.md - Dashboard production data source and controlled auto-refresh
  - [x] 16.1-04-PLAN.md - Render Blueprint, secrets, deployment docs, and operator runbook
- Wave 3:
  - [x] 16.1-05-PLAN.md - External go-live verification scripts
- Wave 4:
  - [x] 16.1-06-PLAN.md - Go-live evidence, UAT, verification, and residual gate closeout

**Residual External Gate:** Phase 16.1 code/planning is complete, but production readiness is not externally complete until sanitized deployed evidence exists for dashboard URL/auth, worker heartbeat, shared production data, Telegram runtime delivery, and local-computer independence.

---

### Phase 16.2: End-to-End UAT & Operational Burn-in

**Goal:** Prove that the deployed system operates continuously under real QuantConnect Paper Trading conditions.

**Depends on:** Phase 16.1 (deployed product exists); Phase 15 authoritative `/live/orders/read` order/fill/rejection gate must be completed before v1.1 can be marked complete.

**Requirements:** UAT-01, UAT-02, UAT-03, UAT-04, UAT-05, UAT-06, UAT-07, UAT-08, UAT-09, OPS-01

**Success Criteria** (what must be TRUE):

1. Deployed flow proves signal -> scoring -> risk decision -> Paper order -> authoritative order result -> fill -> sync -> dashboard -> Telegram.
2. Scheduler heartbeat and missed-run monitoring are externally verified.
3. Restart and redeployment recovery are externally verified.
4. Duplicate-run prevention, stale-data handling, temporary QuantConnect failure handling, and Telegram delivery failure handling are verified.
5. Burn-in covers multiple consecutive real market sessions.
6. Final operational-readiness report confirms v1.1 is a working deployed product, not only completed code, tests, plans, or documentation.

**Plans**: TBD

---

### Phase 17: MTF Backtest Validation

**Goal:** Strategy modes are continuously validated through automated comparative backtesting with human-gated activation decisions

**Depends on:** Phase 13 (requires API client for Cloud Backtest API; independent of sync/scheduler). Phase 17 must not be used to bypass Phase 15, 16.1, or 16.2 operational readiness gates.

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
| SCHED-01 | 16 | Complete |
| SCHED-02 | 16 | Complete |
| SCHED-03 | 16 | Complete |
| SCHED-04 | 16 | Complete |
| SCHED-05 | 16 | Complete |
| SCHED-06 | 16 | Complete |
| SAFE-03 | 16 | Complete |
| PROD-01 | 16.1 | Pending |
| PROD-02 | 16.1 | Pending |
| PROD-03 | 16.1 | Pending |
| PROD-04 | 16.1 | Pending |
| PROD-05 | 16.1 | Pending |
| PROD-06 | 16.1 | Pending |
| PROD-07 | 16.1 | Pending |
| PROD-08 | 16.1 | Pending |
| PROD-09 | 16.1 | Pending |
| PROD-10 | 16.1 | Pending |
| SAFE-06 | 16.1 | Pending |
| SAFE-07 | 16.1 | Pending |
| UAT-01 | 16.2 | Pending |
| UAT-02 | 16.2 | Pending |
| UAT-03 | 16.2 | Pending |
| UAT-04 | 16.2 | Pending |
| UAT-05 | 16.2 | Pending |
| UAT-06 | 16.2 | Pending |
| UAT-07 | 16.2 | Pending |
| UAT-08 | 16.2 | Pending |
| UAT-09 | 16.2 | Pending |
| OPS-01 | 16.2 | Pending |
| MTF-01 | 17 | Pending |
| MTF-02 | 17 | Pending |
| MTF-03 | 17 | Pending |
| MTF-04 | 17 | Pending |
| MTF-05 | 17 | Pending |

**Coverage:** 63/63 requirements mapped âœ“ (11 categories, 0 orphans)

## Progress

| Milestone | Phases | Plans | Status | Shipped |
|-----------|--------|-------|--------|---------|
| v1.0 | 12 | 53 | Complete | 2026-06-15 |
| v1.1 | 7 | TBD | Active; not complete until deployed product and burn-in are externally verified | â€” |

## v1.1 Completion Gate

v1.1 must not be marked complete until all of the following are true:

1. Phase 15's `/live/orders/read` order/fill gate is externally verified for simulated Paper Trading, but v1.1 still requires deployed end-to-end verification.
2. Phase 16 scheduler exists but does not by itself satisfy production readiness.
3. Phase 16.1 deploys the dashboard and autonomous worker as a working Render-hosted personal product with durable data transport, real dashboard data, real Telegram delivery, secure secrets, and operation while the local computer is off.
4. Phase 16.2 proves multiple consecutive real market sessions and produces a final operational-readiness report.
5. Any future milestone after v1.1 requires explicit user approval.
