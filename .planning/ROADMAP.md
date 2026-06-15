# Roadmap: Dahan MarketPilot

## Overview

Dahan MarketPilot v1 is planned as a safety-first sequence. The project starts with repository foundation, licensing, paper-only configuration, typed models, and non-trading scaffolds. It then verifies current QuantConnect APIs, builds universe/regime/indicator foundations, implements each setup independently, adds transparent scoring and explanations, adds risk/order lifecycle and notification events, validates through backtesting gates, enables QuantConnect Paper Trading and Telegram alerts, adds a read-only Render Streamlit dashboard, and finishes with CI/CD, security, documentation, and release audit.

## Phases

**Phase Numbering:**

- Integer phases (1, 2, 3): Planned milestone work.
- Decimal phases (2.1, 2.2, 4.1): Controlled insertions that preserve
  completed phase history while adding required product-definition work before a
  later phase starts.

- [x] **Phase 1: Foundation and Safety** - Repository foundation, licensing, paper-only guard, configuration, domain models, tests, and minimal non-trading app surfaces. (completed 2026-06-12)
- [x] **Phase 2: QuantConnect Foundation and Universe** - Verify current LEAN APIs, add dynamic universe, data quality, SymbolData lifecycle, indicators, and market regime. (completed 2026-06-13)
- [x] **Phase 3: Trend Pullback** - Implement and test the Trend Pullback setup with evidence, rejections, scoring components, and explanations. (completed 2026-06-13)
- [x] **Phase 4: Volume Breakout** - Implement and test prior-resistance breakout logic with current-bar exclusion and volume confirmation. (completed 2026-06-13)
- [x] **Phase 4.1: Multi-Timeframe Signal Foundation** - Add StrategyMode, completed-bar/timeframe contracts, 4H alignment policy, per-timeframe readiness, MTF setup adaptation, deterministic tests, and documentation sync. (completed 2026-06-14)
- [x] **Phase 5: Relative Strength and Unified Scoring** - Implement Relative Strength Leader, candidate ranking, MarketPilot Score, classification, confidence, and setup comparison while consuming StrategyMode and MTF evidence from Phase 4.1. (completed 2026-06-14)
- [x] **Phase 6: Portfolio Risk and Order Lifecycle** - Add portfolio constraints, sizing, order state, stops, targets, exits, restart state, and notification-domain events. (completed 2026-06-14)
- [x] **Phase 7: Backtesting and Validation** - Add realistic backtesting, no-look-ahead validation, chronological validation, activation gates, and reports. (completed 2026-06-14)
- [x] **Phase 8: QuantConnect Paper Trading and Telegram** - Add gated paper modes, QuantConnect Paper Trading deployment design, reconciliation, recovery, and Telegram delivery. (completed 2026-06-14)
- [x] **Phase 9: Render Dashboard** - Add read-only mobile Streamlit dashboard backed by QuantConnect-sourced data, caching, auth, stale-data handling, and system health. (completed 2026-06-15)
- [ ] **Phase 10: CI/CD, Security and Release** - Add workflows, weekly validation, dashboard health, security review, operations docs, recovery docs, final audit, and release preparation.

## Phase Details

### Phase 1: Foundation and Safety

**Goal**: Establish the repository and safety foundation without implementing trading entries or submitting stock orders.
**Depends on**: Nothing (first phase)
**Requirements**: SAF-01, SAF-02, SAF-03, SAF-04, SAF-05, SAF-06, CFG-01, CFG-02, CFG-03, CFG-04, CFG-05, QC-01
**Success Criteria** (what must be TRUE):

  1. The repository has required safety, licensing, attribution, disclaimer, configuration, and test foundations.
  2. Unsafe configuration fails validation, including any attempt to disable `PAPER_TRADING_ONLY`.
  3. A minimal non-trading QuantConnect algorithm and minimal read-only Streamlit foundation exist without order logic.
  4. No production strategy code, stock orders, Paper orders, broker adapters, or fake performance artifacts exist.

**Plans**: 4 plans
Plans:
**Wave 1**

- [x] 01-01: Repository, licensing, attribution, disclaimer, and project instruction foundation.

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 01-02: Paper-only safety guard, typed configuration, FX seed configuration, and validation rules.

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 01-03: Domain model and deterministic unit-test foundation.

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 01-04: Minimal non-trading QuantConnect and Streamlit foundations with no order controls.

### Phase 2: QuantConnect Foundation and Universe

