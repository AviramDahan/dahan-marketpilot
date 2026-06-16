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
  - "Sanitized evidence that a credentialed no-order dispatch probe deployed successfully but produced no observable marker"
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
  - "External callback/order verification remains blocked because a no-order generic dispatch probe still produced no observable log marker."

patterns-established:
  - "Before debugging MarketPilot order logic, isolate QuantConnect generic command dispatch with a no-order echo algorithm."
  - "External smoke scripts must be directly runnable from `scripts\\...` and bootstrap the repository root onto `sys.path`."

requirements-completed: []

duration: 41min
completed: 2026-06-16T17:45:00Z
---

# Phase 15 Plan 07: Command Dispatch Diagnosis Summary

**Local diagnostic tooling complete; credentialed no-order dispatch still not observed.**

## Performance

- **Tasks completed:** 3/4 completed, 1/4 skipped because Commands dispatch remains blocked.
- **Checkpoint:** `blocked_external_dispatch_not_observed`.
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

Status: `blocked_external_dispatch_not_observed`

Credentialed QuantConnect env vars were saved in a local ignored `.secrets/`
file and used only in the active process. Secret values were not committed or
documented.

Sanitized external results:

- Existing Paper deployment was stopped.
- Echo compile `677437f56a306fab73f489b921f92652-dbdb35fb652acd584047b1e67f1a13b0` returned `BuildSuccess`.
- Echo Paper deployment `L-2c24272bebaead4a441fadf048662324` returned `Running`.
- Generic echo `/live/commands/create` returned success.
- Twelve immediate polls showed 0 live logs and no `MARKETPILOT_DISPATCH_PROBE_RECEIVED` marker.
- A delayed follow-up generic command to the same deploy also returned command API success.
- Eighteen delayed polls showed 0 live logs and no marker.
- The echo deployment was stopped after the probe.

No callback, order, fill, rejection, or portfolio-change evidence is claimed.

## Verification

- `python -m pytest tests/test_qc_api.py -q` - passed.
- `python -m pytest tests/test_lean_command_flow.py tests/test_paper_order_flow_e2e.py -q` - passed.
- Direct dry-run of `scripts/qc_command_dispatch_probe.py --dry-run --skip-deploy` - passed with fake env values.
- Direct dry-run of `scripts/qc_command_smoke.py --dry-run --command-label typed_order_command_probe` - passed with fake env values.

## Residual Risk

- Phase 15 still cannot be marked externally complete because even the no-order
  generic echo probe did not produce observable `on_command` log evidence.
- The likely blocker is QuantConnect command dispatch semantics, live log
  visibility, or account/project behavior, not MarketPilot order logic.
- If a future probe receives the marker, rerun the MarketPilot generic command
  smoke and require callback-to-order or callback-to-rejection evidence.

## Next Step

Investigate a supported alternate delivery path or QuantConnect-specific command
registration requirement. Do not keep modifying MarketPilot order logic until a
no-order callback receipt is observable. If using a fallback, it must remain
paper-only, idempotent, and externally proven before Phase 15 can pass.

---
*Phase: 15-paper-trading-order-flow*
*Completed: local diagnostic gap closure on 2026-06-16*
