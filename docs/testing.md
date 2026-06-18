# Testing

Phase 1 and Phase 2 tests are deterministic and offline.

Run the local suite with:

```powershell
python -m pytest
```

Tests must not require:

- Internet access.
- QuantConnect credentials.
- Telegram credentials.
- Render credentials.
- Broker credentials.
- Real market data.

Phase 1 automated tests cover repository safety, configuration validation,
FX seed behavior, foundational models, static dashboard safety, and static LEAN
shell safety as those artifacts are introduced.

Current Phase 1 suites:

- `tests/test_safety.py`
- `tests/test_configuration.py`
- `tests/test_models.py`
- `tests/test_project_files.py`
- `tests/test_lean_static_safety.py`
- `tests/test_dashboard.py`
- `tests/test_quantconnect_verification_docs.py`
- `tests/test_data_quality.py`
- `tests/test_universe.py`
- `tests/test_indicators.py`
- `tests/test_symbol_data.py`
- `tests/test_regime.py`
- `tests/test_trend_pullback_contract.py`
- `tests/test_trend_pullback_detection.py`
- `tests/test_trend_pullback_rejections.py`
- `tests/test_trend_pullback_explanations.py`
- `tests/test_trend_pullback_safety.py`

QuantConnect verification contracts are documented in
`docs/quantconnect_verification.md`.

LEAN compile verification is external and may require Docker, the LEAN CLI,
`lean login`, `lean init`, and QuantConnect organization access. When available,
run:

```powershell
lean build
```

If LEAN prerequisites are unavailable, record the check as not run. Do not store
credentials in this repository or paste them into chat.

The local dashboard preview is optional and must remain local-only:

```powershell
streamlit run dashboard/app.py
```

The Phase 1 dashboard shell must display `No live data connected` and must not
connect to QuantConnect, Render, Telegram, brokers, or live market data.

Phase 1 does not test strategy signals, order lifecycle, portfolio state,
Telegram delivery, Render deployment, QuantConnect Paper Trading, or real
market data access.

Phase 2 universe tests use offline fixtures only. They verify strict
data-quality rejection, accepted/rejected counts, additions, removals, sector
distribution, and QuantConnect API contract documentation without importing
QuantConnect runtime modules.

Phase 2 indicator and SymbolData tests verify readiness-first behavior,
invalid-data rejection, cleanup for removed symbols, and no strategy signal or
order behavior.

Phase 2 regime tests verify SPY/QQQ RISK_ON, NEUTRAL, and RISK_OFF
classification, transition detection, unchanged-state suppression, unready or
missing benchmark rejection, and entry-gate-only behavior.

Phase 3 Trend Pullback contract tests verify setup vocabulary, completed daily
bar timing, configuration defaults, hard rejection reason coverage, and absence
of order, classification, Telegram, live deployment, or fake backtest behavior.

Phase 3 Trend Pullback detection and rejection tests verify valid EMA20/EMA50
pullbacks, close above prior completed bar high, RISK_OFF rejection,
data-readiness rejection, EMA50 break rejection, pullback-window rejection,
ATR/reward-risk rejection, weak recovery volume, deferred earnings risk, and
completed daily-bar timing.

Phase 3 Trend Pullback explanation and safety tests verify numeric evidence,
readable rejection explanations, absence of total score/confidence/ranking
fields, and absence of order, classification, Telegram, credential, live
deployment, or fake backtest behavior.

Phase 4 Volume Breakout tests are deterministic and offline. They verify
current-bar-excluded prior resistance, completed-close breakout confirmation,
volume confirmation, SET-04 hard gates, stale SymbolData readiness rejection,
evaluator-calculated reward/risk proxy, evidence completeness, readable
explanations, setup-only output, and forbidden behavior absence.

Current Phase 4 suites:

- `tests/test_volume_breakout_contract.py`
- `tests/test_volume_breakout_detection.py`
- `tests/test_volume_breakout_rejections.py`
- `tests/test_volume_breakout_explanations.py`
- `tests/test_volume_breakout_safety.py`

Phase 4 tests must not require QuantConnect, Telegram, Render, broker
credentials, internet access, live market data, fake backtest results, fake
portfolio values, or profitability claims.

## Phase 4.1 Multi-Timeframe Tests

Phase 4.1 tests must verify exactly three strategy modes:
`daily_only`, `daily_filter_4h_setup`, and
`daily_filter_4h_setup_1h_optional`. Missing, empty, invalid, or unsupported
modes fail closed, and strategy mode must remain separate from environment mode.

