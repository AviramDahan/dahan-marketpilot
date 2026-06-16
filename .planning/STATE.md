---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: QuantConnect Live Paper Trading
status: Blocked 15-05 Task 3: external QuantConnect paper smoke not verified
stopped_at: 15-05-PLAN.md Task 3 checkpoint: blocked_external_not_verified
last_updated: "2026-06-16T12:19:33.834Z"
last_activity: 2026-06-16
progress:
  total_phases: 5
  completed_phases: 2
  total_plans: 13
  completed_plans: 12
  percent: 92
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-06-15)

**Core value:** The system must provide an auditable paper-only swing-trading workflow where every signal, backtest, paper action, portfolio display, alert, and report is traceable to verified rules and numeric evidence.
**Current focus:** v1.1 QuantConnect Live Paper Trading. Phase 15 is in progress.

## Current Position

Phase: 15
Plan: 15-05-PLAN.md
Status: Blocked 15-05 Task 3: external QuantConnect paper smoke not verified
Last activity: 2026-06-16

Progress: [█████████░] 92%

## Performance Metrics

**Velocity:**

- Total plans completed: 52
- Average duration: 6 min for Phase 04 Plans 01-04
- Total execution time: 0.3 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01 | 4 | - | - |
| 02 | 4 | - | - |
| 03 | 3 | - | - |
| 04 | 4/4 | 22 min | 6 min |
| 04.1 | 4/4 | - | - |
| 05 | 3/3 | - | - |
| 06 | 5/5 | - | - |
| 07 | 5/5 | - | - |
| 08 | 4/4 | 76 min | 19 min |
| 09 | 8/8 | 169 min | 21 min |
| 10 | 4/4 | 45 min | 11 min |
| 10.1 | 5/5 | - | - |

**Recent Trend:**

- Last 5 plans: 10.1-01, 10.1-02, 10.1-03, 10.1-04, 10.1-05
- Trend: Phase 10.1 complete; all milestone audit runtime integration gaps closed locally

