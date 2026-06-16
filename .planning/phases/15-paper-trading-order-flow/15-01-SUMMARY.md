---
phase: 15-paper-trading-order-flow
plan: 01
subsystem: api
tags: [quantconnect, paper-trading, commands-api, live-orders, pytest]

requires:
  - phase: 13-qc-api-client-and-safety-foundation
    provides: "Authenticated safety-gated QCApiClient, credential redaction, retry handling, and initial typed wrappers"
  - phase: 14-data-sync-dashboard-integration
    provides: "QuantConnect remains authoritative for synced paper state and dashboard display mirrors"
provides:
  - "Paper-gated QuantConnect live deploy, command delivery, stop, liquidate, and official live orders polling wrappers"
  - "Hardcoded QuantConnectBrokerage live-paper deployment payload with explicit id-only QuantConnect dataProviders"
  - "Typed QuantConnectPaperOrder fields for signal ids, idempotency keys, raw status, fill quantities, average fill price, tags, rejection reasons, and raw payloads"
  - "Offline fake fixtures and tests proving command delivery is not order/fill success"
affects: [phase-15-paper-trading-order-flow, phase-15-plan-02, phase-15-plan-04, quantconnect-api-boundary]

tech-stack:
  added: []
  patterns: [paper-gated-qc-api-boundary, official-live-orders-polling, command-delivery-not-order-success]

key-files:
  created:
    - tests/fixtures/qc_api/live_command_success.json
    - tests/fixtures/qc_api/live_orders_read_success.json
    - .planning/phases/15-paper-trading-order-flow/15-01-SUMMARY.md
  modified:
    - marketpilot/qc_api.py
    - marketpilot/quantconnect_paper.py
    - tests/test_qc_api.py

key-decisions:
  - "QCApiClient.create_live_algorithm hardcodes QuantConnectBrokerage with environment live-paper and rejects account/data-provider credential payloads."
  - "QCApiClient.create_live_command returns command-delivery success only; authoritative order/fill/rejection state must come from /live/orders/read."
  - "QCApiClient.read_live_orders now uses the official /live/orders/read endpoint instead of live/read portfolio sync output."

patterns-established:
  - "Only marketpilot/qc_api.py constructs QuantConnect API URLs."
  - "Live order tags use the compact mp:<signal_id>:<idempotency_key> format for downstream traceability."
  - "Live orders preserve raw QuantConnect status and raw payload alongside normalized typed fields."

requirements-completed: [PTD-01, PTD-02, PTD-03, FT-01]

duration: 56min
completed: 2026-06-16T07:15:39Z
---

# Phase 15 Plan 01: QC API Paper Boundary Summary

**QuantConnect paper-only live deployment, command delivery, stop/liquidate controls, and authoritative live-orders polling wrappers**

## Performance

- **Duration:** 56 min
- **Started:** 2026-06-16T06:20:00Z
- **Completed:** 2026-06-16T07:15:39Z
- **Tasks:** 2
- **Files modified:** 5
- **Local Python:** 3.10.10

## Accomplishments

- Added TDD coverage and fake fixtures for paper-gated `/live/commands/create`, `/live/orders/read`, hardcoded live-paper deployment payloads, and typed live-order parsing.
- Updated `QCApiClient` so `create_live_algorithm()` builds only a QuantConnect paper brokerage payload with `environment="live-paper"` and explicit id-only `QuantConnectBrokerage` data provider configuration.
- Added `create_live_command()` for command delivery and `read_live_orders_page()`/`read_live_orders()` for official `/live/orders/read` polling, preserving signal/order/fill trace fields without treating command success as order success.

## Official API Verification

- QuantConnect Create Live Algorithm docs verify required `versionId`, `projectId`, `compileId`, `nodeId`, `brokerage`, and `dataProviders` fields: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/create-live-algorithm
- QuantConnect Create Live Command docs verify `/live/commands/create` accepts `projectId` plus nested `command` and returns a base success response: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/live-commands/create-live-command
- QuantConnect Live Orders docs verify `/live/orders/read` accepts `algorithmId`, `start`, `end`, and `projectId`: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/read-live-algorithm/orders
- QuantConnect Paper Trading docs verify paper trading uses fictional capital and avoids real-money execution: https://www.quantconnect.com/docs/v2/cloud-platform/live-trading/brokerages/quantconnect-paper-trading

