# Paper Trading Order Flow

SIMULATED PAPER TRADING ONLY - NOT FINANCIAL ADVICE.

This document describes the Phase 15 order-flow boundary for Dahan MarketPilot.
The implementation delivers validated MarketPilot signal commands to a running
QuantConnect paper algorithm and mirrors authoritative QuantConnect order/fill
evidence into local audit JSONL records. The local repository never becomes the
source of truth for active paper portfolio state.

## Authority Model

QuantConnect is authoritative for simulated paper deployment state, algorithm
state, orders, fills, holdings, cash, portfolio equity, and paper performance.
Local JSONL records are audit and display mirrors only. A local command-delivery
success means only that the command request was accepted by the local
`QCApiClient.create_live_command()` boundary. It is not an executed order, fill,
portfolio change, or profit/loss result.

Order and fill evidence is accepted only from QuantConnect live-order polling
through `poll_quantconnect_order_updates()`, which calls the `QCApiClient`
`/live/orders/read` wrapper and records `source_authority="quantconnect"` with
`local_authority=false`.

## Flow

1. The runtime pipeline produces an `OrderIntent` after strategy, scoring, risk,
   reconciliation, and paper eligibility gates have already passed.
2. `submit_signal_command()` builds a `marketpilot_signal` payload with
   `correlation_id`, `signal_id`, `idempotency_key`, `symbol`, `quantity`,
   `signal_time_utc`, `expires_at_utc`, `strategy_mode`, `primary_setup`,
   `paper_trading_only=true`, and
   `command_delivery_is_order_execution=false`.
3. The local sender checks the latest Phase 14 sync JSONL record. Missing,
   stale, failed, malformed, future-dated, or reconciliation-mismatch records
   block command delivery.
4. The local sender checks signal freshness. Expired or stale signals are
   skipped before any QuantConnect API call and are recorded as audit evidence.
5. The local sender checks the signal idempotency ledger. Duplicate
   idempotency keys are rejected before any QuantConnect API call.
6. The command is delivered through `QCApiClient.create_live_command()` to a
   user-managed running QuantConnect paper deployment.
7. `lean/main.py` receives the command in `DahanMarketPilotRuntime.on_command()`.
   It first records sanitized receipt evidence, then validates command type,
   paper-only flags, schema, supported symbol shape, integer positive quantity,
   expiry, and duplicate idempotency before placing exactly one tagged LEAN
   paper `market_order()`.
8. LEAN order tags use `mp:<signal_id>:<idempotency_key>` so later
   `/live/orders/read` evidence can be mapped back to the signal.
9. `poll_quantconnect_order_updates()` mirrors QuantConnect order observations
   into append-only audit records.
10. `read_signal_order_fill_trace()` reconstructs the local evidence chain by
    `signal_id` or `idempotency_key` without mutating state.

Phase 15-08 also implements a guarded Object Store signal-inbox fallback for
diagnosis. When explicitly configured with a MarketPilot Object Store key, the
LEAN adapter polls that key, clears the Object Store cache before read attempts,
parses the JSON payload, and routes it into the same validation path as
`on_command()`. Object Store delivery remains only a delivery mechanism; it is
not order, fill, or portfolio authority.

## Stale And Duplicate Gates

SAFE-05 is enforced twice:

- Before `create_live_command()` in local Python.
- Inside `DahanMarketPilotRuntime.on_command()` before any LEAN order call.

Duplicate prevention is also enforced twice:

- Before command delivery through the local signal idempotency ledger.
- Inside LEAN through `marketpilot_seen_command_keys`.

Stale, expired, duplicate, malformed, non-paper, unsupported-symbol, and unsafe
payloads must not create a QuantConnect API command or a LEAN paper order.

## Fill And Rejection Evidence

Partial fills and rejections are tracked from QuantConnect live-order payloads.
The parser preserves raw status, raw payload, fill quantity, remaining quantity,
average fill price, rejection reason, order tag, signal id, idempotency key, and
parse warnings.

The local parser does not infer fills. A `Filled` or `PartiallyFilled` status
without QuantConnect fill quantity evidence is mirrored as order observation
evidence with warnings, not as a fill.

## Operator Environment Names

Credentialed paper smoke verification requires user-managed QuantConnect setup
outside the repository and outside chat. The implementation and documentation
may name required environment variables, but must never store or print values:

- `QUANTCONNECT_USER_ID`
- `QUANTCONNECT_API_TOKEN`
- `QC_PROJECT_ID`
- `QC_DEPLOY_ID`
- `QC_COMPILE_ID`
- `QC_NODE_ID`
- `QC_VERSION_ID`
- `QC_ORGANIZATION_ID` (optional; the smoke can attempt `/account/read`)

These values must point only to a simulated QuantConnect Paper Trading
deployment. They must not identify a real-money brokerage account or any live
brokerage credential path.

## Prohibited Paths

The order flow must never add or document:

- Real-money trading.
- Real brokerage credentials or adapters.
- Leverage, margin, short selling, options, futures, cryptocurrency, Forex, or
  unsupported asset classes.
- Dashboard order-entry or order-mutation controls.
- Local portfolio authority in JSON, CSV, SQLite, Excel, Render storage, GitHub,
  or audit files.
- Profitability, guaranteed return, or fake execution claims.

## Verification Classes

Offline automated tests prove local behavior only. They use fake clients, fake
sync JSONL records, fake LEAN objects, and temporary audit files.

