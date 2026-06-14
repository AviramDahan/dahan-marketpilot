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
