# Notification Events

Phase 6 notification events are typed, transport-neutral domain events. They
are not Telegram strings and do not send network requests.

Supported event types:

- `risk_rejection`
- `sizing_decision`
- `order_intent`
- `lifecycle_transition`
- `stop_target_update`
- `partial_close`
- `full_close`
- `recovery_mismatch`
- `backtest_preview`

Payloads are sanitized before they are stored in events. The fake collector is
for deterministic tests only. Deduplication and rate limiting affect
notification emission only; they never control risk, order, or exit safety
logic.

Real Telegram delivery remains deferred to Phase 8.

Backtest preview events are historical previews for deterministic inspection.
They are emitted through the fake collector only, are sanitized like all other
notification-domain events, and cannot control risk, activation gates, order
lifecycle, or exit safety.