Tests must cover completed daily, completed 4H, and completed 1H timing;
independent Daily/4H/1H readiness; RTH-only behavior; `America/New_York` DST;
holidays; early closes; partial-session bars; stale data; no future bars; no
incomplete bars; and no same-bar execution assumptions.

Future backtesting must compare the three regular modes, a mandatory-1H variant
for backtesting only, different 4H alignment policies, and a 2H alternative if
technically justified. Comparison reports should include candidate/trade counts,
win rate, average RR/R, max drawdown, holding period, missed opportunities,
false breakout rate, delayed-entry impact, fees/slippage, year-by-year,
out-of-sample, and walk-forward results.

Current Phase 4.1 suites:

- `tests/test_strategy_config.py`
- `tests/test_timeframes.py`
- `tests/test_setup_mtf_adaptation.py`

Current Phase 5 suites:

- `tests/test_relative_strength_contract.py`
- `tests/test_relative_strength_detection.py`
- `tests/test_relative_strength_rejections.py`
- `tests/test_relative_strength_explanations.py`
- `tests/test_relative_strength_safety.py`
- `tests/test_scoring.py`
- `tests/test_ranking.py`

Current Phase 6 risk suites:

- `tests/test_risk_contract.py`
- `tests/test_position_sizing.py`
- `tests/test_portfolio_constraints.py`
- `tests/test_risk_safety.py`
- `tests/test_order_lifecycle_contract.py`
- `tests/test_order_lifecycle_transitions.py`
- `tests/test_order_idempotency.py`
- `tests/test_order_lifecycle_safety.py`
- `tests/test_exit_contract.py`
- `tests/test_stops_targets.py`
- `tests/test_partial_trailing_holding_period.py`
- `tests/test_exit_regime_authority.py`
- `tests/test_exit_safety.py`
- `tests/test_audit_journal.py`
- `tests/test_restart_recovery.py`
- `tests/test_split_delisting_placeholders.py`
- `tests/test_persistence_safety.py`
- `tests/test_notification_events.py`
- `tests/test_notification_fake_transport.py`
- `tests/test_notification_dedup_rate_limit.py`
- `tests/test_notification_safety.py`

These tests cover risk config safety, risk-based sizing, allocation/cash
limits, sector exposure, position count, daily entries, and static scans proving
no order submission or external delivery behavior exists in risk code.
Lifecycle tests cover state contracts, valid and forbidden transitions, stable
idempotency keys, and absence of submission behavior.
Exit tests cover structural stops, 2R targets, partial-exit modeling, trailing
stop disabled defaults, maximum holding period, and the rule that RISK_OFF does
not erase existing exit obligations.
Persistence tests cover append-only JSONL audit records, QuantConnect-wins
restart mismatch handling, safe split/delisting placeholders, and absence of
fake portfolio authority.
Notification-domain tests cover typed event contracts, payload sanitization,
fake collector behavior, delivery-failure isolation, deduplication, rate
limiting, and absence of real Telegram/network delivery.

Phase 7 backtesting and validation tests are deterministic and offline. They
cover config safety, QuantConnect not-run records, no-look-ahead checks,
current-bar exclusion, signal/fill separation, same-bar ambiguity, stale data,
strategy-mode timing alignment, report source labels, unavailable validation
windows, chronological validation, sensitivity analysis, SPY/QQQ benchmark
comparison, activation gates, report generation, preview notifications, and
artifact safety.

## Phase 10.1 Runtime Integration Tests

Phase 10.1 closes the strategy-to-paper E2E flow gap identified by milestone
audit. Tests are deterministic and offline. Run:

```powershell
python -m pytest tests/test_runtime_orchestrator.py tests/test_runtime_reconciliation_gate.py tests/test_lean_runtime_bridge_static.py tests/test_dashboard_object_store_source.py tests/test_runtime_notification_emission.py -q
```

Current Phase 10.1 suites:

- `tests/test_runtime_orchestrator.py`
- `tests/test_runtime_reconciliation_gate.py`
- `tests/test_lean_runtime_bridge_static.py`
- `tests/test_dashboard_object_store_source.py`
- `tests/test_runtime_notification_emission.py`

These tests cover the runtime orchestrator pipeline (setup → scoring → ranking →
risk → order intents), reconciliation gate decisions, static LEAN bridge safety,
dashboard Object Store source/loader, and runtime notification emission with
Telegram failure isolation.

