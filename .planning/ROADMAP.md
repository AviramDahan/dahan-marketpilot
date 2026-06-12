# Roadmap: Dahan MarketPilot

## Overview

Dahan MarketPilot v1 is planned as a safety-first sequence. The project starts with repository foundation, licensing, paper-only configuration, typed models, and non-trading scaffolds. It then verifies current QuantConnect APIs, builds universe/regime/indicator foundations, implements each setup independently, adds transparent scoring and explanations, adds risk/order lifecycle and notification events, validates through backtesting gates, enables QuantConnect Paper Trading and Telegram alerts, adds a read-only Render Streamlit dashboard, and finishes with CI/CD, security, documentation, and release audit.

## Phases

**Phase Numbering:**

- Integer phases (1, 2, 3): Planned milestone work.
- Decimal phases (2.1, 2.2): Urgent insertions if needed later.

- [ ] **Phase 1: Foundation and Safety** - Repository foundation, licensing, paper-only guard, configuration, domain models, tests, and minimal non-trading app surfaces.
- [ ] **Phase 2: QuantConnect Foundation and Universe** - Verify current LEAN APIs, add dynamic universe, data quality, SymbolData lifecycle, indicators, and market regime.
- [ ] **Phase 3: Trend Pullback** - Implement and test the Trend Pullback setup with evidence, rejections, scoring components, and explanations.
- [ ] **Phase 4: Volume Breakout** - Implement and test prior-resistance breakout logic with current-bar exclusion and volume confirmation.
- [ ] **Phase 5: Relative Strength and Unified Scoring** - Implement Relative Strength Leader, candidate ranking, MarketPilot Score, classification, confidence, and setup comparison.
- [ ] **Phase 6: Portfolio Risk and Order Lifecycle** - Add portfolio constraints, sizing, order state, stops, targets, exits, restart state, and notification-domain events.
- [ ] **Phase 7: Backtesting and Validation** - Add realistic backtesting, no-look-ahead validation, chronological validation, activation gates, and reports.
- [ ] **Phase 8: QuantConnect Paper Trading and Telegram** - Add gated paper modes, QuantConnect Paper Trading deployment design, reconciliation, recovery, and Telegram delivery.
- [ ] **Phase 9: Render Dashboard** - Add read-only mobile Streamlit dashboard backed by QuantConnect-sourced data, caching, auth, stale-data handling, and system health.
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

- [ ] 01-01: Repository, licensing, attribution, disclaimer, and project instruction foundation.

**Wave 2** *(blocked on Wave 1 completion)*

- [ ] 01-02: Paper-only safety guard, typed configuration, FX seed configuration, and validation rules.

**Wave 3** *(blocked on Wave 2 completion)*

- [ ] 01-03: Domain model and deterministic unit-test foundation.

**Wave 4** *(blocked on Wave 3 completion)*

- [ ] 01-04: Minimal non-trading QuantConnect and Streamlit foundations with no order controls.

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

- [ ] 02-01: Verify current LEAN APIs and establish QuantConnect integration conventions.
- [ ] 02-02: Dynamic universe selection and data-quality pipeline.
- [ ] 02-03: SymbolData lifecycle and required indicator readiness.
- [ ] 02-04: SPY/QQQ market regime and regime tests.

### Phase 3: Trend Pullback

**Goal**: Implement the Trend Pullback setup as an independently testable strategy module with transparent evidence and rejection logic.
**Depends on**: Phase 2
**Requirements**: SET-01, SET-02, SET-07
**Success Criteria** (what must be TRUE):

  1. Trend Pullback detects valid pullbacks toward EMA20/EMA50 in established uptrends.
  2. Trend Pullback rejects invalid data, RISK_OFF, excessive ATR, broken structure, poor reward/risk, and failed constraints.
  3. Signal timing uses completed daily bars and records later valid execution assumptions.
  4. Unit tests cover triggers, recovery behavior, and rejection conditions.

**Plans**: 3 plans

Plans:

- [ ] 03-01: Trend Pullback rule contract and fixture design.
- [ ] 03-02: Trend Pullback detection, rejection, and evidence generation.
- [ ] 03-03: Trend Pullback scoring components, explanations, and tests.

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

