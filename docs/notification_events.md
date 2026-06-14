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
- `system`
- `protective_recovery`

Payloads are sanitized before they are stored in events. The fake collector is
for deterministic tests only. Deduplication and rate limiting affect
notification emission only; they never control risk, order, or exit safety
logic.

Telegram delivery is a Phase 8 transport adapter over these domain events. It
uses the same stable delivery key as local deduplication:

```text
event_type|correlation_id
```

Duplicate suppression and local rate limiting can suppress or delay outbound
Telegram delivery, but they cannot approve Paper modes, create orders, change
order lifecycle states, clear reconciliation mismatches, unblock new entries,
or change protective recovery decisions.

Backtest preview events are historical previews for deterministic inspection.
They are emitted through the fake collector only, are sanitized like all other
notification-domain events, and cannot control risk, activation gates, order
lifecycle, or exit safety.

Protective recovery events are high-severity domain alerts for missing
stop/target protection on filled QuantConnect Paper positions. They may be
collected by fake transports or later delivered by Telegram, but delivery
success or failure never controls protective recovery, exit obligations, or
new-entry blocking.