Key safety invariants proven:

- Runtime pipeline is pure and side-effect-free.
- Telegram delivery success/failure cannot affect trading, exits,
  reconciliation, recovery, or safety decisions.
- Dashboard export is read-only and non-authoritative.
- QuantConnect remains the sole authoritative source for Paper portfolio state.

## Security Release Gates

Phase 10 security release gates are deterministic and offline. Run:

```powershell
python -m pytest tests/test_security_release_gates.py tests/test_safety.py tests/test_dashboard_read_only.py tests/test_paper_trading_safety.py tests/test_backtest_artifact_safety.py -q
```

These tests inspect workflow files, security review evidence, dashboard
read-only boundaries, Paper Trading safety, and fake-performance rejection.

GitHub Actions Secrets may be configured outside the repository for guarded
external checks:

- `QUANTCONNECT_USER_ID`
- `QUANTCONNECT_API_TOKEN`
- `QUANTCONNECT_PROJECT_ID`
- `DASHBOARD_HEALTH_URL`
- `DASHBOARD_PASSWORD`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

Unexecuted external checks are not passed checks. Missing QuantConnect,
Telegram, Render, broker, dashboard, operator-confirmation, or package
prerequisites must be recorded as `skipped` or `not_run`.

## Phase 15 Paper Order Flow Tests

Phase 15 tests are deterministic and offline unless explicitly labeled as a
credentialed QuantConnect paper smoke check. Offline tests use fake
QuantConnect clients, fake sync JSONL records, fake LEAN runtime objects, and
temporary audit files. They do not prove real QuantConnect execution.

Run the targeted Phase 15 order-flow regression command with:

```powershell
pytest tests/test_paper_order_flow_e2e.py tests/test_paper_order_flow.py tests/test_lean_command_flow.py tests/test_qc_api.py tests/test_sync.py -q
```

When local Python satisfies the project version requirement, also run:

```powershell
pytest -q
```

Credentialed paper smoke verification requires the following environment
variable names to be configured outside the repository and outside chat:

- `QUANTCONNECT_USER_ID`
- `QUANTCONNECT_API_TOKEN`
- `QC_PROJECT_ID`
- `QC_DEPLOY_ID`
- `QC_COMPILE_ID`
- `QC_NODE_ID`
- `QC_VERSION_ID`
- `QC_ORGANIZATION_ID` (optional; discovered through `/account/read` when possible)

If these are absent, record the smoke status as
`blocked_external_not_verified`. Do not treat mocks, fake fills, or `not_run`
as real QuantConnect evidence.

Current external evidence from 2026-06-16:

- Authenticated `/live/list`, `/live/read`, and `/live/orders/read` smoke
  passed against the user-managed Paper deployment for project `32900381`.
- The deployment was read as `running`, with equity `27027.03` and 0 live
  orders.
- Follow-up smoke synced Phase 15 files to QuantConnect, compiled successfully,
  created a new Paper deployment, and received `success=true` from
  `/live/commands/create`.
- Callback-to-order smoke remains blocked because no `on_command` debug log or
  live order appeared after polling `/live/logs/read` and `/live/orders/read`.
- Phase 15-06 added `scripts/qc_command_smoke.py`, which refuses to run unless
  `MARKETPILOT_QC_COMMAND_SMOKE_ENABLED=1` and redacts secret environment
  values from output.
- A typed command probe also returned command API success, but still produced 0
  callback logs and 0 live orders after 12 polls.
- Phase 15-07 added `scripts/qc_command_dispatch_probe.py`, which refuses to
  run unless `MARKETPILOT_QC_DISPATCH_PROBE_ENABLED=1`. It dry-runs without
  network calls, generates a no-order Python echo algorithm, and tests generic
  Commands API dispatch before MarketPilot order logic is tested again.
- Run the dispatch probe dry-run with:

```powershell
$env:MARKETPILOT_QC_DISPATCH_PROBE_ENABLED="1"
python scripts\qc_command_dispatch_probe.py --dry-run --skip-deploy
```

Credentialed Phase 15-07 dispatch evidence: compile and Paper deploy succeeded,
and `/live/commands/create` returned success for a no-order generic echo probe,
but immediate and delayed `/live/logs/read` polling returned 0 logs and no
`MARKETPILOT_DISPATCH_PROBE_RECEIVED` marker. Record this status as
`blocked_external_dispatch_not_observed`.

