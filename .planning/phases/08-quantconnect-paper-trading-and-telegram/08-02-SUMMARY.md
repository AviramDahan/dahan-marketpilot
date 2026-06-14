---
phase: 08-quantconnect-paper-trading-and-telegram
plan: "02"
subsystem: paper-trading-recovery
tags: [quantconnect, paper-trading, reconciliation, restart-recovery, protective-recovery, notifications, tdd]
requires:
  - phase: 08-quantconnect-paper-trading-and-telegram/08-01
    provides: "Paper mode gates and QuantConnect Paper deployment prerequisite contracts"
  - phase: 06-portfolio-risk-and-order-lifecycle
    provides: "Order lifecycle, idempotency, exit obligations, audit mirror, and notification-domain events"
provides:
  - "QuantConnect-authoritative Paper snapshot, order, fill, holding, performance, deployment, and algorithm status contracts"
  - "Pure reconciliation decisions that block new entries on local mirror mismatch while preserving exits"
  - "QuantConnect-first restart recovery with local audit attached as context only"
  - "Protective recovery for filled Paper positions missing stop/target protection, independent from notification delivery"
affects: [phase-08, phase-09-dashboard, phase-10-cicd-security]
tech-stack:
  added: []
  patterns:
    - "QuantConnect snapshots are immutable authoritative inputs; local state is mirror context only"
    - "Recovery and protective decisions are pure domain decisions with optional non-authoritative notification events"
key-files:
  created:
    - marketpilot/reconciliation.py
    - tests/test_reconciliation.py
    - tests/test_quantconnect_restart_recovery.py
    - tests/test_protective_recovery.py
  modified:
    - marketpilot/quantconnect_paper.py
    - marketpilot/recovery.py
    - marketpilot/exits.py
    - marketpilot/notification_events.py
    - docs/recovery.md
    - docs/paper_trading.md
    - docs/notification_events.md
    - docs/safety.md
key-decisions:
  - "QuantConnect Paper snapshots remain authoritative for cash, equity, holdings, orders, fills, deployment status, algorithm status, and performance."
  - "Reconciliation mismatches block new entries, preserve exit obligations, emit high-severity system-domain events, and require explicit recovery."
  - "Restart recovery never promotes local audit history to authority when QuantConnect is unavailable."
  - "Protective recovery may emit notification-domain events, but delivery success or failure cannot alter recovery decisions."
patterns-established:
  - "Authoritative QuantConnect order IDs and fills override local mirror values after submission."
  - "Local idempotency keys remain pre-submission duplicate-intent protection."
  - "New system/protective event families use string domain event types to preserve existing Phase 6 NotificationEventType factory coverage."
requirements-completed: [TEL-02, TEL-06]
test-results:
  targeted: "python -m pytest tests/test_reconciliation.py tests/test_quantconnect_restart_recovery.py tests/test_protective_recovery.py -q -> 9 passed"
  broad: "python -m pytest -q -> passed"
  external: "No QuantConnect, Telegram, Render, broker credentials, internet, or market access required."
metrics:
  duration: "12 min"
  completed: 2026-06-14
---

# Phase 08 Plan 02: Order Reconciliation and Recovery Summary

**QuantConnect-authoritative reconciliation, restart rebuilds, and protective recovery that blocks unsafe Paper entries without depending on Telegram delivery.**

## Performance

- **Duration:** 12 min
- **Started:** 2026-06-14T11:40:57Z
- **Completed:** 2026-06-14T11:51:43Z
- **Tasks:** 3
- **Files modified:** 12

## Accomplishments

- Added immutable QuantConnect Paper snapshot contracts for cash, equity, holdings, orders, fills, deployment status, algorithm status, and performance.
- Added `reconcile_quantconnect_state()` to compare QuantConnect snapshots against local order lifecycle and audit mirrors without overwriting authoritative state.
- Added QuantConnect-first restart recovery that reconstructs active positions/orders/fills from QuantConnect first and blocks new entries when QuantConnect is unavailable.
- Added protective recovery for filled Paper positions missing stop/target protection, with high-severity notification-domain events that never control safety decisions.

## Task Commits

1. **Task 1 RED:** `4f988c4` test(08-02): add failing reconciliation contract tests
2. **Task 1 GREEN:** `9f838d0` feat(08-02): add quantconnect reconciliation contracts
3. **Task 2 RED:** `91b5106` test(08-02): add failing quantconnect restart recovery tests
4. **Task 2 GREEN:** `03d137a` feat(08-02): add quantconnect-first restart recovery
5. **Task 3 RED:** `0e8d29d` test(08-02): add failing protective recovery tests
6. **Task 3 GREEN:** `e9ec37f` feat(08-02): add protective recovery failure isolation
7. **Documentation sync:** `7e3e419` docs(08-02): document protective recovery safety

## Files Created/Modified