- [ ] 04-01: Breakout window and prior-resistance contract.
- [ ] 04-02: Volume Breakout detection, rejection, and evidence generation.
- [ ] 04-03: Volume Breakout scoring components, explanations, and tests.

### Phase 5: Relative Strength and Unified Scoring

**Goal**: Add Relative Strength Leader and unify setup ranking into transparent MarketPilot scoring.
**Depends on**: Phase 4
**Requirements**: SET-05, SET-06, SCO-01, SCO-02, SCO-03
**Success Criteria** (what must be TRUE):

  1. Relative Strength Leader works independently and can also confirm other setups.
  2. MarketPilot Score ranks candidates with component-level numeric evidence.
  3. Score classification and confidence boundaries are configurable, documented, and tested.
  4. Combined Swing remains blocked until individual setup validation is complete.

**Plans**: 3 plans

Plans:

- [ ] 05-01: Relative Strength Leader setup and tests.
- [ ] 05-02: Unified MarketPilot scoring, classifications, and confidence.
- [ ] 05-03: Setup comparison, explanations, and Combined Swing readiness gate.

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

- [ ] 06-01: Portfolio constraints and position sizing.
- [ ] 06-02: Order state machine and duplicate-order prevention.
- [ ] 06-03: Stops, targets, partial exits, trailing exits, and maximum holding period.
- [ ] 06-04: Persistence, restart-state restoration, split/delisting handling where practical, and audit journal.
- [ ] 06-05: Notification-domain events, formatters, fake transport, deduplication, and rate limiting.

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

- [ ] 07-01: Backtest execution assumptions, fees, slippage, fill models, and no-look-ahead tests.
- [ ] 07-02: Full-period, year-by-year, In-Sample, and Out-of-Sample reporting.
- [ ] 07-03: Walk-Forward or equivalent chronological validation and sensitivity analysis.
- [ ] 07-04: Benchmark comparison, activation gates, and strategy approval state.
- [ ] 07-05: Backtest report generation and notification preview mode.

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

- [ ] 08-01: Paper Trading modes, deployment gates, and QuantConnect Live Node assumptions.
- [ ] 08-02: Order reconciliation, restart recovery, and protective-order recovery.
- [ ] 08-03: Telegram integration path, secrets handling, and delivery service.
- [ ] 08-04: Telegram alert coverage, duplicate suppression, rate limiting, and failure tests.

### Phase 9: Render Dashboard

**Goal**: Build a read-only mobile Streamlit dashboard on Render using QuantConnect-sourced data and safe caching.
**Depends on**: Phase 8
**Requirements**: QC-05, DASH-01, DASH-02, DASH-03, DASH-04, DASH-05, DASH-06, DASH-07
**Success Criteria** (what must be TRUE):

  1. Render serves a password-protected, mobile-friendly Streamlit dashboard.
  2. Dashboard pages are read-only and contain no order controls.
  3. Dashboard data is sourced from verified QuantConnect API/export paths with caching and stale-data warnings.
  4. USD/NIS displays, FX warnings, auth behavior, error presentation, and secret masking are tested.

**Plans**: 4 plans

Plans:

- [ ] 09-01: Verify QuantConnect data access/export path and dashboard data contracts.
- [ ] 09-02: Streamlit app shell, authentication, mobile layout, and read-only enforcement.
- [ ] 09-03: Dashboard pages for portfolio, positions, trades, signals, backtests, strategies, risk, notifications, activity, and system status.
- [ ] 09-04: Render deployment configuration, caching, stale-data handling, FX display, and dashboard tests.

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
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8 -> 9 -> 10.

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation and Safety | 0/4 | Not started | - |
| 2. QuantConnect Foundation and Universe | 0/4 | Not started | - |
| 3. Trend Pullback | 0/3 | Not started | - |
| 4. Volume Breakout | 0/3 | Not started | - |
| 5. Relative Strength and Unified Scoring | 0/3 | Not started | - |
| 6. Portfolio Risk and Order Lifecycle | 0/5 | Not started | - |
| 7. Backtesting and Validation | 0/5 | Not started | - |
| 8. QuantConnect Paper Trading and Telegram | 0/4 | Not started | - |
| 9. Render Dashboard | 0/4 | Not started | - |
| 10. CI/CD, Security and Release | 0/4 | Not started | - |
