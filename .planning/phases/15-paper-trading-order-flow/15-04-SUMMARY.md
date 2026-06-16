---
phase: 15-paper-trading-order-flow
plan: 04
subsystem: paper-order-flow
tags: [quantconnect, live-orders, fills, audit-jsonl, traceability, pytest]

requires:
  - phase: 15-paper-trading-order-flow
    provides: "Plan 15-01 QCApiClient live-orders wrappers and typed QuantConnectPaperOrder fields"
  - phase: 15-paper-trading-order-flow
    provides: "Plan 15-02 MarketPilot signal command tags, signal ids, idempotency keys, and append-only audit journal usage"
provides:
  - "QuantConnect live order parser that maps raw statuses to local lifecycle states while preserving raw status and raw payload evidence"
  - "Authoritative order/fill/rejection polling mirror that appends source_authority=quantconnect and local_authority=false JSONL audit records"
  - "Signal-to-order-to-fill trace query helper that reads existing audit records without changing state"
affects: [phase-15-plan-05, phase-16-scheduler, fill-tracking, paper-audit-trace]

tech-stack:
  added: []
  patterns: [quantconnect-authoritative-order-mirror, append-only-audit-trace, fixture-first-live-order-parser]

key-files:
  created:
    - .planning/phases/15-paper-trading-order-flow/15-04-SUMMARY.md
  modified:
    - marketpilot/paper_order_flow.py
    - tests/test_paper_order_flow.py

key-decisions:
  - "QuantConnect live orders are parsed into local lifecycle evidence, but raw status and raw payload remain preserved for unknown response shapes."
  - "Filled and partially filled audit records are emitted only when QuantConnect provides fill quantity evidence; local code does not infer fills from status alone."
  - "Trace queries read append-only audit records by signal_id or idempotency_key and never become portfolio or order authority."

patterns-established:
  - "Use source_authority=\"quantconnect\", local_authority=false, and paper_trading_only=true on every QC-derived order/fill audit record."
  - "Unknown QC statuses produce visible parse_warnings while preserving raw_payload for fixture refinement."
  - "The fill trace helper sorts matching audit records by UTC timestamp and performs no writes."

requirements-completed: [FT-01, FT-02, FT-03, FT-04]

duration: 10min
completed: 2026-06-16T11:54:00Z
---

# Phase 15 Plan 04: Authoritative Order/Fill Audit Summary

**QuantConnect live-order status, partial-fill, fill, rejection, and unknown-shape evidence mirrored into append-only audit records with signal trace queries**

## Performance

- **Duration:** 10 min
- **Started:** 2026-06-16T11:48:53Z
- **Completed:** 2026-06-16T11:54:00Z
- **Tasks:** 2
- **Files modified:** 3
- **Local Python:** 3.10.10

## Accomplishments

- Added parser coverage for submitted, partially filled, filled, rejected, canceled, unknown, and missing-fill QuantConnect live order payloads.
- Implemented `parse_quantconnect_live_order()` and `parse_quantconnect_live_orders()` with lifecycle mapping, MarketPilot tag recovery, raw status preservation, raw payload preservation, and explicit parse warnings.
- Implemented `poll_quantconnect_order_updates()` to read mocked/typed QC live orders through the client boundary and append one authority-labeled JSONL audit record per observed order update.
- Implemented `read_signal_order_fill_trace()` to reconstruct a command/order/fill or command/order/rejection chain from existing audit evidence by `signal_id` or `idempotency_key`.

## Official API Verification

- QuantConnect `/live/orders/read` docs were rechecked during execution. The official request uses `algorithmId`, `start`, `end`, and `projectId`; the docs state live order snapshots update about every 10 minutes.
- QuantConnect order event docs were rechecked during execution. Order events are the official LEAN order-state update surface, including fill-state changes.
- QuantConnect command docs were rechecked during execution. Command delivery remains distinct from order/fill execution.

## Task Commits

