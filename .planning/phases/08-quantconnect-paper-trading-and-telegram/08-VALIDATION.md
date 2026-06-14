---
phase: 08-quantconnect-paper-trading-and-telegram
validated: 2026-06-14
status: planned
nyquist_validation: true
human_verification_required: false
---

# Phase 08 Validation Plan

This validation contract maps Phase 8 requirements and context decisions to
planned deterministic checks. It is a planning artifact for Nyquist coverage;
execution will create the concrete tests and `08-VERIFICATION.md`.

## Validation Strategy

Phase 8 must prove that Paper Trading activation, QuantConnect reconciliation,
protective recovery, and Telegram delivery are safe without requiring real
QuantConnect credentials, a live node, Telegram credentials, internet access,
or real market data in automated tests.

External QuantConnect and Telegram availability is represented as
`not_configured`, `not_run`, `missing_token`, or `missing_chat_id` unless the
operator configures secrets outside repository files.

## Requirement Coverage

| Requirement | Planned Evidence | Plans |
|-------------|------------------|-------|
| REG-04 | Regime transition alert tests emit only when previous and current regime states differ; repeated unchanged states emit no alert. | 08-04 |
| TEL-01 | Paper mode gating tests cover Shadow, Limited Paper, Full Approved Paper, `validation_passed` not Paper eligible, stale/unavailable validation fail-closed, and Limited Paper caps. | 08-01 |
| TEL-02 | QuantConnect prerequisite/status, snapshot, reconciliation, restart recovery, and protective recovery tests prove QuantConnect source-of-truth behavior and local audit-mirror boundaries. | 08-01, 08-02 |
| TEL-03 | Alert taxonomy and formatting tests cover BUY candidate, WATCH, Paper BUY/SELL, order/fill/exit/regime/system/error/start/restart/daily summary event families. | 08-03, 08-04 |
| TEL-04 | Delivery result tests cover disabled, missing token, missing chat ID, rate limited, rejected, failed, delivered, duplicate suppression, and local rate limiting. | 08-03, 08-04 |
| TEL-05 | Static and unit tests reject committed Telegram/QuantConnect secret values, redact secret-like fields, and document external secret-store setup only. | 08-01, 08-03 |
| TEL-06 | Failure-isolation tests prove Telegram delivery success/failure never controls Paper gates, order lifecycle, reconciliation, protective exits, or recovery decisions. | 08-02, 08-03, 08-04 |

## Decision Coverage

| Decision Range | Planned Evidence | Plans |
|----------------|------------------|-------|
| D-01..D-05 | Paper mode gating, transition audit records, Limited Paper caps, and fail-closed validation evidence tests. | 08-01 |
| D-06..D-10 | QuantConnect Paper deployment prerequisite contracts, operator-run command rendering, not-configured/not-run states, and real brokerage rejection tests. | 08-01 |
| D-11..D-15 | QuantConnect-authoritative snapshot, mismatch, restart recovery, local audit mirror, and protective recovery tests. | 08-02 |
| D-16..D-20 | Telegram config, external secret lookup, delivery result mapping, dedup/rate limiting, plain-text sanitized formatter, and failure isolation tests. | 08-03 |
| D-21..D-24 | Full alert taxonomy, regime transition suppression, daily summary events, and historical backtest real-Telegram-disabled tests. | 08-04 |

## Test Matrix

| Test File | Primary Coverage | External Access |
|-----------|------------------|-----------------|
| `tests/test_paper_modes.py` | TEL-01, D-01..D-05 | None |
| `tests/test_quantconnect_paper_contract.py` | TEL-02, D-06..D-10 | None |
| `tests/test_paper_trading_safety.py` | TEL-02, TEL-05, no fake deployment/state | None |
| `tests/test_reconciliation.py` | TEL-02, D-11..D-13 | None |
| `tests/test_quantconnect_restart_recovery.py` | TEL-02, D-14 | None |
| `tests/test_protective_recovery.py` | TEL-02, TEL-06, D-15 | None |
| `tests/test_telegram_secret_handling.py` | TEL-05, D-16..D-17 | None |
| `tests/test_telegram_transport.py` | TEL-04, TEL-06, D-18..D-20 | None |
| `tests/test_telegram_safety.py` | TEL-06, delivery non-authority | None |
| `tests/test_telegram_alert_coverage.py` | TEL-03, D-21 | None |
| `tests/test_regime_telegram_alerts.py` | REG-04, D-22 | None |
| `tests/test_daily_summary_notifications.py` | TEL-03, D-23 | None |
| `tests/test_telegram_failure_isolation.py` | TEL-04, TEL-06, D-18..D-19 | None |

## Nyquist Sampling

- Every requirement mapped to Phase 8 has at least one planned automated test
  file and one plan owner.
- Safety-critical invariants are sampled from multiple angles:
  activation gating, configuration safety, static secret scans, runtime delivery
  results, reconciliation mismatch handling, and failure isolation.
- External systems are modeled through typed contracts and fake/injected
  clients; no deterministic automated test requires real QuantConnect,
  Telegram, Render, broker credentials, internet, or market data.

## Release Gate

Before Phase 8 can be marked complete, execution verification must show:

- `python -m pytest -q` passed.
- GSD verification status is `passed`.
- External QuantConnect and Telegram checks are either actually executed and
  documented, or explicitly recorded as `not_configured`/`not_run`.
- No repository file contains real QuantConnect credentials, Telegram token,
  Telegram chat ID, real-money broker configuration, fake Paper portfolio
  authority, or fake deployment results.
