# Requirements: Dahan MarketPilot

**Defined:** 2026-06-12
**Core Value:** The system must provide an auditable paper-only swing-trading workflow where every signal, backtest, paper action, portfolio display, alert, and report is traceable to verified rules and numeric evidence.

## v1 Requirements

### Safety And Compliance

- [x] **SAF-01**: The system rejects any configuration where `PAPER_TRADING_ONLY` is false.
- [x] **SAF-02**: The system rejects real broker configuration, real-money credentials, live-money order support, leverage, margin, short selling, options, futures, cryptocurrency, Forex, and dashboard order submission.
- [x] **SAF-03**: Every dashboard page and generated report displays `SIMULATED PAPER TRADING ONLY - NOT FINANCIAL ADVICE`.
- [x] **SAF-04**: The repository includes `LICENSE`, `NOTICE`, `THIRD_PARTY_NOTICES.md`, and `DISCLAIMER.md` before release.
- [x] **SAF-05**: Secrets and credentials never appear in source files, logs, tests, reports, planning artifacts, or chat instructions.
- [x] **SAF-06**: Documentation clearly prohibits real-money trading, hidden live-trading switches, real-broker adapters, and automatic migration to live trading.

### Configuration And Foundation

- [x] **CFG-01**: The repository has a Python project foundation with test configuration, dependency files, `.env.example`, `.gitignore`, and focused documentation.
- [x] **CFG-02**: Typed configuration validates strategy, risk, notifications, dashboard, and environment settings.
- [x] **CFG-03**: Starting capital is configured from `starting_budget_nis`, `initial_usd_ils_rate`, `starting_cash_usd`, `trading_currency`, `display_currency`, `fx_rate_timestamp`, and `fx_rate_source`.
- [x] **CFG-04**: FX logic displays current USD and NIS values without rewriting historical USD accounting, and warns when the FX rate is stale.
- [x] **CFG-05**: Domain models cover signals, scores, explanations, positions, orders, fills, exits, alerts, reports, and audit events.

### QuantConnect Architecture

- [x] **QC-01**: A minimal non-trading `QCAlgorithm` compiles without submitting stock orders.
- [ ] **QC-02**: Current official QuantConnect LEAN and Cloud APIs are verified before implementation code uses them.
- [ ] **QC-03**: QuantConnect remains authoritative for simulated cash, portfolio equity, holdings, open positions, orders, fills, Paper Trading state, algorithm status, Paper Trading performance, and QuantConnect Backtest results.
- [ ] **QC-04**: LEAN CLI workflows are documented for sync, cloud backtest, and result retrieval without exposing credentials.
- [ ] **QC-05**: QuantConnect Object Store or Cloud API export mechanisms are designed only after official documentation verification.

### Universe And Market Regime

- [ ] **UNI-01**: The system uses QuantConnect dynamic fundamental or liquidity universe selection rather than a static hand-written ticker list.
- [ ] **UNI-02**: The universe filters for US-listed common equities, price at least $5, at least 250 completed daily bars, average 20-day volume at least 500,000 shares, average 20-day dollar volume at least $20,000,000, configurable minimum market capitalization, and valid tradability.
- [ ] **UNI-03**: The universe excludes ETFs, OTC securities, preferred shares where identifiable, warrants, invalid securities, stale data, and critical missing data.
- [ ] **UNI-04**: Universe records include counts, additions, removals, exclusions, exclusion reasons, sector distribution, update timestamp, and data-quality status.
- [ ] **UNI-05**: SymbolData and indicator lifecycle cleanup handles securities leaving the universe.
- [ ] **REG-01**: Market regime uses SPY and QQQ with EMA20, EMA50, EMA200, slopes, 20-day return, 60-day return, and optional breadth measures.
- [ ] **REG-02**: RISK_ON, NEUTRAL, and RISK_OFF thresholds are configurable, documented, unit-tested, and reported.
- [ ] **REG-03**: RISK_OFF blocks new long entries but does not automatically liquidate every existing position solely due to regime change.
- [ ] **REG-04**: Telegram regime transition alerts are generated when enabled and duplicate unchanged-state alerts are suppressed.

### Indicators And Setups