**Goal**: Build verified QuantConnect foundations for data, indicators, dynamic universe, SymbolData lifecycle, and market regime.
**Depends on**: Phase 1
**Requirements**: QC-02, QC-03, QC-04, UNI-01, UNI-02, UNI-03, UNI-04, UNI-05, REG-01, REG-02, REG-03, IND-01, IND-02, IND-03, IND-04, IND-05
**Success Criteria** (what must be TRUE):

  1. Current official QuantConnect APIs used by the phase are documented and verified.
  2. Dynamic universe selection records counts, additions, removals, exclusions, and data-quality reasons.
  3. Indicator readiness and invalid-data rejection prevent incomplete signals.
  4. SPY/QQQ market regime states are configurable, tested, and do not force blanket liquidation.

**Plans**: 4 plans
Plans:
**Wave 1**

- [x] 02-01: Verify current LEAN APIs and establish QuantConnect integration conventions.

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 02-02: Dynamic universe selection and data-quality pipeline.

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 02-03: SymbolData lifecycle and required indicator readiness.

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 02-04: SPY/QQQ market regime and regime tests.

### Phase 3: Trend Pullback

**Goal**: Implement the Trend Pullback setup as an independently testable strategy module with transparent evidence and rejection logic.
**Depends on**: Phase 2
**Requirements**: SET-01, SET-02, SET-07
**Success Criteria** (what must be TRUE):

  1. Trend Pullback detects valid pullbacks toward EMA20/EMA50 in established uptrends.
  2. Trend Pullback rejects invalid data, RISK_OFF, excessive ATR, broken structure, poor reward/risk, and failed constraints.
  3. Signal timing uses completed daily bars and records later valid execution assumptions.
  4. Unit tests cover triggers, recovery behavior, and rejection conditions.

**Plans**: 4 plans
Plans:
**Wave 1**

- [x] 03-01: Trend Pullback rule contract and fixture design.

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 03-02: Trend Pullback detection, rejection, and evidence generation.

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 03-03: Trend Pullback scoring components, explanations, and tests.

### Phase 4: Volume Breakout

**Goal**: Implement Volume Breakout as an independently testable setup with current-bar exclusion and volume confirmation.
**Depends on**: Phase 3
**Requirements**: SET-03, SET-04
**Success Criteria** (what must be TRUE):

  1. Prior resistance excludes the current bar and uses the configured completed-bar window.
  2. Breakout signals require volume confirmation, acceptable extension, acceptable ATR, and valid reward/risk.
  3. Signals are rejected for stale data, earnings-risk conflict, poor reward/risk, or portfolio conflicts.
  4. Unit tests prove current-bar exclusion and no same-close fill assumption.

**Plans**: 3 plans
Plans:
**Wave 1**

- [x] 04-01: Breakout window and prior-resistance contract.

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 04-02: Volume Breakout detection, rejection, and evidence generation.

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 04-03: Volume Breakout scoring components, explanations, and tests.

**Wave 4** *(gap closure after verification)*

- [x] 04-04: Stale-data gap closure for Volume Breakout readiness.

### Phase 4.1: Multi-Timeframe Signal Foundation

**Goal**: Add the typed strategy-mode and completed-bar foundation needed for Daily/4H/optional 1H signal evidence before unified scoring starts.
**Depends on**: Phase 4
**Requirements**: MODE-01, MODE-02, MODE-03, TF-01, TF-02, TF-03, TF-04, TF-05, TF-06, TF-07, QC-MTF-01, QC-MTF-02, SET-MTF-01, SET-MTF-02, SET-MTF-03, BT-MTF-01
**Success Criteria** (what must be TRUE):

  1. The system supports exactly `daily_only`, `daily_filter_4h_setup`, and `daily_filter_4h_setup_1h_optional`, with `daily_only` as the default compatibility and benchmark mode.
  2. Strategy mode is separate from `backtest`, `shadow`, and `paper` environment modes, and invalid modes fail closed.
  3. Completed-bar and setup timing contracts are timeframe-aware and preserve signal timeframe, bar start/end, completion status, exchange timezone, RTH/partial-session status, freshness, source resolution, and later valid execution requirement.
  4. Daily, 4H, and 1H responsibilities are explicit; 4H is the primary setup/signal timeframe in MTF modes, while 1H is optional confirmation only.
  5. QuantConnect multi-resolution, consolidator, RTH, DST, holiday, early-close, dynamic-universe cleanup, and warm-up assumptions are verified against official docs before implementation uses them.
  6. Orders, Paper Trading, Telegram delivery, real Backtests, fake performance, portfolio mutation, and live behavior remain disabled.

**Plans**: 4 plans

Plans:

**Wave 1**

