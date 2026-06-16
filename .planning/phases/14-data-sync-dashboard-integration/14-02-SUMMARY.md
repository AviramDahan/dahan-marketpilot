---
phase: 14-data-sync-dashboard-integration
plan: 02
subsystem: dashboard-data
tags: [dashboard, jsonl, freshness, quantconnect, streamlit]

requires:
  - phase: 14-data-sync-dashboard-integration
    provides: "Plan 14-01 writes append-only data/portfolio_sync.jsonl records"
provides:
  - "DashboardFreshnessStatus.ERROR for >30 minute stale/error sync data"
  - "sync_jsonl dashboard source loader that reads the latest JSONL record"
  - "UTC-aware three-state freshness evaluation using 600s and 1800s thresholds"
  - "Degraded dashboard snapshots for missing, empty, corrupt, or incomplete sync data"
affects: [phase-14-dashboard-display, dashboard-data-layer, sync-jsonl-boundary]

tech-stack:
  added: []
  patterns:
    - "Read-only JSONL file boundary between sync producer and dashboard consumer"
    - "Dashboard data freshness maps FRESH/STALE/ERROR to portfolio section status"

key-files:
  created: []
  modified:
    - dashboard/models.py
    - dashboard/data.py
    - dashboard/config.py
    - tests/test_dashboard_runtime_source.py

key-decisions:
  - "Dashboard sync_jsonl reads only the latest non-empty JSONL line and never imports marketpilot.sync or marketpilot.qc_api."
  - "Missing or corrupt sync data returns an honest degraded DashboardSnapshot instead of fabricated portfolio values."
  - "Unparseable source_timestamp produces UNKNOWN freshness with no fabricated timestamp; corrupt record structure produces ERROR degraded state."

patterns-established:
  - "sync_jsonl source metadata uses source=quantconnect_sync_jsonl and authority=authoritative."
  - "Freshness thresholds are config-driven: fresh <= stale_warning_seconds, stale <= stale_error_seconds, error beyond that."

requirements-completed: [DASH-01, DASH-02, DASH-03, DASH-04, SAFE-04]

duration: 10min
completed: 2026-06-15
---

# Phase 14 Plan 02: Dashboard Data Layer Summary

**sync_jsonl dashboard loading with UTC freshness thresholds and honest degraded portfolio state**

## Performance

- **Duration:** 10 min
- **Started:** 2026-06-15T23:49:00Z
- **Completed:** 2026-06-15T23:59:09Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Added `DashboardFreshnessStatus.ERROR` so dashboard freshness can distinguish fresh, stale, error, and unknown states.
- Added `sync_jsonl` dispatch and loader in `dashboard/data.py` that reads the latest JSONL line, validates the record, maps portfolio holdings, and labels QuantConnect as authoritative.
- Implemented UTC-aware freshness evaluation from `source_timestamp` against `DashboardConfig.stale_warning_seconds` and `DashboardConfig.stale_error_seconds`.
- Added focused tests for config acceptance, missing/empty data, corrupt JSONL, unparseable timestamps, latest-line loading, and freshness boundaries.

## Task Commits

1. **Task 1: Add ERROR freshness state to DashboardFreshnessStatus enum** - `325b534` (feat)
2. **Task 2: Implement sync_jsonl loader with 3-state freshness evaluation** - `d52556c` (feat)

## Files Created/Modified

- `dashboard/models.py` - Added `DashboardFreshnessStatus.ERROR`.
- `dashboard/data.py` - Added read-only `sync_jsonl` loader, latest-line reader, UTC freshness evaluation, sync record parsing, and degraded snapshots.
- `dashboard/config.py` - Added `sync_jsonl` to accepted dashboard data source kinds.
- `tests/test_dashboard_runtime_source.py` - Added focused coverage for the new source kind and freshness thresholds.

## Decisions Made

