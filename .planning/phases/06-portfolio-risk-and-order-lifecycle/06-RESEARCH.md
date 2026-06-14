# Phase 6 Research: Portfolio Risk and Order Lifecycle

**Date:** 2026-06-14
**Status:** Planning research complete

## Research Summary

Phase 6 should remain deterministic, offline-testable, and paper-only. The
implementation should create domain models, validation rules, audit records, and
events that later QuantConnect Paper Trading code can consume, without creating
real order submission or fake portfolio authority now.

## Key Findings

- Risk sizing should use explicit stop distance and fail closed when stop data
  is missing, zero, negative, non-finite, or incompatible with the candidate.
- Candidate classifications from Phase 5 are audit labels. Phase 6 may consume
  ranked candidates, but it must require explicit risk, stop, target, cash,
  allocation, count, sector, and idempotency validation before producing an
  order intent.
- Local order lifecycle state should be an audit mirror and intent model. It is
  useful for tests and recovery context, but QuantConnect remains authoritative
  for actual Paper orders, fills, holdings, cash, and positions.
- Exits should be modeled separately from market-regime entry gates. A later
  `RISK_OFF` regime can block new long entries, but it must not remove existing
  stop, target, partial-close, full-close, or recovery obligations.
- Persistence should be append-only JSONL. The journal should record decisions,
  lifecycle events, config/version hashes, and recovery mismatches without
  becoming an authoritative portfolio database.
- Notification-domain events should be typed and transport-neutral. Telegram
  strings, tokens, chat IDs, network calls, and delivery semantics remain
  deferred to Phase 8.

## Recommended Modules

- `marketpilot/risk.py` for portfolio constraints and position sizing.
- `marketpilot/order_lifecycle.py` for order intents, lifecycle states,
  transitions, and idempotency keys.
- `marketpilot/exits.py` for stops, targets, partial exits, trailing exit
  configuration, maximum holding period, and regime-independent exit
  obligations.
- `marketpilot/audit_journal.py` for append-only JSONL audit records.
- `marketpilot/recovery.py` for local-vs-QuantConnect restart reconciliation
  contracts and safe split/delisting placeholders.
- `marketpilot/notification_events.py` for typed domain events, sanitization,
  fake collector, deduplication, and rate limiting.

## Verification Strategy

Use deterministic unit tests only:

- No QuantConnect credentials, Cloud calls, Paper Trading deployment, Telegram,
  Render, broker credentials, internet, or real market access.
- Use frozen dataclasses/enums and simple fixture objects.
- Add static safety tests that scan Phase 6 production files for forbidden live,
  broker, credential, Telegram-delivery, fake-performance, and order-submission
  behavior.
- Run targeted tests per plan, then full `python -m pytest -q`.

## Deferrals

- Actual QuantConnect Paper order submission and real order reconciliation:
  Phase 8.
- Real Telegram delivery and formatting for human messages: Phase 8.
- Full QuantConnect-verified split/delisting behavior: later verification, with
  safe placeholders in Phase 6.
- Backtest activation, performance reports, and strategy approval gates:
  Phase 7.

