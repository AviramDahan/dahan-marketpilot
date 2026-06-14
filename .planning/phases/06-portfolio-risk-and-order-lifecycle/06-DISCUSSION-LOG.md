# Phase 6: Portfolio Risk and Order Lifecycle - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md - this log preserves the alternatives considered.

**Date:** 2026-06-14
**Phase:** 6-portfolio-risk-and-order-lifecycle
**Areas discussed:** Risk budget and portfolio limits, Position sizing and cash handling, Order lifecycle states, Stops and exits, Persistence and restart recovery, Notification-domain events

---

## Risk Budget And Portfolio Limits

| Option | Description | Selected |
|--------|-------------|----------|
| A | 1% per-trade risk, 10 max positions, 30% sector exposure, 3 new entries/day. | yes |
| B | More conservative limits. | |
| C | More aggressive limits. | |
| D | You choose. | |

**User's choice:** A A A A
**Notes:** Recommended balanced defaults selected.

---

## Position Sizing And Cash Handling

| Option | Description | Selected |
|--------|-------------|----------|
| A | Risk amount divided by stop distance; invalid stop rejects; 15% max allocation; reduce quantity only if still valid. | yes |
| B | Simpler fixed-allocation or reject-only choices. | |
| C | Score-scaled or negative-cash choices. | |
| D | You choose. | |

**User's choice:** A A A A
**Notes:** Risk-based sizing selected.

---

## Order Lifecycle States

| Option | Description | Selected |
|--------|-------------|----------|
| A | Rich audit lifecycle, QuantConnect source of truth, idempotency key, no Phase 6 order submission. | yes |
| B | Simpler lifecycle/local-source alternatives. | |
| C | More aggressive broker/Paper behavior. | |
| D | You choose. | |

**User's choice:** A A A A
**Notes:** Phase 6 remains intent/events only.

---

## Stops And Exits

| Option | Description | Selected |
|--------|-------------|----------|
| A | Setup structural stop with ATR sanity cap, 2R target, modeled partial exits, trailing disabled by default. | yes |
| B | Simpler or omitted exit behavior. | |
| C | More aggressive defaults. | |
| D | You choose. | |

**User's choice:** A A A A
**Notes:** Exit behavior is modeled/configurable; execution is deferred.

---

## Persistence And Restart Recovery

| Option | Description | Selected |
|--------|-------------|----------|
| A | JSONL append-only audit journal, QuantConnect wins on mismatch, safe split/delisting placeholders. | yes |
| B | Minimal current-position persistence. | |
| C | Local portfolio source of truth or full execution behavior. | |
| D | You choose. | |

**User's choice:** A A A A
**Notes:** Local state is recovery/audit context only.

---

## Notification-Domain Events

| Option | Description | Selected |
|--------|-------------|----------|
| A | Typed domain events, sanitized payloads, delivery failure cannot block safety, fake transport for tests. | yes |
| B | Smaller event set or no fake transport. | |
| C | Telegram-specific payloads now. | |
| D | You choose. | |

**User's choice:** A A A A
**Notes:** Notification-domain events are transport-independent.

---

## The Agent's Discretion

The user did not choose "You choose" in this phase. The agent retains discretion
over names and file layout while preserving the selected A decisions.

## Deferred Ideas

- Real QuantConnect Paper order submission - Phase 8.
- Real Telegram delivery - Phase 8.
- Real Backtest execution and activation gates - Phase 7.
