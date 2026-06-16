---
phase: 15-paper-trading-order-flow
plan: "08"
subsystem: quantconnect-object-store-signal-fallback
tags: [quantconnect, object-store, paper-trading, diagnostics, gap-closure]

requires:
  - phase: 15-paper-trading-order-flow
    provides: "Phase 15-07 command API acceptance with no observable dispatch marker"
provides:
  - "Guarded Object Store API wrappers for MarketPilot signal inbox probes"
  - "Disabled-by-default Object Store paper signal smoke runner"
  - "LEAN Object Store polling hook that reuses MarketPilot command validation"
  - "Sanitized external evidence that Object Store API write is blocked for the current QC organization/account state"
affects: [phase-15-paper-trading-order-flow, quantconnect-paper-operations]

tech-stack:
  added: []
  patterns: [disabled-external-smoke-helper, object-store-namespace-safety, shared-lean-validation]

key-files:
  created:
    - scripts/qc_object_store_signal_smoke.py
    - .planning/phases/15-paper-trading-order-flow/15-08-SUMMARY.md
  modified:
    - marketpilot/qc_api.py
    - lean/main.py
    - tests/test_qc_api.py
    - tests/test_lean_command_flow.py
    - docs/paper_trading_order_flow.md
    - docs/testing.md
    - .planning/phases/15-paper-trading-order-flow/15-UAT.md
    - .planning/phases/15-paper-trading-order-flow/15-VERIFICATION.md

key-decisions:
  - "Object Store fallback writes/deletes are allowed only under `{project_id}/marketpilot/signals/*.json`."
  - "The live algorithm polls Object Store only when an explicit signal key is configured."
  - "Object Store delivery is not order/fill authority; `/live/orders/read` remains the only order authority."
  - "Phase 15 remains externally blocked because `/object/set` returned `Organization not found` before algorithm receipt could be tested."

patterns-established:
  - "Fallback delivery must route into the same MarketPilot command validation path as Commands API delivery."
  - "External smoke scripts must separate object write, algorithm receipt, order/rejection polling, cleanup, and final status."

requirements-completed: []

duration: 49min
completed: 2026-06-16T18:23:00Z
---

# Phase 15 Plan 08: Object Store Fallback Summary

**Local Object Store fallback implementation complete; external Object Store write blocked.**

## Performance

- **Tasks completed:** 3/4 locally complete.
- **Checkpoint:** `blocked_external_object_store_write_not_verified`.
- **Local Python:** 3.10.10

## Accomplishments

- Added narrow QuantConnect Object Store wrappers to `QCApiClient`:
  `/account/read`, `/object/set`, `/object/get`, `/object/list`,
  `/object/properties`, and `/object/delete`.
- Added namespace safety so Object Store writes/deletes are limited to
  `{project_id}/marketpilot/signals/<safe-name>.json`.
- Added `scripts/qc_object_store_signal_smoke.py`, disabled by default behind
  `MARKETPILOT_QC_OBJECT_STORE_SMOKE_ENABLED=1`.
- Added LEAN Object Store polling in `lean/main.py`, disabled unless an
  explicit signal key is configured.
- Routed Object Store payloads through the existing MarketPilot command
  normalization, stale-window, duplicate-idempotency, paper-only, and safe-tag
  validation path.
- Added tests for Object Store API request shapes, multipart upload behavior,
  namespace rejection, dry-run redaction, LEAN polling, stale rejection, and
  malformed JSON rejection.

## External Smoke Status

Status: `blocked_external_object_store_write_not_verified`

Credentialed QuantConnect env vars were loaded from the local ignored
`.secrets/` file. Secret values were not committed or documented.

Sanitized external results:

- Existing Paper deployment stop attempt returned `success=false`.
- Object Store smoke compiled the injected-key Paper algorithm successfully:
  compile `cc45d0b42ae58f274bd3b813432bcbcf-845d50c9f70c2df38cedff8fdf2e5eba`
  returned `BuildSuccess`.
- Paper deploy `L-1d49f38582cfbf61646aa479f54fbaa7` returned `Running`.
- The QC project file was restored after deploy.
- `/object/set` for key
  `32900381/marketpilot/signals/object-store-smoke-20260616181357.json`
  returned `success=false` with sanitized error `Organization not found`.
- `/object/properties` for the same key returned `success=false` with
  `File not found`.
- Eighteen `/live/logs/read` and `/live/orders/read` polls observed 0 logs,
  0 orders, and no Object Store receipt marker.
- Cleanup returned `success=false` because the object was not created.
- The temporary Paper deployment was stopped successfully after diagnostics.

No Object Store algorithm receipt, order, fill, rejection, or portfolio-change
evidence is claimed.

## Verification

- `python -m pytest tests/test_qc_api.py tests/test_lean_command_flow.py -q` - passed.
- `python -m pytest tests/test_qc_api.py tests/test_lean_command_flow.py tests/test_paper_order_flow_e2e.py -q` - passed.
- Direct dry-run of `scripts/qc_object_store_signal_smoke.py --dry-run --skip-deploy` - passed with fake env values.

## Residual Risk

- The QuantConnect UI shows the active organization as `FREE / UPGRADE`; the
  Object Store API may require a different paid organization state or storage
  permission even though `/account/read` and `projects/read` expose the same
  organization id.
- Phase 15 still cannot be marked externally complete because neither Commands
  dispatch nor Object Store delivery produced algorithm receipt or
  order/rejection evidence.
- If Object Store permissions are enabled later, rerun the same smoke and
  require `/object/set` success plus algorithm receipt and
  `/live/orders/read` evidence before marking the fallback passed.

## Next Step

Resolve QuantConnect Object Store organization/storage permissions or select a
different supported delivery path. Do not proceed to scheduler automation until
Phase 15 has real Paper delivery-to-order/rejection evidence.

---
*Phase: 15-paper-trading-order-flow*
*Completed: local Object Store fallback implementation with external write blocker on 2026-06-16*