- [ ] **IND-01**: Required trend indicators include EMA8, EMA20, EMA50, EMA200, EMA slopes, moving-average alignment, EMA distances, and distance from 52-week high.
- [ ] **IND-02**: Required momentum indicators include RSI14, MACD 12/26/9, ROC20, ROC60, 20-day return, 60-day return, relative strength versus SPY and QQQ, and momentum percentile where practical.
- [ ] **IND-03**: Required volume indicators include average volume 20/50, relative volume, average dollar volume 20/50, volume trend, and pullback-volume behavior.
- [ ] **IND-04**: Required risk indicators include ATR14, ATR percentage, rolling volatility, structural swing high/low, recent drawdown, gap-risk approximation, and maximum adverse movement approximation where practical.
- [ ] **IND-05**: Missing, invalid, infinite, stale, or NaN data rejects signals and never becomes a default positive score.
- [ ] **SET-01**: Trend Pullback identifies strong stocks in established uptrends that pull back toward EMA20 or EMA50 and begin to recover.
- [ ] **SET-02**: Trend Pullback rejects broken trend structure, excessive ATR, excessive stop distance, overextension, incomplete data, earnings-risk conflicts, weak reward/risk, and failed portfolio constraints.
- [x] **SET-03**: Volume Breakout calculates prior resistance from the previous completed bars only, excluding the current bar.
- [x] **SET-04**: Volume Breakout requires volume confirmation, acceptable ATR, acceptable EMA20 extension, sufficient dollar volume, valid reward/risk, and non-RISK_OFF regime.
- [ ] **SET-05**: Relative Strength Leader measures outperformance versus SPY and QQQ while enforcing healthy structure, liquidity, ATR, 52-week high proximity, and overextension limits.
- [ ] **SET-06**: Trend Pullback, Volume Breakout, and Relative Strength Leader are implemented and validated independently before any Combined Swing strategy.
- [ ] **SET-07**: Completed daily-bar signals execute only at a later valid tradable price by default, with the exact execution method recorded.

### Strategy Modes And Multi-Timeframe Signals

- [ ] **MODE-01**: The system supports exactly three regular strategy modes: `daily_only`, `daily_filter_4h_setup`, and `daily_filter_4h_setup_1h_optional`.
- [ ] **MODE-02**: `daily_only` is the default, compatibility mode, and backtesting benchmark, and strategy mode remains separate from environment modes `backtest`, `shadow`, and `paper`.
- [ ] **MODE-03**: Strategy-mode configuration is typed and validated, preferably through `config/strategy.yaml`; missing, empty, invalid, or unsupported mode values fail closed.
- [ ] **TF-01**: Daily timeframe is mandatory and owns universe eligibility, liquidity, data quality, broad trend, EMA structure, SPY/QQQ regime, broad relative strength, volatility, gap/earnings context, and rejection of structurally weak candidates.
- [ ] **TF-02**: In MTF modes, completed 4H bars are the primary setup/signal timeframe for Trend Pullback and Volume Breakout, including setup quality, recovery/breakout confirmation, momentum/volume evidence, invalidation, and primary setup timestamp.
- [ ] **TF-03**: 1H is optional confirmation only in `daily_filter_4h_setup_1h_optional`; it can improve confidence/readiness/evidence but cannot independently create a trade or override failed Daily, invalid 4H, `RISK_OFF`, stale data, hard rejection, or invalid reward/risk.
- [ ] **TF-04**: Signals use completed bars only and timing models support `completed_daily_bar`, `completed_four_hour_bar`, and `completed_one_hour_bar` without future bars, incomplete bars, or unrealistic same-bar assumptions.
- [ ] **TF-05**: `SetupTiming` or its successor preserves strategy mode, signal timeframe, timestamp, bar start/end, completion status, exchange timezone, regular-hours status, partial-session status, freshness, source resolution, and later-valid-execution requirement.
- [ ] **TF-06**: Daily, 4H, and 1H readiness are tracked independently; mandatory timeframe data fails closed, while missing optional 1H alone cannot reject a valid Daily+4H candidate.
- [ ] **TF-07**: The system emits at most one candidate per symbol and does not create separate Daily, 4H, and 1H candidates.
- [ ] **QC-MTF-01**: Current official QuantConnect/LEAN documentation is verified before implementation selects multi-resolution subscriptions, consolidators, calendar/custom anchoring, RTH filtering, extended-hours exclusion, holidays, early closes, DST handling, indicator warm-up, and dynamic-universe consolidator registration/cleanup.
- [ ] **QC-MTF-02**: The 4H alignment policy is explicit. Because the US regular session is 6.5 hours, partial-session bars must be identified and forbidden from signal generation by default; partial evidence and a 2H alternative may be evaluated later, but 4H must not be silently replaced.
- [ ] **SET-MTF-01**: Trend Pullback MTF behavior uses Daily for broader healthy trend, 4H for pullback/recovery primary setup, and optional 1H for entry-readiness confirmation.
- [ ] **SET-MTF-02**: Volume Breakout MTF behavior uses Daily for structure, 4H for primary breakout, and optional 1H to confirm the breakout is holding and not overextended.
- [ ] **SET-MTF-03**: Relative Strength Leader and Phase 5 scoring consume strategy mode and MTF evidence, including `strategy_mode`, `daily_context_score`, `four_hour_setup_score`, `one_hour_confirmation_score`, `timeframe_alignment_status`, and `data_quality_confidence`, without finalizing arbitrary MTF weights before validation.
- [ ] **BT-MTF-01**: Future backtesting compares `daily_only`, `daily_filter_4h_setup`, `daily_filter_4h_setup_1h_optional`, a mandatory-1H-confirmation variant for backtesting only, different 4H alignment policies, and a 2H alternative if technically justified.