- [x] 04.1-01-PLAN.md - QuantConnect MTF verification and StrategyMode contract.

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 04.1-02-PLAN.md - Completed-bar models, generalized SetupTiming, and per-timeframe readiness.

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 04.1-03-PLAN.md - Trend Pullback and Volume Breakout MTF adaptation with daily_only compatibility.

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 04.1-04-PLAN.md - Documentation, validation, future backtesting comparison requirements, and Phase 5 handoff.

### Phase 5: Relative Strength and Unified Scoring

**Goal**: Add Relative Strength Leader and unify setup ranking into transparent MarketPilot scoring.
**Depends on**: Phase 4.1
**Requirements**: SET-05, SET-06, SCO-01, SCO-02, SCO-03, SET-MTF-03
**Success Criteria** (what must be TRUE):

  1. Relative Strength Leader works independently and can also confirm other setups.
  2. MarketPilot Score ranks candidates with component-level numeric evidence.
  3. Score classification and confidence boundaries are configurable, documented, and tested.
  4. Combined Swing remains blocked until individual setup validation is complete.
  5. Phase 5 consumes StrategyMode, daily context score, 4H setup evidence, optional 1H confirmation evidence, timeframe alignment status, and data-quality confidence without finalizing arbitrary MTF weights before backtesting validation.

**Plans**: 3 plans

Plans:

**Wave 1**

- [x] 05-01-PLAN.md - Relative Strength Leader setup and tests.

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 05-02-PLAN.md - Unified MarketPilot scoring, classifications, and confidence.

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 05-03-PLAN.md - Setup comparison, explanations, and Combined Swing readiness gate.

### Phase 6: Portfolio Risk and Order Lifecycle

**Goal**: Build portfolio constraints, sizing, order lifecycle, exits, persistence, audit, and notification-domain events.
**Depends on**: Phase 5
**Requirements**: SCO-04, RISK-01, RISK-02, RISK-03, RISK-04, RISK-05, RISK-06, RISK-07
**Success Criteria** (what must be TRUE):

  1. Risk budgeting, position sizing, allocation, cash, sector, and count constraints reject unsafe orders.
  2. Order lifecycle states cover submissions, fills, rejections, cancellations, stops, targets, partial closes, full closes, and restart restoration.
  3. Exits remain authoritative for existing positions regardless of market regime changes.
  4. Notification-domain events are testable with fake transports and do not control safety logic.

**Plans**: 5 plans

Plans:

**Wave 1**

- [x] 06-01-PLAN.md - Portfolio constraints and position sizing.

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 06-02-PLAN.md - Order state machine and duplicate-order prevention.

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 06-03-PLAN.md - Stops, targets, partial exits, trailing exits, and maximum holding period.

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 06-04-PLAN.md - Persistence, restart-state restoration, split/delisting handling where practical, and audit journal.

**Wave 5** *(blocked on Wave 4 completion)*

- [x] 06-05-PLAN.md - Notification-domain events, formatters, fake transport, deduplication, and rate limiting.

### Phase 7: Backtesting and Validation

**Goal**: Prove backtesting methodology, no-look-ahead behavior, execution realism, reports, and activation gates before Paper Trading.
**Depends on**: Phase 6
**Requirements**: BT-01, BT-02, BT-03, BT-04, BT-05, BT-06, BT-07, BT-08
**Success Criteria** (what must be TRUE):

  1. Backtests and Paper Trading use identical strategy-rule modules.
  2. No-look-ahead, current-bar exclusion, signal/fill timing, and same-bar ambiguity tests pass.
  3. Reports include chronological validation, benchmark comparison, fee/slippage assumptions, and activation-gate outcomes.
  4. The repository contains no fake backtest, fake portfolio, or profitability claim artifacts.

**Plans**: 5 plans

Plans:

**Wave 1**

- [x] 07-01-PLAN.md - Backtest execution assumptions, fees, slippage, fill models, and no-look-ahead tests.

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 07-02-PLAN.md - Full-period, year-by-year, In-Sample, and Out-of-Sample reporting.

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 07-03-PLAN.md - Walk-Forward or equivalent chronological validation and sensitivity analysis.

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 07-04-PLAN.md - Benchmark comparison, activation gates, and strategy approval state.

**Wave 5** *(blocked on Wave 4 completion)*

- [x] 07-05-PLAN.md - Backtest report generation and notification preview mode.

### Phase 8: QuantConnect Paper Trading and Telegram

