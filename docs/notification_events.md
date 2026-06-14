# Notification Events

Phase 6 notification events are typed, transport-neutral domain events. They
are not Telegram strings and do not send network requests.

Supported event types:

Phase 8 Telegram alert families:

- `buy_candidate`
- `watch`
- `paper_buy`
- `paper_sell`
- `submitted_order`
- `partial_fill`
- `full_fill`
- `stop`
- `target`
- `partial_close`
- `full_close`
- `rejected_order`
- `canceled_order`
- `regime_change`
- `system`
- `error`
- `start_restart`
- `daily_summary`

Phase 6 compatibility event types:

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

Required Telegram alert payloads may include symbol, setup, classification,
score, Paper mode, activation state, order/fill state, stop/target context,
regime state, system health, and reason fields. They must not include secrets,
credentials, copied token or chat target values, fake performance, or
profitability guarantees. The domain event layer stores sanitized payloads and
the Telegram adapter formats concise plain text from those fields.

Regime transition alerts are generated only when the previous and current
regime states differ. Unchanged repeated states produce no new
`regime_change` event. Transition payloads include previous state, current
state, timestamp, correlation ID, and reason labels so deduplication can still
use `event_type|correlation_id`.

Daily summaries are end-of-day notification artifacts, not portfolio authority.
They include the active Paper mode, new signal count, entry count, exit count,
open position count, rejected action count, and system warnings. They explicitly
label QuantConnect as the authoritative portfolio source and do not invent
portfolio values.

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
