# Phase 15 Context: Paper Trading & Order Flow

## Phase

- Phase: 15 - Paper Trading & Order Flow
- Goal: Pipeline signals are delivered to a running QC paper algorithm and fill results are tracked with full audit traceability.
- Depends on: Phase 14 data sync/dashboard integration.
- Requirements: PTD-01, PTD-02, PTD-03, PTD-04, PTD-05, FT-01, FT-02, FT-03, FT-04, SAFE-05.
- Granularity: Fine.

## Decisions

- D-01: Phase 15 is simulated Paper Trading only. No real-money path, real brokerage credential path, leverage, margin, short selling, options, futures, cryptocurrency, Forex, dashboard order entry, or hidden live-trading switch is allowed.
- D-02: QuantConnect remains authoritative for orders, fills, holdings, cash, portfolio equity, paper deployment state, and algorithm state. Local JSONL audit records are trace and mirror evidence only.
- D-03: Signal delivery uses the QuantConnect Commands API to a running QuantConnect paper algorithm. Local code must not submit broker orders directly, and Render/dashboard code must remain read-only.
- D-04: SAFE-05 stale signal enforcement happens twice: before Commands API delivery and inside the LEAN `on_command` receiver. Every stale skip must be auditable and must not create a LEAN order.
- D-05: Duplicate deployment and signal attempts are rejected by deterministic idempotency keys before the request leaves the local process. LEAN also rejects duplicate signal commands before placing an order.
- D-06: Commands carry a MarketPilot signal payload, not a generic external order command. LEAN translates accepted signal payloads into paper orders inside `on_command`, with a compact order tag carrying `signal_id` and `idempotency_key`.
- D-07: Fill and rejection tracking polls the official QuantConnect live orders endpoint and treats that response as authoritative. Do not infer fills from local lifecycle state, and do not claim real external execution unless it actually ran.
- D-08: Credentials and secrets must not appear in code, docs, tests, fixtures, audit records, logs, summaries, or chat. User-managed QuantConnect credentials stay outside the repository and outside chat.
- D-09: Phase 14 sync and reconciliation are required pre-submission inputs. A stale sync record, missing sync record, API error sync, or reconciliation mismatch blocks new signal delivery while preserving exit/recovery obligations.
- D-10: Automated tests must be deterministic and offline, using mocks and fixtures. They must not require QuantConnect, Telegram, Render, broker credentials, internet, or market access.
- D-11: Existing untracked local artifacts are out of scope for planning and execution: `.planning/research/.cache/`, `data/`, and `lean.json` must not be modified by Phase 15 planning.
- D-12: No new external packages are required for Phase 15; use existing `requests`, `tenacity`, stdlib dataclasses/datetime/path/json, and pytest fixtures.

## Deferred Ideas

- Multi-algorithm management is out of scope for Phase 15.
- WebSocket streaming is out of scope for Phase 15.
- Automatic state correction is out of scope for Phase 15.
- Any real-money migration, broker adapter, or dashboard mutation control is forbidden, not deferred.

## The Agent's Discretion

- Use deterministic JSONL-backed ledgers for idempotency and audit mirrors, matching existing `marketpilot.audit_journal` and `marketpilot.sync` patterns.
- Keep the LEAN receiver thin. Put reusable payload normalization and validation in a pure `marketpilot` module so tests can run offline without a LEAN runtime.
- If real QuantConnect credentials are unavailable during execution, record external checks as `not_run`; do not convert offline mocks into evidence of real QC execution.

## Source Audit

