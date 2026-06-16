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
   It validates command type, paper-only flags, schema, supported symbol shape,
   integer positive quantity, expiry, and duplicate idempotency before placing
   exactly one tagged LEAN paper `market_order()`.
8. LEAN order tags use `mp:<signal_id>:<idempotency_key>` so later
   `/live/orders/read` evidence can be mapped back to the signal.
9. `poll_quantconnect_order_updates()` mirrors QuantConnect order observations
   into append-only audit records.
10. `read_signal_order_fill_trace()` reconstructs the local evidence chain by
    `signal_id` or `idempotency_key` without mutating state.

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