1. **Task 1 RED: Add live order parsing and lifecycle mapping tests** - `49677b2` (test)
2. **Task 1 GREEN: Parse QuantConnect live order states** - `f6bef66` (feat)
3. **Task 2 RED: Add order audit trace tests** - `9d13ec4` (test)
4. **Task 2 GREEN: Mirror QuantConnect order updates to audit** - `d55c134` (feat)

## Files Created/Modified

- `marketpilot/paper_order_flow.py` - Added `QuantConnectOrderObservation`, `QuantConnectOrderPollResult`, live-order parsing helpers, status-to-lifecycle mapping, audit mirroring, and trace query helpers.
- `tests/test_paper_order_flow.py` - Added deterministic offline tests for parser cases, fill/rejection audit records, no-fill-inference behavior, unknown-status preservation, and trace queries.
- `.planning/phases/15-paper-trading-order-flow/15-04-SUMMARY.md` - Execution summary and verification record.

## Verification

- `pytest tests/test_paper_order_flow.py -q` - passed, 32 tests.
- `rg 'source_authority.*quantconnect|local_authority' marketpilot/paper_order_flow.py tests/test_paper_order_flow.py` - passed; authority labels are present in implementation and tests.
- RED gate for Task 1 failed as expected before implementation with missing `parse_quantconnect_live_order()`.
- RED gate for Task 2 failed as expected before implementation with missing `poll_quantconnect_order_updates()`.

## Decisions Made

- Unknown QuantConnect order statuses map to `status="unknown"` in audit payloads and include `parse_warnings=["unknown_order_status"]`, while retaining the raw status and raw payload.
- A `Filled` or `PartiallyFilled` raw status without QuantConnect fill quantity evidence is mirrored as `paper_order_observed`, not `paper_fill_observed`, with explicit missing-fill warnings.
- `read_signal_order_fill_trace()` filters by audit payload identity fields and sorts by record timestamp; it does not mutate JSONL or derive authority.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- A parallel 15-03 executor committed and continued modifying LEAN command receiver files during this plan. Those files were not staged or modified by Plan 15-04.
- Existing unrelated untracked local artifacts remained untouched: `.planning/research/.cache/`, `data/`, and `lean.json`.

## Known Stubs

None. Stub-pattern scan over `marketpilot/paper_order_flow.py` and `tests/test_paper_order_flow.py` found no TODO/FIXME/placeholder/coming-soon markers. Optional `None` values in parser outputs are intentional evidence for missing QuantConnect fields, not unfinished stubs.

## Threat Flags

None beyond the plan's declared trust boundaries. This plan intentionally mirrors the QuantConnect live-orders response into local JSONL and mitigates the trust boundary with raw evidence preservation, explicit parse warnings, `source_authority="quantconnect"`, `local_authority=false`, and no fill inference without QC fill data.

## Auth Gates

None. All verification used deterministic offline fixtures and mocked clients; no QuantConnect credentials, Telegram credentials, Render credentials, internet, or market access were used.

## Residual Risks

- Real QuantConnect paper live-order payloads were not captured because no credentialed smoke run was performed in this plan.
- Public docs do not expose every possible order payload field shape; unknown shapes are preserved for manual fixture refinement in Plan 15-05.
- Local tests ran under Python 3.10.10 while project metadata requires Python >=3.11 for strict/release validation.

## User Setup Required

None for this plan. Later credentialed smoke checks still require user-managed QuantConnect credentials and a paper live node outside chat.

## Next Phase Readiness

Plan 15-05 can use `submit_signal_command()` plus `poll_quantconnect_order_updates()` in offline E2E tests, then add documentation and credentialed paper-smoke verification gates without treating local JSONL as authority.

## Self-Check: PASSED

- Found created/modified files: `marketpilot/paper_order_flow.py`, `tests/test_paper_order_flow.py`, `.planning/phases/15-paper-trading-order-flow/15-04-SUMMARY.md`.
- Found task commits: `49677b2`, `f6bef66`, `9d13ec4`, `d55c134`.
- Verified no tracked files were deleted by the 15-04 task commits.

---
*Phase: 15-paper-trading-order-flow*
*Completed: 2026-06-16*
