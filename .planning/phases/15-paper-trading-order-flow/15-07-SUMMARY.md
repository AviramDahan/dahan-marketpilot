---
phase: 15-paper-trading-order-flow
plan: "07"
subsystem: quantconnect-command-dispatch-diagnosis
tags: [quantconnect, commands, paper-trading, diagnostics, gap-closure]

requires:
  - phase: 15-paper-trading-order-flow
    provides: "Phase 15-06 command API acceptance and callback/order blocker evidence"
provides:
  - "Guarded no-order QuantConnect command-dispatch probe"
  - "Official generic command payload alignment for MarketPilot smoke"
  - "Sanitized command receipt evidence in LEAN before payload parsing"
  - "Documentation that external dispatch probe was not run because QC env vars were missing"
affects: [phase-15-paper-trading-order-flow, quantconnect-paper-operations]

tech-stack:
  added: []
  patterns: [disabled-external-smoke-helper, sanitized-dispatch-probe, official-command-payload-alignment]

key-files:
  created:
    - scripts/qc_command_dispatch_probe.py
    - .planning/phases/15-paper-trading-order-flow/15-07-SUMMARY.md
  modified:
    - marketpilot/qc_api.py
    - scripts/qc_command_smoke.py
    - lean/main.py
    - tests/test_qc_api.py
    - tests/test_lean_command_flow.py
    - docs/paper_trading_order_flow.md
    - docs/testing.md
    - .planning/phases/15-paper-trading-order-flow/15-UAT.md
    - .planning/phases/15-paper-trading-order-flow/15-VERIFICATION.md

key-decisions:
  - "A generic no-`$type` payload is the primary command-dispatch diagnostic because official QuantConnect docs route generic payloads to `on_command`."
  - "Typed command payloads are retained only as diagnostics and use flat fields, not a nested `parameters` envelope."
  - "External callback/order verification remains blocked until QC env vars are configured in the active process and the no-order dispatch probe is run."

patterns-established:
  - "Before debugging MarketPilot order logic, isolate QuantConnect generic command dispatch with a no-order echo algorithm."
  - "External smoke scripts must be directly runnable from `scripts\\...` and bootstrap the repository root onto `sys.path`."

requirements-completed: []

duration: 41min
completed: 2026-06-16T17:45:00Z
---

# Phase 15 Plan 07: Command Dispatch Diagnosis Summary

**Local diagnostic tooling complete; credentialed external dispatch probe not run due missing env.**

## Performance

- **Tasks completed:** 2/4 fully, 1/4 documented as not run, 1/4 skipped.
- **Checkpoint:** `not_run_missing_env` for external QuantConnect dispatch probe.
- **Local Python:** 3.10.10

## Accomplishments

- Added `scripts/qc_command_dispatch_probe.py`, a guarded no-order diagnostic
  for QuantConnect generic Commands API dispatch.
- Added `QCApiClient` wrappers for project file read/update and compile
  create/read endpoints used by the diagnostic probe.
- Updated `scripts/qc_command_smoke.py` so typed diagnostics use flat fields
  instead of a nested `parameters` envelope.
- Added sanitized command receipt evidence in `lean/main.py` before parsing or
  validation.
- Added tests for the dispatch probe enable gate, dry-run redaction, no-order
  algorithm body, official generic payload, flat typed diagnostic payload, and
  new API wrappers.
- Verified both scripts can be run directly from the repo root with dry-run
  settings.

## External Smoke Status

Status: `not_run_missing_env`

The active process did not have these env vars configured:

- `QUANTCONNECT_USER_ID`
- `QUANTCONNECT_API_TOKEN`
- `QC_PROJECT_ID`
- `QC_DEPLOY_ID`
- `QC_NODE_ID`
- `QC_VERSION_ID`

No credentialed external QuantConnect command dispatch probe was run in this
plan. No callback, order, fill, rejection, or portfolio-change evidence is
claimed.

## Verification

- `python -m pytest tests/test_qc_api.py -q` - passed.
- `python -m pytest tests/test_lean_command_flow.py tests/test_paper_order_flow_e2e.py -q` - passed.
- Direct dry-run of `scripts/qc_command_dispatch_probe.py --dry-run --skip-deploy` - passed with fake env values.
- Direct dry-run of `scripts/qc_command_smoke.py --dry-run --command-label typed_order_command_probe` - passed with fake env values.

## Residual Risk

- Phase 15 still cannot be marked externally complete until the no-order
  dispatch probe is run with real QuantConnect env vars in the active process.
- If the no-order probe receives no log marker after API acceptance, the likely
  blocker is QuantConnect command dispatch or account/project behavior, not
  MarketPilot order logic.
- If the no-order probe receives the marker, rerun the MarketPilot generic
  command smoke and require callback-to-order or callback-to-rejection evidence.

## Next Step

Configure QuantConnect env vars in the current shell and run:

`python scripts\qc_command_dispatch_probe.py --command-label generic_echo`

Do not paste or commit credential values. If the probe passes, continue with the
MarketPilot generic command smoke. If it does not pass, record the external
dispatch blocker or implement only a supported paper-only fallback.

---
*Phase: 15-paper-trading-order-flow*
*Completed: local diagnostic gap closure on 2026-06-16*
