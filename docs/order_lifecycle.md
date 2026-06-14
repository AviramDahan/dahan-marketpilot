# Order Lifecycle

Phase 6 order lifecycle models are local audit mirrors and intent records only.
QuantConnect remains the source of truth for actual Paper order state, fills,
cash, holdings, and positions.

Lifecycle states:

- `planned`
- `submitted`
- `partially_filled`
- `filled`
- `rejected`
- `canceled`
- `protective_orders_pending`
- `open`
- `partially_closed`
- `closed`

Duplicate prevention uses a stable idempotency key derived from symbol,
strategy mode, primary setup, signal time, and portfolio epoch.

Phase 6 does not submit, cancel, replace, or modify Paper orders. Actual
QuantConnect Paper submission remains deferred to Phase 8.