### Scoring, Explanations, And Audit

- [ ] **SCO-01**: Candidate scoring includes setup quality, trend, momentum, relative strength, volume, risk/reward, market regime, sector/portfolio fit, data quality, and earnings-risk policy.
- [ ] **SCO-02**: Every signal and rejection includes numeric evidence, component scores, total score, classification, confidence, and hard rejection reasons.
- [ ] **SCO-03**: Score classifications and confidence boundaries are configurable, documented, unit-tested, and included in reports.
- [ ] **SCO-04**: The audit trail records signal inputs, scoring evidence, decisions, orders, fills, exits, alerts, configuration version, strategy version, and timestamps.

### Portfolio Risk And Order Lifecycle

- [ ] **RISK-01**: Portfolio constraints enforce maximum position count, maximum sector exposure, maximum daily entries, cash constraints, and per-trade risk budget.
- [ ] **RISK-02**: Position sizing respects risk by stop distance, allocation limits, cash availability, and zero/invalid quantity rejection.
- [ ] **RISK-03**: Stops, targets, partial exits, trailing stops, maximum holding period, and duplicate-order prevention are modeled and tested.
- [ ] **RISK-04**: Order lifecycle handles submitted, partially filled, fully filled, rejected, canceled, protective order creation, target creation, partial close, full close, and restart restoration states.
- [ ] **RISK-05**: Split and delisting handling are designed and tested where practical.
- [ ] **RISK-06**: Existing positions remain governed by individual exit rules even when market regime changes.
- [ ] **RISK-07**: Notification-domain events are separate from order-safety logic and can be tested with fake transports.

### Backtesting And Validation

- [ ] **BT-01**: Backtests use the same strategy rules as Paper Trading.
- [ ] **BT-02**: Backtests include explicit fee, slippage, fill, and execution-timing assumptions.
- [ ] **BT-03**: Tests verify no-look-ahead behavior, current-bar exclusion, signal/fill timing, and same-bar ambiguity handling.
- [ ] **BT-04**: Reports include full-period, year-by-year, In-Sample, Out-of-Sample, Walk-Forward or equivalent chronological validation, sensitivity analysis, benchmark comparison, and activation-gate outcomes.
- [ ] **BT-05**: Strategy activation gates block unapproved strategies from Paper orders.
- [ ] **BT-06**: Historical reports never claim guaranteed profitability or future certainty.
- [ ] **BT-07**: Backtest notifications are disabled during normal historical Backtests unless preview mode is explicitly enabled.
- [ ] **BT-08**: The repository never contains fake Backtest results or fake portfolio data.

### Paper Trading And Telegram