Phase 15-08 adds an Object Store fallback smoke. It is also disabled by
default:

```powershell
$env:MARKETPILOT_QC_OBJECT_STORE_SMOKE_ENABLED="1"
python scripts\qc_object_store_signal_smoke.py --dry-run --skip-deploy
```

Credentialed Phase 15-08 evidence: local Object Store wrappers and LEAN polling
tests passed, and the injected-key Paper algorithm compiled and deployed
successfully. The first Object Store upload attempt returned `Organization not
found` because the multipart request inherited a JSON `Content-Type`; Phase
15-09 corrected this at the API client layer.

Phase 15-09 adds a safer Object Store preflight. Use diagnose-only before any
full fallback smoke:

```powershell
$env:MARKETPILOT_QC_OBJECT_STORE_SMOKE_ENABLED="1"
python scripts\qc_object_store_signal_smoke.py --diagnose-only --skip-deploy
```

Credentialed Phase 15-09 evidence: diagnose-only returned
`object_store_write_available`; `/object/set` returned `success=true`,
`/object/properties` returned JSON metadata, and cleanup succeeded. The run did
not compile, deploy, send commands, poll logs, or poll orders.

Full Phase 15-09 fallback smoke then wrote the signal object, compiled to
`BuildSuccess`, deployed a Paper algorithm, restored `main.py`, cleaned up the
object, and stopped the deployment. Eighteen polls observed 0 logs, 0 tagged
orders, and no receipt marker. This exposed a local log-read request shape gap.

Phase 15-10 corrected `/live/logs/read` to use the official `startLine`,
`endLine`, and `deploymentLogs` fields. The rerun wrote the signal object,
compiled to `BuildSuccess`, deployed a Paper algorithm, restored `main.py`,
cleaned up the object, and stopped the deployment. Live logs showed the Object
Store receipt marker, Object Store acceptance marker, and a QuantConnect Paper
order event with status `Submitted`; `/live/orders/read` returned 0 orders
during the smoke window. Record this status as
`object_store_delivery_receipt_or_rejection_observed` and keep order/fill
authority pending until `/live/orders/read` returns a tagged order, fill, or
rejection.

Phase 15-11 makes temporary Paper deployments safer: Object Store fallback
smokes stop deployments by default after polling and expose `--keep-running`
only for an explicit operator-approved next-open or market-hours observation.
A short credentialed auto-stop check created a Paper deployment, cleaned the
probe object, and returned `stop_success=true`.

Phase 15-12 tightens the order-authority smoke:

- `qc_object_store_signal_smoke.py` now matches `/live/orders/read` rows only
  when the order tag exactly equals the current run's expected
  `mp:<signal_id>:<idempotency_key>` value.
- Stale MarketPilot-tagged orders from older deployments are counted separately
  and cannot satisfy the authority gate.
- `lean/main.py` defers an accepted Object Store signal when the symbol has no
  tradeable price yet, leaving the Object Store key unprocessed so a later
  scheduled poll can retry after data arrives.

Credentialed Phase 15-12 market-hours evidence: Object Store write, compile,
Paper deploy, original-file restore, object cleanup, and deployment stop all
succeeded. Live logs for deployment `L-3eccd7fbf41cc4b0aa944d500f760a90`
showed Object Store receipt, Object Store acceptance, `Submitted`, and `Filled`
for SPY quantity 1 at fill price `$751.31`. `/live/orders/read` still did not
return the current run's exact order tag; it returned only an older tagged order
from deployment `L-103091222fcd6eee4aae06e1de635e38`. Record this status as
`live_logs_filled_but_orders_read_current_tag_missing`; Phase 15 remains open
until the official orders endpoint returns the current tagged order, fill, or
rejection, or an approved QuantConnect-authority alternative is documented.

Phase 15-13 closes that authority gate. `qc_object_store_signal_smoke.py` now
polls `/live/orders/read` with `start=0,end=1000`, preserves exact current-tag
order evidence in top-level `qc_order_evidence_*` fields, and cleans up the
Object Store probe on deploy failure as well as successful runs. Credentialed
Paper-only evidence: key
`32900381/marketpilot/signals/object-store-smoke-20260617143733.json`, compile
`be2643e583a354020fbc7a08e1a136fc-e62f04e374002b91ed7c97cf9ee17189`,
deployment `L-d62998269941f7f00ba48804a092c2b7`, exact tag
`mp:qc-object-store-sig-20260617143733:qc-object-store-order-20260617143733`,
order id `1`, status `3`, Submitted and Filled events, fill quantity `1`, fill
price `$750.08`, object cleanup success, and deployment stop success. Phase 15
order authority is passed for simulated Paper Trading only.