- Kept `dashboard/data.py` decoupled from `marketpilot.sync` and `marketpilot.qc_api`; the JSONL file is the only boundary.
- Treated missing, empty, and corrupt JSONL data as degraded snapshots rather than exceptions or synthetic portfolio values.
- Treated invalid `source_timestamp` as `UNKNOWN` freshness without inventing a timestamp, while malformed record structure remains an error.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Accepted sync_jsonl in DashboardConfig**
- **Found during:** Task 2 (sync_jsonl loader implementation)
- **Issue:** The plan's expected verification constructs `DashboardConfig(data_source_kind="sync_jsonl", ...)`, but `dashboard/config.py` still rejected that source kind.
- **Fix:** Added `sync_jsonl` to `_validate_data_source()` while preserving existing local path, secret-like path, URL, and parent traversal rejection.
- **Files modified:** `dashboard/config.py`
- **Verification:** `pytest --tb=short -q tests/test_dashboard_runtime_source.py tests/test_dashboard_data_contracts.py tests/test_dashboard_object_store_source.py`; `pytest --tb=short -q`; expected manual command returned `status=unknown` for missing local sync data.
- **Committed in:** `d52556c`

---

**Total deviations:** 1 auto-fixed (Rule 2 missing critical functionality)
**Impact on plan:** Required for the planned public configuration path and verification command. No new external dependency or dashboard write capability was added.

## Issues Encountered

- A separate Phase 14 Plan 01 commit (`16d0e29`) appeared in the repository history during this run. It was preserved and not included in this plan's task commits.
- Unrelated untracked local artifacts remained untouched: `.planning/research/.cache/`, `data/`, and `lean.json`.

## Verification

- `python -c "from dashboard.models import DashboardFreshnessStatus; assert DashboardFreshnessStatus.ERROR.value == 'error'; print('ERROR state added')"` -> passed.
- `python -c "from dashboard.data import load_dashboard_snapshot; from dashboard.config import DashboardConfig; from datetime import datetime, timezone; cfg = DashboardConfig(data_source_kind='sync_jsonl', data_source_path='data/portfolio_sync.jsonl'); snap = load_dashboard_snapshot(cfg, now=datetime.now(timezone.utc)); print(f'status={snap.source_metadata.freshness_status.value}')"` -> passed, printed `status=unknown` for missing local sync data.
- `rg "marketpilot\.(sync|qc_api)" dashboard/data.py` -> no forbidden imports found.
- `pytest --tb=short -q tests/test_dashboard_runtime_source.py tests/test_dashboard_data_contracts.py tests/test_dashboard_object_store_source.py` -> passed.
- `pytest --tb=short -q` -> passed.

## Known Stubs

- `dashboard/data.py:518` - Existing Object Store runtime loader stub remains from prior dashboard work. It is unrelated to `sync_jsonl` and does not block this plan because `sync_jsonl` has a concrete loader.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: file_input | `dashboard/data.py` | New read-only JSONL file input is parsed as untrusted data; malformed/missing data returns degraded snapshots and the loader reads only the latest 4096-byte tail chunk. |

## Residual Risks

- If a valid JSONL record line exceeds the 4096-byte tail chunk, the dashboard will return a degraded parse error rather than reading the full file. This preserves the denial-of-service mitigation from the plan.
- The dashboard does not maintain expected generation state yet, so generation is informational and logged/reasoned when missing or zero.

## User Setup Required

None - no external service configuration required for this plan.

## Next Phase Readiness

Plan 14-03 can consume `DashboardFreshnessStatus.ERROR`, `source_metadata.freshness_status`, `source_metadata.source_timestamp`, and portfolio section status to render the freshness banner and sync status display.

## Self-Check: PASSED

- Verified created/modified files exist: `dashboard/models.py`, `dashboard/data.py`, `dashboard/config.py`, `tests/test_dashboard_runtime_source.py`, and this summary.
- Verified task commits exist: `325b534` and `d52556c`.
- Verified no tracked files were deleted by the 14-02 task commits.

---
*Phase: 14-data-sync-dashboard-integration*
*Completed: 2026-06-15*