## Task Commits

1. **Task 1: Add API wrapper tests and fixtures** - `a6d374f` (test)
2. **Task 2: Implement paper command and live orders wrappers** - `ac005a0` (feat)

## Files Created/Modified

- `marketpilot/qc_api.py` - Added paper-gated command/live-orders endpoints, live-paper deployment payload construction, command delivery wrapper, official live-orders page wrapper, and live-order parser helpers.
- `marketpilot/quantconnect_paper.py` - Extended `QuantConnectPaperOrder` with signal/idempotency, raw status, fill quantities, average fill price, tag, rejection reason, and raw payload fields.
- `tests/test_qc_api.py` - Added offline tests for paper-gated endpoints, deploy payload shape, command payload nesting, and official live orders parsing.
- `tests/fixtures/qc_api/live_command_success.json` - Fake command delivery success response with no secrets.
- `tests/fixtures/qc_api/live_orders_read_success.json` - Fake partial-fill and rejected-order response with no secrets.

## Verification

- `pytest tests/test_qc_api.py -q` - passed, 23 tests.
- RED gate before implementation - failed as expected with missing endpoint allowlist entries, missing `version_id` deploy signature, missing `create_live_command()`, missing `read_live_orders_page()`, and missing live-order parser fields.
- `rg "quantconnect\\.com/api" marketpilot -g "*.py"` - passed; only `marketpilot/qc_api.py` contains the API base URL.

## Decisions Made

- Kept `/live/commands/create` success semantics as delivery-only evidence. It does not imply a LEAN order was placed or filled.
- Treated `/live/orders/read` as the authoritative order polling API. `live/read` remains portfolio/snapshot sync context only.
- Restricted live deployment payloads to QuantConnect paper brokerage and id-only QuantConnect data provider settings to avoid real brokerage credential paths.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- None. Existing unrelated untracked local artifacts remained untouched: `.planning/research/.cache/`, `data/`, and `lean.json`.

## Known Stubs

None. The empty list/dict matches found in modified source are parser accumulators or existing defaults, not UI/data stubs that block the plan goal.

## Threat Flags

None beyond the plan's declared trust boundaries. This plan intentionally adds paper-gated QuantConnect command and live-order API wrappers and mitigates the new mutation surface with `PAPER_TRADING_ONLY`, hardcoded `live-paper`, and data-provider credential rejection.

## Auth Gates

None. All verification was deterministic and offline; no QuantConnect credentials were used or requested.

## Residual Risks

- Real QuantConnect account behavior was not exercised because this plan intentionally used offline mocks and fake fixtures.
- Public docs do not expose every possible live-order response field shape; Plan 15-04/15-05 should capture credentialed paper fixtures before claiming external fill-tracking verification.
- Local tests ran under Python 3.10.10; strict/release verification should use the project-supported Python version.

## User Setup Required

None for this plan. Future credentialed smoke checks still require user-managed QuantConnect credentials and paper live node setup outside chat.

## Next Phase Readiness

Plan 15-02 can build the signal command sender and deployment idempotency layer on top of `create_live_algorithm()` and `create_live_command()`. Plan 15-04 can consume the typed `QuantConnectPaperOrder` fields from `/live/orders/read` for audit traceability.

## Self-Check: PASSED

- Found created/modified files: `marketpilot/qc_api.py`, `marketpilot/quantconnect_paper.py`, `tests/test_qc_api.py`, `tests/fixtures/qc_api/live_command_success.json`, `tests/fixtures/qc_api/live_orders_read_success.json`, `.planning/phases/15-paper-trading-order-flow/15-01-SUMMARY.md`.
- Found task commits: `a6d374f`, `ac005a0`.
- Verified no tracked files were deleted by the 15-01 task commits.

---
*Phase: 15-paper-trading-order-flow*
*Completed: 2026-06-16*
