# Phase 15 Plan Quality Validation

**Phase:** 15 - Paper Trading & Order Flow  
**Goal:** Pipeline signals are delivered to a running QC paper algorithm and fill results are tracked with full audit traceability.  
**Plans checked:** 15-01-PLAN.md through 15-05-PLAN.md  
**Verdict:** PASS after revision
**Validated at:** 2026-06-16

## Executive Verdict

The five plans are structurally well-formed and mostly cover the intended local implementation path: QuantConnect API wrappers, command payload construction, pre-submit safety gates, LEAN `on_command` order placement, live-order polling, audit records, and offline E2E tests.

Initial validation found two blockers and one warning. The plan set was revised
before execution:

1. `15-RESEARCH.md` now resolves the open questions as mandatory execution
   gates and external verification requirements.
2. Plan 15-05 no longer allows `not_run` to satisfy running-QuantConnect
   delivery; missing credentialed smoke evidence must be recorded as
   `blocked_external_not_verified` and must not mark Phase 15 complete.
3. Plan 15-02 now defines the Phase 14 sync freshness gate exactly: latest sync
   JSONL record, UTC `source_timestamp`, max age 600 seconds, `sync_status ==
   "success"`, and `reconciliation_clean is True`.

## Coverage Summary

| Requirement | Plans | Verdict | Evidence |
|---|---:|---|---|
| PTD-01 | 15-01, 15-02, 15-05 | PASS | Deployment wrapper and deploy idempotency are planned; account-specific `/live/create` behavior is a required external smoke gate before phase completion. |
| PTD-02 | 15-01, 15-02, 15-03, 15-05 | PASS | Commands API wrapper, local command sender, LEAN receiver, and mandatory external smoke evidence gate are planned. |
| PTD-03 | 15-01, 15-05 | PASS | Stop/liquidate wrappers remain paper-gated and covered by tests/docs. |
| PTD-04 | 15-02, 15-05 | PASS | Duplicate deploy keys are rejected before API calls; offline E2E covers duplicate path. |
| PTD-05 | 15-03, 15-05 | PASS | LEAN `on_command` validates MarketPilot payloads and places tagged `market_order` only on accepted commands. |
| FT-01 | 15-01, 15-04, 15-05 | PASS | `/live/orders/read` wrapper and polling are planned; exact real response shape must be captured in sanitized smoke evidence before external verification. |
| FT-02 | 15-04, 15-05 | PASS | Audit append of QC-derived order/fill evidence is planned with `source_authority=quantconnect` and `local_authority=false`. |
| FT-03 | 15-04, 15-05 | PASS | Partial fill/rejection handling is planned with offline fixtures and required external evidence capture for real field locations. |
| FT-04 | 15-04, 15-05 | PASS | Signal/order/fill trace query is planned through idempotency key, signal id, QC order id, tag, and audit records. |
| SAFE-05 | 15-02, 15-03, 15-05 | PASS | Stale-window checks are planned before Commands API delivery and again inside LEAN. |

## Plan Structure

| Plan | Wave | Depends On | Tasks | Structure | Scope |
|---|---:|---|---:|---|---|
| 15-01 | 1 | none | 2 | PASS | PASS |
| 15-02 | 2 | 15-01 | 2 | PASS | PASS |
| 15-03 | 3 | 15-02 | 2 | PASS | PASS |
| 15-04 | 3 | 15-02 | 2 | PASS | PASS |
| 15-05 | 4 | 15-03, 15-04 | 3 | PASS | PASS |

`gsd-tools query verify.plan-structure` returned `valid: true` for all five plans. The dependency graph is acyclic and wave assignments are coherent: API boundary first, local sender second, LEAN receiver and fill polling in parallel after sender contracts, final E2E/docs/UAT last.

## Key Links

| Link | Verdict | Evidence |
|---|---|---|
| `paper_order_flow.py` -> `QCApiClient.create_live_command` | PASS | Plan 15-02 explicitly calls `QCApiClient.create_live_command()` after sync, stale, and duplicate gates. |
| `lean/main.py` -> `lean_command_receiver.py` | PASS | Plan 15-03 wires `on_command` through pure normalization/validation helpers. |
| LEAN accepted command -> tagged paper order | PASS | Plan 15-03 requires exactly one `self.market_order(symbol, quantity, tag=tag)` for accepted commands. |
| QC live orders -> audit JSONL | PASS | Plan 15-04 requires `poll_quantconnect_order_updates()` to call the QC live-orders wrapper and append authoritative audit records. |
| Audit JSONL -> trace query | PASS | Plan 15-04 requires `read_signal_order_fill_trace()` to reconstruct chain without becoming authoritative state. |
| External running QC paper algorithm -> phase verification | PASS | Plan 15-05 requires credentialed smoke evidence before phase completion; missing evidence is `blocked_external_not_verified`, not pass. |

## Verification Commands

The planned automated commands are mostly sufficient for deterministic offline behavior:

- `pytest tests/test_qc_api.py -q`
- `pytest tests/test_paper_order_flow.py -q`
- `pytest tests/test_lean_command_flow.py tests/test_lean_static_safety.py tests/test_lean_runtime_bridge_static.py -q`
- `pytest tests/test_paper_order_flow_e2e.py tests/test_paper_order_flow.py tests/test_lean_command_flow.py tests/test_qc_api.py tests/test_sync.py -q`
- `pytest -q` if the local Python version satisfies project requirements

These commands do not and should not require QuantConnect credentials. The gap is not offline testing; the gap is that final phase verification can still pass with no credentialed running-paper check.

## Dimension Results

| Dimension | Verdict | Notes |
|---|---|---|
| Requirement Coverage | PASS | All required IDs appear in plan frontmatter, and external payload/setup uncertainty is handled as an execution gate. |
| Task Completeness | PASS | All tasks have files, action, verify, and done fields. |
| Dependency Correctness | PASS | No missing references or cycles found. |
| Key Links Planned | PASS | Internal wiring is planned, and external running-algorithm verification is mandatory before phase completion. |
| Scope Sanity | PASS | Plans have 2, 2, 2, 2, and 3 tasks respectively. |
| Verification Derivation | PASS | User-observable phase goal includes running QC delivery, and final plan blocks completion without real credentialed smoke evidence. |
| Context Compliance | PASS | Plans honor D-01 through D-12 and do not implement deferred ideas. |
| Scope Reduction Detection | PASS | No plan reduces a locked decision to static/stub/future work. |
| Architectural Tier Compliance | PASS | REST calls stay in `QCApiClient`; local sender gates; order placement stays in LEAN. |
| Nyquist Compliance | PASS | Each implementation task has an automated pytest command; no watch-mode or full E2E-only sampling issue found. |
| Cross-Plan Data Contracts | PASS | Command payload, tag, idempotency key, and audit fields are carried through the planned pipeline. |
| AGENTS.md Compliance | PASS | Plans preserve paper-only, no secrets, offline tests, no new packages, and QuantConnect authority. |
| Research Resolution | PASS | `15-RESEARCH.md` now has `## Open Questions (RESOLVED AS EXECUTION GATES)` and converts external unknowns into blocking evidence requirements. |
| Pattern Compliance | PASS | Plans follow `15-PATTERNS.md` boundary rules; no analog file-classification table is present to enforce per-file analog references. |

## Blockers

None after revision.

## Warnings

None after revision.

## Required Changes Before Execution

Completed in planning revision.

## Recommendation

Proceed to execution. The local/offline architecture is sound, and the external QuantConnect smoke evidence is now a blocking completion gate rather than an optional `not_run` note.