*Updated after each plan completion*
| Phase 04 P01 | 6 min | 2 tasks | 4 files |
| Phase 04 P02 | 6 min | 2 tasks | 3 files |
| Phase 04 P03 | 7 min | 2 tasks | 6 files |
| Phase 04 P04 | 3 min | 2 tasks | 4 files |
| Phase 04.1 P01 | - | StrategyMode config | 4 files |
| Phase 04.1 P02 | - | Timeframe contracts | 3 files |
| Phase 04.1 P03 | - | Setup MTF adaptation | 4 files |
| Phase 04.1 P04 | - | Docs and verification | 10 files |
| Phase 05 P01 | - | RSL setup | 8 files |
| Phase 05 P02 | - | Scoring | 4 files |
| Phase 05 P03 | - | Ranking | 5 files |
| Phase 06 P01 | - | Portfolio constraints and sizing | 10 files |
| Phase 06 P02 | - | Order lifecycle and idempotency | 7 files |
| Phase 06 P03 | - | Stops, targets, exits, and holding period | 10 files |
| Phase 06 P04 | - | Audit journal, restart recovery, corporate-action placeholders | 8 files |
| Phase 06 P05 | - | Notification-domain events and fake transport | 6 files |
| Phase 07 P01 | - | Backtesting assumptions and no-look-ahead validation | 10 files |
| Phase 07 P02 | - | Backtest report contracts and windows | 7 files |
| Phase 07 P03 | - | Chronological validation and sensitivity analysis | 5 files |
| Phase 07 P04 | - | Benchmark comparison and activation gates | 6 files |
| Phase 07 P05 | - | Report generation and preview notifications | 9 files |
| Phase 08 P01 | 10 min | Paper mode gates and QuantConnect deployment contracts | 10 files |
| Phase 08 P02 | 12 min | QuantConnect reconciliation, restart recovery, and protective recovery | 12 files |
| Phase 08 P03 | 9 min | 3 tasks | 10 files |
| Phase 08 P04 | 45 min | Telegram alert coverage, regime transitions, daily summaries, failure isolation | 10 files |
| Phase 09 P01 | 28min | 3 tasks | 6 files |
| Phase 09 P02 | 22min | 3 tasks | 10 files |
| Phase 09 P03 | 24min | 2 tasks | 9 files |
| Phase 09 P06 | 18min | 2 tasks | 7 files |
| Phase 09 P04 | 19min | 2 tasks | 8 files |
| Phase 09 P05 | 18min | 2 tasks | 7 files |
| Phase 09 P07 | 22min | 2 tasks | 9 files |
| Phase 09 P08 | 18min | 3 tasks | 9 files |
| Phase 10 P01 | 12min | 2 tasks | 6 files |
| Phase 10 P02 | 10min | 2 tasks | 4 files |
| Phase 10 P03 | 9min | 2 tasks | 5 files |
| Phase 10 P04 | 14min | 3 tasks | 4 files |
| Phase 10.1 P01 | 7min | 3 tasks | 4 files |
| Phase 10.1 P02 | 9min | 3 tasks | 3 files |
| Phase 10.1 P03 | 7min | 3 tasks | 4 files |
| Phase 10.1 P04 | 8min | 3 tasks | 4 files |
| Phase 10.1 P05 | - | 3 tasks | 11 files |
| Phase 14 P01 | 70min | 2 tasks | 3 files |
| Phase 14 P03 | 5min | 2 tasks | 2 files |
| Phase 14-data-sync-dashboard-integration P04 | 10min | 3 tasks | 2 files |
| Phase 15 P01 | 56min | 2 tasks | 5 files |
| Phase 15 P02 | 14min | 2 tasks | 4 files |
| Phase 15 P03 | 9min | 2 tasks | 6 files |
| Phase 15 P04 | 10min | 2 tasks | 3 files |
| Phase 15 P05 | 9min | 2/3 tasks | 6 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Initialization: Use GSD planning artifacts and stop before Phase 1.
- Initialization: Git repository initialized, but no commits are allowed without explicit user request.
- Initialization: QuantConnect is source of truth for paper portfolio and backtest state.
- Initialization: Render is read-only and Telegram is non-authoritative notification infrastructure.
- Phase 3: Trend Pullback uses completed daily bars only and returns setup evidence, not trade instructions.
- Phase 4 planning: Volume Breakout plans are verified and ready to execute with current-bar exclusion, volume confirmation, and evidence-only boundaries.
- [Phase 4]: Phase 4 Plan 01: Volume Breakout prior resistance uses bars[-lookback_bars - 1 : -1] to exclude the signal bar.
- [Phase 4]: Phase 4 Plan 01: Volume Breakout remains a separate setup evidence module with no order, sizing, classification, backtest, Telegram, Paper, or Live behavior.
- [Phase 04]: Phase 4 Plan 02: Completed-close breakout confirmation - Volume Breakout confirms breakouts only when the completed daily close exceeds buffered prior resistance, preserving current-bar exclusion and avoiding intraday high validity.
- [Phase 04]: Phase 4 Plan 02: Evaluator-calculated reward/risk proxy - Volume Breakout calculates reward/risk proxy from projected setup evidence, latest close, and prior resistance instead of accepting a precomputed setup input.
- [Phase 04]: Phase 4 Plan 03: Volume Breakout evidence remains future-consumable setup evidence only; no score, confidence, ranking, classification, BUY/WATCH/AVOID labels, or trade instruction were added. D-14 and D-15 reserve full scoring and classifications for Phase 5 while keeping Phase 4 auditable.
- [Phase 04]: Phase 4 Plan 03: Early rejected Volume Breakout results include core evidence for resistance lookback, breakout buffer, and regime. Audit output should not disappear on early fail-closed paths.
- [Phase 04]: Phase 4 Plan 04: Volume Breakout stale data uses SymbolData.future_signal_ready(..., stale=...) and rejects as DATA_NOT_READY with symbol_data_stale evidence.
- Phase 4: Volume Breakout uses completed daily bars, current-bar-excluded prior resistance, volume confirmation, stale-data rejection, and setup evidence only.
- Phase 5 planning: Relative Strength Leader, MarketPilot Score, classification/confidence, one-candidate-per-symbol ranking, and Combined Swing readiness gate are planned across 3 waves with full requirements and decision coverage.
- Phase 4.1 planning: StrategyMode and MTF signal foundations are inserted before Phase 5. Supported modes are exactly `daily_only`, `daily_filter_4h_setup`, and `daily_filter_4h_setup_1h_optional`; `daily_only` remains default and benchmark.
- Phase 4.1 planning: Recommended 4H policy is market-open anchored, RTH-only, `America/New_York`, with partial-session bars marked non-signal by default.
- Phase 4.1 planning: 1H is optional confirmation only and cannot independently create trades or override failed Daily, invalid 4H, `RISK_OFF`, stale data, hard rejection, or invalid reward/risk.
- Phase 4.1 execution: `marketpilot/timeframes.py`, `load_strategy_config()`, extended `SetupTiming`, and MTF setup evidence are implemented with 135 passing tests.
- Phase 5 execution: Relative Strength Leader, MarketPilot Score, audit classifications, confidence, one-candidate-per-symbol ranking, and disabled Combined Swing readiness gate are implemented with 164 passing tests.
- Phase 6 discussion: Default risk settings are 1% per trade, 10 max open positions, 30% sector exposure, 3 max new entries per day, and 15% max allocation per position.
- Phase 6 discussion: Position sizing uses risk amount divided by stop distance; invalid stop distance rejects fail-closed, and cash shortage can reduce quantity only when minimum reward/risk and quantity remain valid.
- Phase 6 discussion: Phase 6 creates order intent, lifecycle, exit, persistence, and notification-domain models only; actual QuantConnect Paper order submission remains Phase 8.
- Phase 6 discussion: QuantConnect remains authoritative on restart mismatch; local JSONL audit journal is append-only recovery and audit context.
- Phase 6 discussion: Notification-domain events are typed, sanitized, transport-independent, and delivery failure must never block safety logic.
- Phase 6 planning: Five executable plans now cover risk sizing, order lifecycle/idempotency, exits, persistence/recovery, and notification-domain events.
- Phase 6 execution: Portfolio risk, sizing, lifecycle, exits, JSONL audit journal, restart recovery placeholders, and notification-domain events are implemented with 215 passing tests.
- Phase 7 discussion: QuantConnect Cloud/LEAN is official backtest authority, with deterministic local harnesses for no-look-ahead and timing validation.
- Phase 7 discussion: Backtest and future Paper Trading must reuse shared strategy-rule modules; adapters must not duplicate strategy logic.
- Phase 7 discussion: Real backtest artifacts require documented real runs; otherwise only schemas, parsers, fixtures, and examples are allowed with no performance claims.
- Phase 7 discussion: Missing QuantConnect access is recorded as not_run while offline deterministic validation continues.
- Phase 7 discussion: Activation gates default to not approved for Paper until validation passes, and notification preview uses fake transport only.
- Phase 7 planning: Five executable plans cover backtest execution assumptions, report windows, chronological validation, benchmark/activation gates, and notification preview artifacts.
- Phase 7 execution: Backtesting contracts, report generation, chronological validation, sensitivity analysis, benchmark comparison, activation gates, and preview notifications are implemented with 247 passing tests.
- Phase 8 Plan 01 execution: Paper mode gates, Limited Paper caps, transition audit records, and QuantConnect Paper deployment prerequisite contracts are implemented with local tests passing.
- Phase 8 Plan 01 decision: `validation_passed` remains inactive for Paper Trading; only `approved_for_limited_paper` and `approved_for_full_paper` can be Paper-order eligible.
- Phase 8 Plan 01 decision: QuantConnect Paper deployment is operator-run metadata only; missing prerequisites return `not_configured` or `not_run` and never fake deployment state.
- Phase 8 Plan 02 execution: QuantConnect Paper snapshots, reconciliation decisions, QuantConnect-first restart recovery, and protective recovery are implemented with 9 targeted tests and the full local suite passing.
- Phase 8 Plan 02 decision: QuantConnect Paper snapshots remain authoritative for cash, equity, holdings, orders, fills, deployment status, algorithm status, and performance; local lifecycle/audit records are mirror context only.
- Phase 8 Plan 02 decision: Reconciliation mismatch blocks new entries, preserves exit obligations, emits high-severity system-domain events, and requires explicit recovery.
- Phase 8 Plan 02 decision: Restart recovery fails closed when QuantConnect is unavailable and never promotes local audit history into authoritative Paper state.
- Phase 8 Plan 02 decision: Protective recovery may emit notification-domain events, but delivery success or failure cannot alter recovery decisions or unblock entries.
- [Phase 08]: Phase 8 Plan 03: Telegram real delivery remains disabled by default and requires explicit config plus externally supplied token and chat target.
- [Phase 08]: Phase 8 Plan 03: NotificationDomainEvent remains the internal contract; Telegram sendMessage is only an outbound adapter.
- [Phase 08]: Phase 8 Plan 03: Telegram delivery success, failure, duplicate suppression, and rate limiting cannot control Paper gates, lifecycle, reconciliation, or protective recovery.
- [Phase 08]: Phase 8 Plan 03: Telegram messages are plain text by default, include the simulated-paper warning, omit paid broadcast fields, and remove secret-like or unsafe profitability text.
- [Phase 08]: Phase 8 Plan 04: Required Telegram alert families are covered by stable transport-neutral event types while preserving the Phase 6 notification enum contract.
- [Phase 08]: Phase 8 Plan 04: Regime alerts emit only on actual previous/current state transitions; unchanged states produce no alert.
- [Phase 08]: Phase 8 Plan 04: Daily summaries are scheduled end-of-day notification artifacts with Paper mode, counts, warnings, and QuantConnect authority labels, not portfolio authority.
- [Phase 08]: Phase 8 Plan 04: Telegram delivery results explicitly record `controls_safety_logic=false` and `delivery_required_for_safety=false`.
- [Phase 10.1]: Phase 10.1 Plan 01: Runtime orchestration contracts are pure MarketPilot dataclasses; LEAN/API objects stay at adapter boundaries. â€” Preserves paper-only safety and keeps QuantConnect-specific objects in later adapter plans.
- [Phase 10.1]: Phase 10.1 Plan 01: Runtime results default to paper-only audit evidence and cannot claim executed QuantConnect orders or fills without QuantConnect-authoritative state. â€” Prevents fake execution, fake fills, and local mirror authority.
- [Phase 10.1]: Phase 10.1 Plan 01: Setup registry includes implemented independent setup evaluators only and does not enable Combined Swing. â€” Keeps Plan 10.1-01 scoped to existing setup evidence and avoids adding new strategy behavior.
- [Phase 10.1]: Phase 10.1 Plan 02: Runtime paper intent readiness requires validation, paper mode, QuantConnect reconciliation, QuantConnect-authoritative portfolio input, risk acceptance, and idempotency evidence. â€” Preserves paper-only safety and prevents score/ranking evidence from becoming an order instruction.
- [Phase 10.1]: Phase 10.1 Plan 02: Scoring and BUY_CANDIDATE classification remain evidence only and do not submit orders or bypass risk/reconciliation gates. â€” Keeps high scores, classifications, and setup evidence separate from execution authority.
- [Phase 10.1]: Phase 10.1 Plan 02: Reconciliation mismatch or missing QuantConnect snapshot blocks new entries, preserves exit obligations, and emits system events that do not control safety logic through delivery. â€” Maintains QuantConnect source-of-truth behavior while keeping notification transport non-authoritative.
- [Phase 10.1]: LEAN runtime integration is adapter-only; setup, scoring, ranking, risk, reconciliation, paper eligibility, and notification decisions remain delegated to marketpilot.runtime_orchestrator. â€” Keeps QCAlgorithm-specific objects at the edge and avoids duplicating strategy logic in lean/main.py.
- [Phase 10.1]: Dynamic universe hooks are allowed only through audited bridge wiring. â€” The old blanket add_universe ban was too broad for INT-02, while bridge static tests keep broker, uncontrolled order, credential, borrowing-style, and unsupported asset paths forbidden.
- [Phase 10.1]: Dashboard/Object Store export and external QuantConnect execution remain not_run evidence in Plan 10.1-03. â€” No operator-run QuantConnect credentials or external execution occurred during this plan.
- [Phase 14]: Plan 01 sync remains a single-cycle callable module; scheduling stays deferred to Phase 16.
- [Phase 14]: Plan 01 local JSONL records are audit/display mirrors only; QuantConnect remains authoritative for Paper portfolio state.
- [Phase 14]: Plan 01 discrepancy handling emits a high-severity system-domain event but never auto-corrects local or QuantConnect state.
- [Phase 14]: Plan 03: Overview converts UTC source/cache timestamps to ET only at the display boundary with zoneinfo.ZoneInfo('America/New_York').
- [Phase 14]: Plan 03: Missing dashboard portfolio values remain unavailable; the overview derives unrealized P&L only from present QuantConnect holding rows.
- [Phase 14]: Plan 03: SyncPortfolioView exposes freshness_level for banner rendering while preserving the existing read-only line-based overview contract.
- [Phase 14]: Phase 14 Plan 04: Dashboard sync_jsonl tests stay independent of marketpilot.sync and verify only the JSONL file contract consumed by dashboard.data.
- [Phase 14]: Phase 14 Plan 04: Sync tests patch QCApiClient and reconcile_quantconnect_state boundaries directly so no real QuantConnect API call can occur.
- [Phase 15]: QuantConnect command API success is command-delivery success only; order and fill authority comes from /live/orders/read. — Prevents local command delivery from being misread as an executed order or fill, preserving QuantConnect source-of-truth semantics.
- [Phase 15]: Paper deployment payloads are hardcoded to QuantConnectBrokerage live-paper with id-only QuantConnect dataProviders and no real brokerage credential path. — Maintains simulated-paper-only safety while matching official QuantConnect live create payload requirements.
- [Phase 15]: Plan 02 signal command payloads carry MarketPilot trace fields and explicitly mark command delivery as not order execution. — Prevents command API success from being misread as an executed order or fill.
- [Phase 15]: Plan 02 deployment and signal idempotency ledgers require caller-supplied paths and do not write repo data/ unless explicitly configured. — Preserves local artifacts and keeps JSONL ledgers as explicit audit mirrors only.
- [Phase 15]: Plan 02 pre-submit sync gate trusts only the latest Phase 14 JSONL record after UTC source_timestamp, max-age, success status, and reconciliation_clean checks pass. — Blocks stale, error, missing, or mismatched sync state before any QuantConnect command API call.
- [Phase 15]: Plan 03 LEAN accepts only MarketPilot signal commands with paper-only, freshness, schema, supported-symbol, and duplicate-idempotency validation before any order call.
- [Phase 15]: Plan 03 allows only one tagged self.market_order(validation.symbol, validation.quantity, tag=validation.tag) path inside on_command.
- [Phase 15]: Plan 03 order-event evidence is sanitized trace context only and does not become local order/fill authority.
- [Phase 15]: Plan 04 preserves unknown QuantConnect live-order statuses as raw evidence with parse warnings instead of inventing local meanings.
- [Phase 15]: Plan 04 emits fill audit records only when QuantConnect provides fill quantity evidence; local code does not infer fills from status alone.
- [Phase 15]: Plan 04 trace queries read append-only audit records by signal_id or idempotency_key without becoming order or portfolio authority.
- [Phase 15]: Plan 05 remains blocked_external_not_verified for PTD-01/PTD-02 external evidence and running-QuantConnect delivery until a credentialed paper-only smoke run records sanitized evidence.
- [Phase 15]: Plan 05 offline E2E tests prove local signal-command-LEAN-audit behavior only; mocks and fake fills are not real QuantConnect execution evidence.