- `marketpilot/quantconnect_paper.py` - Added QuantConnect Paper snapshot, holding, order, fill, deployment, algorithm, and performance contracts.
- `marketpilot/reconciliation.py` - Added mismatch classifications and pure reconciliation decisions.
- `marketpilot/recovery.py` - Added QuantConnect-first restart recovery and unavailable-state fail-closed behavior.
- `marketpilot/exits.py` - Added protective recovery decisions for filled positions missing stop/target protection.
- `marketpilot/notification_events.py` - Added string-based system and protective recovery domain event helpers.
- `tests/test_reconciliation.py` - Added D-11 through D-13 reconciliation tests.
- `tests/test_quantconnect_restart_recovery.py` - Added D-14 restart recovery tests.
- `tests/test_protective_recovery.py` - Added D-15 and TEL-06 protective recovery failure-isolation tests.
- `docs/paper_trading.md` - Documented reconciliation authority and mismatch behavior.
- `docs/recovery.md` - Documented QuantConnect-first restart and protective recovery.
- `docs/notification_events.md` - Documented protective recovery notification non-authority.
- `docs/safety.md` - Documented restart and protective recovery safety rules.

## Verification

- `python -m pytest tests/test_reconciliation.py -q` -> 3 passed.
- `python -m pytest tests/test_quantconnect_restart_recovery.py -q` -> 3 passed.
- `python -m pytest tests/test_protective_recovery.py -q` -> 3 passed.
- `python -m pytest tests/test_reconciliation.py tests/test_quantconnect_restart_recovery.py tests/test_protective_recovery.py -q` -> 9 passed.
- `python -m pytest -q` -> passed.

No automated test invoked QuantConnect, Telegram, Render, broker credentials, internet, or real market access.

## Decisions Made

- QuantConnect order IDs and fill data are authoritative after submission; local mirror fields can only indicate mismatch.
- Local idempotency keys remain the pre-submission duplicate-intent protection and are reported alongside authoritative QuantConnect state.
- Restart recovery returns `not_configured`, `not_run`, or `recovery_required` style statuses when QuantConnect state is unavailable instead of treating local audit as complete authority.
- System and protective recovery event types were implemented as sanitized string domain events instead of extending the Phase 6 `NotificationEventType` enum, preserving existing factory coverage contracts.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Preserved existing notification enum factory contract**
- **Found during:** Task 3 broad verification.
- **Issue:** Adding `system` and `protective_recovery` to `NotificationEventType` broke an existing Phase 6 test that expects every enum value to have a Phase 6 factory.
- **Fix:** Kept the new event families as string domain event types created by helper functions, leaving the existing enum stable.
- **Files modified:** `marketpilot/notification_events.py`, `tests/test_reconciliation.py`, `tests/test_protective_recovery.py`
- **Verification:** `python -m pytest tests/test_protective_recovery.py tests/test_reconciliation.py tests/test_quantconnect_restart_recovery.py -q` and `python -m pytest -q` passed.
- **Committed in:** `e9ec37f`

**Total deviations:** 1 auto-fixed bug.
**Impact on plan:** The fix preserved backwards compatibility without weakening the Phase 8 event behavior.

## Issues Encountered

- `gsd-tools` was not available on `PATH`; the executor used `node C:\Users\User\.codex\gsd-core\bin\gsd-tools.cjs` for SDK queries where possible.
- An initial `apply_patch` attempt targeted the session working directory instead of the requested repository. The stray uncommitted file was deleted immediately and the patch was reapplied to the verified repository path before any commit.
- Local Python remains 3.10.10 while `pyproject.toml` requires Python >=3.11 for strict release validation. The targeted and broad suites passed in the available local environment.

## Known Stubs

None introduced by this plan. The stub scan found only pre-existing documentation text describing Phase 6 split/delisting placeholders.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: quantconnect_snapshot_reconciliation | `marketpilot/reconciliation.py` | External QuantConnect Paper snapshots drive local recovery decisions; mitigated by immutable contracts, `authoritative_source='quantconnect'`, mismatch blocking, and no mutation of QuantConnect or local state. |
| threat_flag: protective_recovery_notification | `marketpilot/exits.py` | Protective recovery may emit high-severity notification-domain events; mitigated by sanitized payloads and tests proving notification delivery failure cannot alter recovery decisions. |

## User Setup Required

None for automated tests. Real QuantConnect Paper recovery still requires user-managed QuantConnect account, Paper Live Node, project ID, API credentials in approved secret stores, and operator-run deployment outside repository files.

## Next Phase Readiness

Plan 08-03 can build Telegram delivery on top of transport-neutral events. Reconciliation and protective recovery already treat notification delivery as non-authoritative, so Telegram failures can be mapped to delivery results without changing trading safety decisions.

## Self-Check: PASSED

- Verified all created and modified files exist.
- Verified task commits exist: `4f988c4`, `9f838d0`, `91b5106`, `03d137a`, `0e8d29d`, `e9ec37f`, `7e3e419`.

---
*Phase: 08-quantconnect-paper-trading-and-telegram*
*Completed: 2026-06-14*