Phase 16.2 keeps a stricter deployed-product UAT gate. QuantConnect live logs
can support the narrative for a Paper order event, but they are partial evidence
only. UAT-01 requires a sanitized `/live/orders/read` row with non-empty order
id, matching tag/correlation/idempotency context, symbol, filled quantity,
filled status, timezone-aware timestamp, and Paper-only confirmation, plus the
same non-empty correlation id across signal/probe, scoring, risk, sync,
dashboard, and Telegram segments. Off-hours diagnostics added paginated
`/live/orders/read` parsing, bounded read-only retry metadata, and preflight
deploy-id source/hash diagnostics; none of these helpers submit orders or
convert live-log fills into authority evidence.

## Phase 16 Production Scheduler Tests

Phase 16 tests are deterministic and offline. They verify the autonomous
scheduler boundaries without requiring QuantConnect, Telegram, Render,
internet access, live market data, or the local computer to be part of
production operation.

Run the targeted Phase 16 suite with:

```powershell
python -m pytest tests/test_scheduler_calendar.py tests/test_scheduler_jobs.py tests/test_scheduler_lock.py tests/test_scheduler_storage.py tests/test_scheduler_health.py tests/test_production_runner.py tests/test_production_scheduler_regression.py -q
```

Current Phase 16 suites:

- `tests/test_scheduler_calendar.py`
- `tests/test_scheduler_jobs.py`
- `tests/test_scheduler_lock.py`
- `tests/test_scheduler_storage.py`
- `tests/test_scheduler_health.py`
- `tests/test_production_runner.py`
- `tests/test_production_scheduler_regression.py`

These tests cover:

- APScheduler configuration boundary and NYSE/ET DST-aware market eligibility.
- Weekend, holiday, early-close, and stale catch-up skips.
- Dependency-aware job graph behavior.
- Durable lease lock overlap prevention.
- Append-only scheduler ledger and stable idempotency keys.
- Heartbeat freshness evaluation and monitor-only failure status.
- Production runtime runner composition through existing sync, runtime,
  paper signal, order-poll, dashboard-export, and notification boundaries.

The GitHub Actions heartbeat workflow is monitor-only. It must never run scans,
signals, QuantConnect commands, or order code.

Phase 16 does not close the Phase 15 `/live/orders/read` authority gate.
Authoritative external order/fill/rejection verification still requires a
valid US market-hours or next-open observation window.

## Phase 16.1 Production Integration Tests

Phase 16.1 tests are deterministic and offline unless explicitly labeled as
operator-run external go-live checks. Run:

```powershell
python -m pytest tests/test_shared_state.py tests/test_dashboard_runtime_source.py tests/test_dashboard_app_rendering.py tests/test_dashboard_render_config.py tests/test_production_runner.py tests/test_phase16_1_golive_scripts.py -q
```

Current Phase 16.1 suites:

- `tests/test_shared_state.py`
- `tests/test_dashboard_runtime_source.py`
- `tests/test_dashboard_app_rendering.py`
- `tests/test_dashboard_render_config.py`
- `tests/test_production_runner.py`
- `tests/test_phase16_1_golive_scripts.py`

These tests cover:

- Render Key Value / Valkey shared state contracts.
- Shared dashboard export mirror and activity records.
- Deployment-wide scheduler lease locking through shared state.
- Dashboard `shared_state` production source and degraded states.
- Controlled Streamlit auto-refresh.
- Render Blueprint Key Value wiring and `REDIS_URL` injection.
- Go-live verification scripts that report missing external evidence as
  blocked/not-run instead of passed.

Operator-run external Phase 16.1 checks require Render and Telegram environment
variables outside the repository:

```powershell
python scripts\verify_render_golive.py --require-dashboard-url --require-shared-state
$env:MARKETPILOT_RUNTIME_TELEGRAM_SMOKE_ENABLED="1"
python scripts\telegram_runtime_smoke.py
```

Phase 16.1 is not complete until deployed Render web/worker evidence,
password-protected dashboard access, shared production data, Telegram runtime
delivery, and local-computer independence are externally verified and recorded.