### Pending Todos

- Close runtime orchestrator gap: QuantConnect data -> setup evaluation -> scoring/ranking -> risk/order lifecycle -> paper reconciliation -> Telegram -> dashboard.
- Close LEAN bridge gap: wire `lean/main.py` to safe MarketPilot strategy/runtime contracts without adding any real-money path.
- Close dashboard source gap: add an approved QuantConnect Object Store/API/export producer or fetcher for read-only dashboard runtime data.

### Roadmap Evolution

- Phase 10.1 inserted after Phase 10 (URGENT): Close gap: runtime orchestrator for strategy-to-paper E2E flow.

### Blockers/Concerns

- Later phases require user-managed QuantConnect account/subscription/API credentials, Telegram bot/chat ID, GitHub Secrets, and Render configuration.
- Exact QuantConnect API endpoints, Object Store behavior, notification APIs, Render deployment details, and Streamlit APIs must be re-verified during the relevant implementation phases.
- Phase 5 execution should record the local Python version because the current shell has Python 3.10 while project metadata requires Python >=3.11 for strict/release validation.
- Phase 9 must keep Render dashboard read-only and source Paper state from verified QuantConnect-approved paths.
- Phase 15 Plan 05 external QuantConnect paper smoke is blocked_external_not_verified because QUANTCONNECT_USER_ID, QUANTCONNECT_API_TOKEN, QC_PROJECT_ID, QC_DEPLOY_ID, QC_COMPILE_ID, QC_NODE_ID, and QC_VERSION_ID are not configured locally.

## Deferred Items

Items acknowledged and carried forward from previous milestone close:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| Future setup idea | Breakout Retest | Deferred | Phase 4.1 planning |
| Future setup idea | Volatility Contraction / Base Breakout | Deferred | Phase 4.1 planning |

## Session Continuity

Last session: 2026-06-16T12:17:59.017Z
Stopped at: 15-05-PLAN.md Task 3 checkpoint: blocked_external_not_verified
Resume file: .planning/phases/15-paper-trading-order-flow/15-05-SUMMARY.md