| Source | ID | Feature or constraint | Plan | Status |
|--------|----|-----------------------|------|--------|
| GOAL | phase-goal | Deliver pipeline signals to a running QC paper algorithm and track fills with audit traceability | 15-01, 15-02, 15-03, 15-04, 15-05 | COVERED |
| REQ | PTD-01 | Deploy paper algorithm through QC API with hardcoded paper-only configuration | 15-01, 15-02, 15-05 | COVERED |
| REQ | PTD-02 | Deliver signals through Commands API without redeployment | 15-01, 15-02, 15-03, 15-05 | COVERED |
| REQ | PTD-03 | Stop and liquidate paper algorithm through API | 15-01, 15-05 | COVERED |
| REQ | PTD-04 | Reject duplicate deploy requests through idempotency keys | 15-02, 15-05 | COVERED |
| REQ | PTD-05 | LEAN receives signal commands and translates them to paper orders | 15-03, 15-05 | COVERED |
| REQ | FT-01 | Poll `/live/orders/read` and map fills to local signal IDs | 15-01, 15-04, 15-05 | COVERED |
| REQ | FT-02 | Append fill events to local audit JSONL while QC remains authoritative | 15-04, 15-05 | COVERED |
| REQ | FT-03 | Track partial fills and order rejections with reasons | 15-04, 15-05 | COVERED |
| REQ | FT-04 | Make signal-to-order-to-fill chain traceable in audit log | 15-04, 15-05 | COVERED |
| REQ | SAFE-05 | Skip stale signals outside valid execution window | 15-02, 15-03, 15-05 | COVERED |
| RESEARCH | api-wrappers | Add `/live/commands/create`, correct `/live/orders/read`, preserve paper-gated stop/liquidate | 15-01 | COVERED |
| RESEARCH | deployment-ledger | Local idempotent deployment ledger keyed by paper-only deployment inputs | 15-02 | COVERED |
| RESEARCH | signal-payload | Custom MarketPilot signal payload with correlation, signal, idempotency, and expiry fields | 15-02, 15-03 | COVERED |
| RESEARCH | lean-receiver | Add `on_command` and `on_order_event`; keep LEAN adapter thin and paper-only | 15-03 | COVERED |
| RESEARCH | order-tags | Tag LEAN orders with signal and idempotency evidence | 15-02, 15-03, 15-04 | COVERED |
| RESEARCH | fill-parser | Fixture-first parser for live order payloads, partial fills, and rejections | 15-04 | COVERED |
| RESEARCH | manual-qc-check | Credentialed QC verification is a human-managed checkpoint and must be marked `not_run` unless run | 15-05 | COVERED |
| CONTEXT | D-01 | Simulated Paper Trading only | 15-01, 15-02, 15-03, 15-04, 15-05 | COVERED |
| CONTEXT | D-02 | QuantConnect authority, local audit mirror only | 15-02, 15-04, 15-05 | COVERED |
| CONTEXT | D-03 | Commands API delivery, no dashboard order entry | 15-01, 15-02, 15-05 | COVERED |
| CONTEXT | D-04 | Stale guards before delivery and in LEAN | 15-02, 15-03, 15-05 | COVERED |
| CONTEXT | D-05 | Duplicate deploy/signal idempotency | 15-02, 15-03, 15-05 | COVERED |
| CONTEXT | D-06 | Custom signal payload and tagged LEAN orders | 15-02, 15-03, 15-04 | COVERED |
| CONTEXT | D-07 | QC live orders are authoritative; no fake execution claims | 15-04, 15-05 | COVERED |
| CONTEXT | D-08 | No credentials or secrets | 15-01, 15-02, 15-03, 15-04, 15-05 | COVERED |
| CONTEXT | D-09 | Phase 14 sync/reconciliation gate before submission | 15-02, 15-05 | COVERED |
| CONTEXT | D-10 | Offline deterministic tests | 15-01, 15-02, 15-03, 15-04, 15-05 | COVERED |
| CONTEXT | D-11 | Do not touch unrelated untracked artifacts | 15-05 | COVERED |
| CONTEXT | D-12 | No new external packages | 15-01, 15-02, 15-03, 15-04, 15-05 | COVERED |

## External Setup

- QuantConnect account, organization access, Paper Trading live node, project id, compile id, node id, version id, deployment id, and API credentials are user-managed.
- Store QuantConnect credentials only in approved local environment variables or secret stores; never in repository files or chat.
- Phase 15 automation must remain useful without credentials by using offline mocks and explicit `not_run` external evidence.
