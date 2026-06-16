---
phase: 15-paper-trading-order-flow
plan: 02
subsystem: paper-order-flow
tags: [quantconnect, commands-api, paper-trading, idempotency, sync-gate, pytest]

requires:
  - phase: 15-paper-trading-order-flow
    provides: "Plan 15-01 QCApiClient wrappers for live-paper deployment and command delivery"
  - phase: 14-data-sync-dashboard-integration
    provides: "Phase 14 sync JSONL records and read_last_sync_record freshness input"
provides:
  - "Frozen MarketPilot signal command models with deterministic deployment idempotency keys and compact order tags"
  - "Local paper deployment orchestration that rejects duplicate deployment keys before QuantConnect API calls"
  - "Signal command submission gate with exact latest-sync freshness, reconciliation, stale-signal, and duplicate-signal checks"
  - "Append-only audit records for skipped, blocked, duplicate, delivered, and failed signal command attempts"
affects: [phase-15-plan-03-lean-command-receiver, phase-15-plan-04-fill-tracking, phase-16-scheduler]

tech-stack:
  added: []
  patterns: [pure-command-models, explicit-jsonl-ledgers, latest-sync-fail-closed-gate, command-delivery-not-fill-success]

key-files:
  created:
    - marketpilot/paper_command_models.py
    - marketpilot/paper_order_flow.py
    - tests/test_paper_order_flow.py
    - .planning/phases/15-paper-trading-order-flow/15-02-SUMMARY.md
  modified: []

key-decisions:
  - "Signal command payloads carry MarketPilot trace fields and explicitly mark command delivery as not order execution."
  - "Deployment and signal idempotency ledgers require caller-supplied paths; the module does not write repo data/ unless a caller explicitly supplies that location."
  - "The pre-submit sync gate trusts only the latest Phase 14 JSONL record after UTC source_timestamp, max-age, success status, and reconciliation_clean checks pass."

patterns-established:
  - "Local order-flow modules receive a QCApiClient instance and never construct QuantConnect URLs or import requests."
  - "Rejected stale, duplicate, missing-sync, stale-sync, api-error-sync, and reconciliation-mismatch signals append audit records before returning."
  - "Accepted signal command results report command_delivered separately from order_executed, which remains false until authoritative QC order polling."

requirements-completed: [PTD-01, PTD-02, PTD-04, SAFE-05]

duration: 14min
completed: 2026-06-16T11:38:26Z
---

# Phase 15 Plan 02: Signal Command Gate Summary

**Local paper deployment and signal-command gates with deterministic idempotency, exact Phase 14 sync freshness checks, and audit-only command delivery evidence**

## Performance

- **Duration:** 14 min
- **Started:** 2026-06-16T11:24:34Z
- **Completed:** 2026-06-16T11:38:26Z
- **Tasks:** 2
- **Files modified:** 4
- **Local Python:** 3.10.10

## Accomplishments

- Added pure command dataclasses and helpers for deterministic paper deployment idempotency keys, MarketPilot signal command payloads, UTC freshness decisions, and compact order tags.
- Added local `deploy_paper_algorithm()` orchestration that rejects duplicate deployment keys before `QCApiClient.create_live_algorithm()`.
- Added `submit_signal_command()` with exact latest-record Phase 14 sync gate, stale-signal skip, duplicate-signal rejection, command delivery via `QCApiClient.create_live_command()`, and append-only audit records.
- Added 20 deterministic offline tests covering RED/GREEN TDD gates, duplicate deployment, accepted command delivery, latest sync record behavior, missing/stale/error/mismatch sync blocking, stale signals, and duplicate signals.

## Task Commits

1. **Task 1 RED: Define command model tests** - `6ff5ccf` (test)
2. **Task 1 GREEN: Implement command models** - `f5d4217` (feat)
3. **Task 2 RED: Define paper order flow tests** - `173d9a3` (test)
4. **Task 2 GREEN: Implement paper order flow gates** - `57f65b1` (feat)

## Files Created/Modified