- [ ] **TEL-01**: Shadow Mode, Limited Paper Mode, and Full Approved Paper Mode are gated by validation state.
- [ ] **TEL-02**: Paper Trading deployment, order reconciliation, restart recovery, and protective-order recovery are designed around QuantConnect as source of truth.
- [ ] **TEL-03**: Telegram sends configured BUY candidate, WATCH, Paper BUY, Paper SELL, submitted-order, partial-fill, full-fill, stop, target, partial-close, full-close, rejected-order, canceled-order, regime, system, error, start/restart, and daily-summary alerts.
- [ ] **TEL-04**: Telegram duplicate suppression, rate limiting, quota handling, missing-token behavior, missing-chat-ID behavior, disabled-notification behavior, and delivery failure behavior are unit-tested.
- [ ] **TEL-05**: Telegram secrets are stored only in approved secret stores and never in repository files.
- [ ] **TEL-06**: Telegram delivery failure does not stop trading logic or protective exit logic.

### Dashboard

- [ ] **DASH-01**: Render hosts a password-protected Streamlit dashboard.
- [ ] **DASH-02**: The dashboard is read-only and contains no order submission, modification, cancellation, or manual trade controls.
- [ ] **DASH-03**: Dashboard views include Overview, Positions, Trades, Signals, Backtests, Strategies, Risk, Notifications, Activity, and System Status.
- [ ] **DASH-04**: Dashboard data is sourced from QuantConnect-approved API/export paths and displays stale-data warnings.
- [ ] **DASH-05**: Dashboard displays portfolio values in USD and NIS and shows FX timestamp/source/staleness warnings.
- [ ] **DASH-06**: Dashboard masks secrets and presents API/cache/authentication errors safely.
- [ ] **DASH-07**: Dashboard tests cover API parsing, caching, stale data, authentication, read-only behavior, error presentation, and secret masking.

### CI/CD, Documentation, And Release

- [ ] **CI-01**: GitHub Actions run deterministic unit tests without requiring QuantConnect, Telegram, Render, broker credentials, internet, or real market access.
- [ ] **CI-02**: GitHub Actions include test, QuantConnect sync, cloud backtest, weekly validation, and dashboard health workflows when implementation reaches those phases.
- [ ] **CI-03**: Documentation covers product purpose, architecture, QuantConnect responsibilities, GitHub responsibilities, Render responsibilities, Telegram responsibilities, safety, strategy rules, scoring, risk management, order lifecycle, execution assumptions, backtesting methodology, bias risks, activation gates, setup, operations, recovery, troubleshooting, limitations, licensing, and disclaimer.
- [ ] **CI-04**: Security review verifies secret handling, read-only dashboard behavior, and absence of real-money trading paths.
- [ ] **CI-05**: Release preparation verifies automated tests, operational documentation, attribution, no fake performance artifacts, and no profitability claims.
- [ ] **CI-06**: Git status and change summaries distinguish executed checks from unexecuted checks.

## v2 Requirements

Deferred to future releases and not part of the v1 roadmap:

- Breakout Retest setup.
- Volatility Contraction / Base Breakout setup.
- Additional setup variants after v1 setups are independently validated.
- More advanced breadth measures after core regime logic is stable.
- Additional dashboard refinements after read-only v1 dashboard is operational.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Real-money trading | Explicitly prohibited by the product purpose and safety policy. |
| Real brokerage integrations | Would create a live-money path. |
| Leverage and margin | Explicitly excluded from v1 and incompatible with safety scope. |
| Short selling | Explicitly excluded from v1. |
| Options, futures, crypto, Forex | Explicitly excluded from v1. |
| Day trading, HFT, intraday scalping | Explicitly excluded from v1 trading style. |
| Manual dashboard order buttons | Render must remain read-only. |
| AI-driven unauditable trade decisions | v1 decisions must be deterministic and explainable. |
| Fake performance or portfolio artifacts | Explicitly prohibited. |
| Profit guarantees | Prohibited and misleading. |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| SAF-01 | Phase 1 | Complete |
| SAF-02 | Phase 1 | Complete |
| SAF-03 | Phase 1 | Complete |
| SAF-04 | Phase 1 | Complete |
| SAF-05 | Phase 1 | Complete |
| SAF-06 | Phase 1 | Complete |
| CFG-01 | Phase 1 | Complete |
| CFG-02 | Phase 1 | Complete |
| CFG-03 | Phase 1 | Complete |
| CFG-04 | Phase 1 | Complete |
| CFG-05 | Phase 1 | Complete |
| QC-01 | Phase 1 | Complete |
| QC-02 | Phase 2 | Pending |
| QC-03 | Phase 2 | Pending |
| QC-04 | Phase 2 | Pending |
| QC-05 | Phase 9 | Pending |
| UNI-01 | Phase 2 | Pending |
| UNI-02 | Phase 2 | Pending |
| UNI-03 | Phase 2 | Pending |
| UNI-04 | Phase 2 | Pending |
| UNI-05 | Phase 2 | Pending |
| REG-01 | Phase 2 | Pending |
| REG-02 | Phase 2 | Pending |
| REG-03 | Phase 2 | Pending |
| REG-04 | Phase 8 | Pending |
| IND-01 | Phase 2 | Pending |
| IND-02 | Phase 2 | Pending |
| IND-03 | Phase 2 | Pending |
| IND-04 | Phase 2 | Pending |
| IND-05 | Phase 2 | Pending |
| SET-01 | Phase 3 | Pending |
| SET-02 | Phase 3 | Pending |
| SET-03 | Phase 4 | Complete |
| SET-04 | Phase 4 | Complete |
| SET-05 | Phase 5 | Pending |
| SET-06 | Phase 5 | Pending |
| SET-07 | Phase 3 | Pending |
| MODE-01 | Phase 4.1 | Complete |
| MODE-02 | Phase 4.1 | Complete |
| MODE-03 | Phase 4.1 | Complete |
| TF-01 | Phase 4.1 | Complete |
| TF-02 | Phase 4.1 | Complete |
| TF-03 | Phase 4.1 | Complete |
| TF-04 | Phase 4.1 | Complete |
| TF-05 | Phase 4.1 | Complete |
| TF-06 | Phase 4.1 | Complete |
| TF-07 | Phase 4.1 | Complete |
| QC-MTF-01 | Phase 4.1 | Complete |
| QC-MTF-02 | Phase 4.1 | Complete |
| SET-MTF-01 | Phase 4.1 | Complete |
| SET-MTF-02 | Phase 4.1 | Complete |
| SET-MTF-03 | Phase 4.1, Phase 5 | Pending |
| BT-MTF-01 | Phase 4.1, Phase 7 | Pending |
| SCO-01 | Phase 5 | Pending |
| SCO-02 | Phase 5 | Pending |
| SCO-03 | Phase 5 | Pending |
| SCO-04 | Phase 6 | Pending |
| RISK-01 | Phase 6 | Pending |
| RISK-02 | Phase 6 | Pending |
| RISK-03 | Phase 6 | Pending |
| RISK-04 | Phase 6 | Pending |
| RISK-05 | Phase 6 | Pending |
| RISK-06 | Phase 6 | Pending |
| RISK-07 | Phase 6 | Pending |
| BT-01 | Phase 7 | Pending |
| BT-02 | Phase 7 | Pending |
| BT-03 | Phase 7 | Pending |
| BT-04 | Phase 7 | Pending |
| BT-05 | Phase 7 | Pending |
| BT-06 | Phase 7 | Pending |
| BT-07 | Phase 7 | Pending |
| BT-08 | Phase 7 | Pending |
| TEL-01 | Phase 8 | Pending |
| TEL-02 | Phase 8 | Pending |
| TEL-03 | Phase 8 | Pending |
| TEL-04 | Phase 8 | Pending |
| TEL-05 | Phase 8 | Pending |
| TEL-06 | Phase 8 | Pending |
| DASH-01 | Phase 9 | Pending |
| DASH-02 | Phase 9 | Pending |
| DASH-03 | Phase 9 | Pending |
| DASH-04 | Phase 9 | Pending |
| DASH-05 | Phase 9 | Pending |
| DASH-06 | Phase 9 | Pending |
| DASH-07 | Phase 9 | Pending |
| CI-01 | Phase 10 | Pending |
| CI-02 | Phase 10 | Pending |
| CI-03 | Phase 10 | Pending |
| CI-04 | Phase 10 | Pending |
| CI-05 | Phase 10 | Pending |
| CI-06 | Phase 10 | Pending |

**Coverage:**

- v1 requirements: 91 total
- Mapped to phases: 91
- Unmapped: 0

---
*Requirements defined: 2026-06-12*
*Last updated: 2026-06-14 after Phase 4.1 multi-timeframe insertion*