**Goal**: Enable gated QuantConnect Cloud Paper Trading modes and Telegram alerts after validation gates pass.
**Depends on**: Phase 7
**Requirements**: REG-04, TEL-01, TEL-02, TEL-03, TEL-04, TEL-05, TEL-06
**Success Criteria** (what must be TRUE):

  1. Shadow, Limited Paper, and Full Approved Paper modes are gated by validation state.
  2. QuantConnect Paper Trading state, orders, fills, reconciliation, restart recovery, and protective-order recovery remain source-of-truth aligned.
  3. Telegram sends configured signal, paper activity, regime, system, error, and daily summary alerts.
  4. Telegram failures, quotas, disabled settings, missing token, and missing chat ID are tested and do not stop trading safety logic.

**Plans**: 4 plans
Plans:
**Wave 1**

- [x] 08-01: Paper Trading modes, deployment gates, and QuantConnect Live Node assumptions.

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 08-02: Order reconciliation, restart recovery, and protective-order recovery.

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 08-03: Telegram integration path, secrets handling, and delivery service.

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 08-04: Telegram alert coverage, duplicate suppression, rate limiting, and failure tests.

### Phase 9: Render Dashboard

**Goal**: Build a read-only mobile Streamlit dashboard on Render using QuantConnect-sourced data and safe caching.
**Depends on**: Phase 8
**Requirements**: QC-05, DASH-01, DASH-02, DASH-03, DASH-04, DASH-05, DASH-06, DASH-07
**Success Criteria** (what must be TRUE):

  1. Render serves a password-protected, mobile-friendly Streamlit dashboard.
  2. Dashboard pages are read-only and contain no order controls.
  3. Dashboard data is sourced from verified QuantConnect API/export paths with caching and stale-data warnings.
  4. USD/NIS displays, FX warnings, auth behavior, error presentation, and secret masking are tested.

**Plans**: 7 plans
Plans:
**Wave 1**

- [x] 09-01: Verify QuantConnect data access/export path and dashboard data contracts.

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 09-02: Streamlit app shell, authentication, mobile layout, and read-only enforcement.

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 09-03: Dashboard page registry and Overview page foundation.
- [x] 09-06: Render deployment and dependency configuration with package-legitimacy checkpoint.

**Wave 4** *(blocked on 09-03 completion)*

- [x] 09-04: Portfolio, trading, signal, backtest, and strategy dashboard pages.

**Wave 5** *(blocked on Wave 4 completion)*

- [x] 09-05: Risk, notifications, activity, and system status dashboard pages.

**Wave 6** *(blocked on 09-01, 09-02, 09-05, and 09-06 completion)*

- [x] 09-07: Cache/stale behavior, USD/NIS FX display helpers, and final dashboard test hardening.

### Phase 10: CI/CD, Security and Release

**Goal**: Prepare the project for safe operation with CI/CD, security review, documentation, recovery procedures, and final release audit.
**Depends on**: Phase 9
**Requirements**: CI-01, CI-02, CI-03, CI-04, CI-05, CI-06
**Success Criteria** (what must be TRUE):

  1. GitHub Actions run deterministic tests and approved QuantConnect/Render workflows without exposing secrets.
  2. Operations, recovery, troubleshooting, setup, licensing, disclaimer, and limitations documentation are complete.
  3. Security review confirms no real-money path, no secret exposure, and read-only dashboard behavior.
  4. Final audit confirms no fake performance artifacts, no unverified profitability claims, and all v1 requirements are traced.

**Plans**: 4 plans

Plans:

- [ ] 10-01: GitHub Actions for tests, QuantConnect sync, cloud backtest, weekly validation, and dashboard health.
- [ ] 10-02: Security review, secret handling, and release gates.
- [ ] 10-03: Operations, recovery, troubleshooting, setup, and limitations documentation.
- [ ] 10-04: Final audit, licensing/attribution review, release preparation, and handoff.

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 4.1 -> 5 -> 6 -> 7 -> 8 -> 9 -> 10.

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation and Safety | 4/4 | Complete    | 2026-06-12 |
| 2. QuantConnect Foundation and Universe | 4/4 | Complete | 2026-06-13 |
| 3. Trend Pullback | 3/3 | Complete | 2026-06-13 |
| 4. Volume Breakout | 4/4 | Complete   | 2026-06-13 |
| 4.1. Multi-Timeframe Signal Foundation | 4/4 | Complete | 2026-06-14 |
| 5. Relative Strength and Unified Scoring | 3/3 | Complete | 2026-06-14 |
| 6. Portfolio Risk and Order Lifecycle | 5/5 | Complete    | 2026-06-14 |
| 7. Backtesting and Validation | 5/5 | Complete    | 2026-06-14 |
| 8. QuantConnect Paper Trading and Telegram | 4/4 | Complete    | 2026-06-14 |
| 9. Render Dashboard | 7/7 | Complete   | 2026-06-15 |
| 10. CI/CD, Security and Release | 0/4 | Not started | - |