- `marketpilot/paper_command_models.py` - Frozen dataclasses and pure helpers for deployment idempotency, signal command payloads, freshness policy, and order tag round-tripping.
- `marketpilot/paper_order_flow.py` - Local paper deployment and signal submission orchestration with explicit JSONL ledgers, Phase 14 sync gate, stale/duplicate skips, audit records, and QCApiClient-only command delivery.
- `tests/test_paper_order_flow.py` - Offline tests for command models, idempotency, sync gate blocking, stale skips, duplicate skips, and accepted command delivery.
- `.planning/phases/15-paper-trading-order-flow/15-02-SUMMARY.md` - Execution summary and verification evidence for this plan.

## Verification

- `pytest tests/test_paper_order_flow.py -q` - passed, 20 tests.
- `rg "quantconnect\\.com/api|requests\\." marketpilot/paper_order_flow.py` - passed; no direct network calls found.
- RED gate for Task 1 failed as expected before implementation with missing `marketpilot.paper_command_models`.
- RED gate for Task 2 failed as expected before implementation with missing `marketpilot.paper_order_flow`.

## Decisions Made

- Command payloads remain project-specific `marketpilot_signal` messages; local code does not submit external broker orders.
- Command API success is recorded only as `command_delivered`; `order_executed`, `order_filled`, and local authority remain false until later authoritative QC order polling.
- Sync freshness uses the latest JSONL record only, requires timezone-aware UTC `source_timestamp`, blocks age greater than 600 seconds, requires `sync_status == "success"`, and requires `reconciliation_clean is True`.
- Idempotency state is local JSONL mirror evidence only and is never portfolio/order authority.

## Deviations from Plan

None - plan executed as written.

## Issues Encountered

- The first RED test patch was accidentally applied from the shell session directory instead of the target repository. It was removed immediately and re-added to the intended repository path before verification or commit.
- `gsd-tools` state/roadmap update helpers partially misformatted existing metadata during close-out (`state.advance-plan` could not parse the current state, and the roadmap progress row lost its original table columns). The affected metadata was corrected to reflect 15-02 completion and 15-03 readiness.
- Existing unrelated untracked local artifacts remained untouched: `.planning/research/.cache/`, `data/`, and `lean.json`.

## Known Stubs

None. Stub-pattern scan hits in the modified files are typed optional fields, status strings, test fixture helpers, or parser/default control flow; they do not represent UI/data placeholders or unfinished behavior.

## Threat Flags

None beyond the plan's declared trust boundaries. This plan intentionally adds local JSONL ledgers and a QCApiClient command boundary, with mitigations for duplicate replay, stale signals, stale/untrusted sync records, and command-delivery-vs-fill semantics.

## Auth Gates

None. All verification was deterministic and offline; no QuantConnect credentials were used or requested.

## Residual Risks

- Real QuantConnect paper deployment and command delivery were not exercised; this plan verified the local gate with offline mocks only.
- `submit_signal_command()` can report command delivery failure from the mocked/API return value, but authoritative order/fill/rejection state remains deferred to Plan 15-04 via `/live/orders/read`.
- Local tests ran under Python 3.10.10 while project metadata requires Python >=3.11 for strict/release validation.

## User Setup Required

None for this plan. Future credentialed smoke checks still require user-managed QuantConnect credentials and a paper live node outside chat.

## Next Phase Readiness

Plan 15-03 can consume `MarketPilotSignalCommand` payloads and `build_order_tag()` in the LEAN `on_command` receiver, adding the second stale/duplicate safety gate inside the running paper algorithm.

## Self-Check: PASSED

- Found created/modified files: `marketpilot/paper_command_models.py`, `marketpilot/paper_order_flow.py`, `tests/test_paper_order_flow.py`, `.planning/phases/15-paper-trading-order-flow/15-02-SUMMARY.md`.
- Found task commits: `6ff5ccf`, `f5d4217`, `173d9a3`, `57f65b1`.
- Verified no tracked files were deleted by the 15-02 task commits.

---
*Phase: 15-paper-trading-order-flow*
*Completed: 2026-06-16*