Real QuantConnect paper execution can be claimed only after a credentialed
paper-only smoke run records sanitized evidence from a user-managed running
paper deployment. Without that run, PTD-01/PTD-02 external delivery evidence and
the running-QuantConnect phase goal remain `blocked_external_not_verified`.

As of Phase 15-06, QuantConnect cloud file sync, compile, Paper deployment
creation, read-only polling, and `/live/commands/create` acceptance are verified.
Callback-to-order evidence remains blocked: both plain and typed MarketPilot
command probes returned command API success, but `/live/logs/read` and
`/live/orders/read` showed no `on_command` debug log and no live order during
the smoke windows. API acceptance must still not be treated as callback
execution, order submission, fill evidence, or portfolio change.

As of Phase 15-07, the next diagnostic route is explicit:

- `scripts/qc_command_dispatch_probe.py` tests a no-order Python echo algorithm
  with a generic no-`$type` command payload, matching QuantConnect's documented
  `on_command` dispatch semantics.
- `scripts/qc_command_smoke.py` keeps `marketpilot_signal` as the default
  generic payload and keeps typed payloads clearly labeled as diagnostics.
- If the no-order echo probe does not log receipt after API acceptance, the
  blocker is QuantConnect command dispatch or account/project behavior, not
  MarketPilot order logic.
- If the echo probe logs receipt, the next safe external proof is the
  MarketPilot generic command smoke, with callback-to-order or
  callback-to-rejection evidence recorded separately from API acceptance.

The Phase 15-07 credentialed echo probe compiled and deployed successfully, and
the Commands API accepted both immediate and delayed generic echo commands.
However, `/live/logs/read` returned 0 logs and no echo marker. Phase 15 remains
externally blocked until QuantConnect command dispatch or a supported fallback
delivery path is proven.

As of Phase 15-08, the Object Store fallback path is locally implemented and
tested:

- `QCApiClient` includes narrow Object Store wrappers for account read, object
  set/get/list/properties/delete.
- Object Store writes/deletes are limited to
  `{project_id}/marketpilot/signals/*.json`.
- `scripts/qc_object_store_signal_smoke.py` refuses to run unless
  `MARKETPILOT_QC_OBJECT_STORE_SMOKE_ENABLED=1`.
- `lean/main.py` polls Object Store only when an explicit signal key is
  configured and reuses the same MarketPilot validation gates as commands.
- The initial credentialed Paper compile/deploy succeeded, but `/object/set`
  returned `Organization not found` because multipart uploads inherited a JSON
  `Content-Type`.

As of Phase 15-09, the Object Store smoke performs a fail-fast write preflight
and Object Store writes are externally verified:

- `--diagnose-only` tests `/object/set`, `/object/properties`, and cleanup
  without compile, deploy, command dispatch, logs polling, or orders polling.
- A failed Object Store write skips Paper deployment entirely.
- `QCApiClient` sets JSON `Content-Type` only on JSON requests and lets
  `requests` construct multipart `Content-Type` for `/object/set`.
- Credentialed diagnose-only returned `object_store_write_available`.
- A full fallback smoke wrote the object, compiled, deployed, restored the
  project file, cleaned up the object, and stopped the Paper deployment.
- Phase 15-10 fixed live-log pagination by using QuantConnect's official
  `startLine`/`endLine` fields with `deploymentLogs=true`.
- The corrected full fallback smoke observed `MarketPilot Object Store signal
  received.`, `MarketPilot object_store accepted: SPY 1`, and a QuantConnect
  Paper `Submitted` order event in live logs.
- The remaining external gap is post-receipt order authority: `/live/orders/read`
  returned 0 orders during the smoke window, and no fill/rejection evidence is
  claimed yet.
- As of Phase 15-11, Object Store fallback smokes stop temporary Paper
  deployments by default after polling. Use `--keep-running` only for an
  explicit operator-approved next-open or market-hours observation window.
- As of Phase 15-12, the Object Store smoke filters `/live/orders/read` by the
  exact expected order tag for the current signal so stale MarketPilot orders
  from older deployments cannot create false-positive authority. `lean/main.py`
  also defers an accepted Object Store signal when the target symbol has no
  tradeable price yet, keeping the signal unprocessed so the next scheduled poll
  can retry after market data arrives.
- A credentialed market-hours smoke on 2026-06-17 compiled and deployed
  successfully, observed Object Store receipt and acceptance, and QuantConnect
  live logs showed both `Submitted` and `Filled` order events for SPY quantity
  1 at fill price `$751.31`. However, `/live/orders/read` for the current
  deployment did not return an order with the exact current tag; it returned
  only an older tagged order from deployment `L-103091222fcd6eee4aae06e1de635e38`.
  Therefore live-log fill evidence is stronger than before, but the
  `/live/orders/read` authority gate remains open.
- As of Phase 15-13, the `/live/orders/read` authority gate is closed for
  simulated Paper Trading. The smoke polls `start=0,end=1000`, records
  top-level `qc_order_evidence_*` fields, and waits long enough for
  QuantConnect's delayed live-order snapshot. The credentialed run for
  deployment `L-d62998269941f7f00ba48804a092c2b7` returned the exact current
  tag `mp:qc-object-store-sig-20260617143733:qc-object-store-order-20260617143733`
  with Submitted and Filled events, fill quantity `1`, fill price `$750.08`,
  object cleanup success, and deployment stop success.
