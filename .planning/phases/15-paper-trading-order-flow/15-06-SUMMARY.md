---
phase: 15-paper-trading-order-flow
plan: "06"
subsystem: quantconnect-paper-command-smoke
tags: [quantconnect, paper-trading, commands, smoke, gap-closure]

requires:
  - phase: 15-paper-trading-order-flow
    provides: "Phase 15 plans 01-05 built and externally smoke-tested deployment, command API acceptance, and order polling boundaries"
provides:
  - "Disabled-by-default QuantConnect command smoke helper with sanitized output"
  - "Tolerant LEAN command normalization for likely QuantConnect dynamic payload variants"
  - "External evidence that typed command API acceptance still produced no callback logs or live orders"
affects: [phase-15-paper-trading-order-flow, quantconnect-paper-operations]

tech-stack:
  added: []
  patterns: [disabled-external-smoke-helper, callback-vs-api-evidence-separation, sanitized-qc-evidence]

key-files:
  created:
    - scripts/qc_command_smoke.py
    - .planning/phases/15-paper-trading-order-flow/15-06-SUMMARY.md
  modified:
    - marketpilot/qc_api.py
    - marketpilot/lean_command_receiver.py
    - tests/test_qc_api.py
    - tests/test_lean_command_flow.py
    - docs/paper_trading_order_flow.md
    - docs/testing.md
    - .planning/phases/15-paper-trading-order-flow/15-UAT.md
    - .planning/phases/15-paper-trading-order-flow/15-VERIFICATION.md

key-decisions:
  - "QuantConnect command API success remains separate from callback receipt, order placement, fill evidence, or portfolio change."
  - "The smoke helper refuses to run unless MARKETPILOT_QC_COMMAND_SMOKE_ENABLED=1 and redacts secret environment values."
  - "Phase 15 remains blocked_external_callback_not_verified because typed command API success still produced no observable on_command log or live order."

patterns-established:
  - "External smoke scripts must support dry-run and sanitized JSON output."
  - "LEAN command normalization may support likely dynamic command envelope variants only after offline tests preserve all safety gates."

requirements-completed: []

duration: 26min
completed: 2026-06-16T13:36:00Z
---

# Phase 15 Plan 06: QuantConnect Command Callback Gap Summary

**Command smoke helper, tolerant receiver normalization, and external callback blocker evidence**

## Performance

- **Tasks completed:** 2/3
- **Checkpoint:** Task 3 remains blocked on missing observable QuantConnect callback/order evidence.
- **Local Python:** 3.10.10

## Accomplishments

- Added `scripts/qc_command_smoke.py`, a guarded operator smoke helper for QuantConnect Paper commands.
- Added `QCApiClient.read_live_logs()` and allowlisted the read-only `live/logs/read` diagnostic endpoint.
- Added offline tests proving the smoke helper refuses by default, redacts secret env values, supports dry-run, and builds both plain and typed probe payloads.
- Extended `marketpilot.lean_command_receiver.normalize_marketpilot_command()` to accept likely QuantConnect dynamic payload variants:
  - PascalCase attribute-style fields.
  - `$type` + `parameters` envelope.
  - Nested `marketpilot_signal` payload.
- Preserved unsafe-order rejection for direct typed order probes and existing stale, duplicate, non-paper, malformed, unsupported-symbol, and non-integer gates.

## External Smoke Evidence

Sanitized external smoke on 2026-06-16:

- Synced updated `main.py` and `marketpilot/lean_command_receiver.py` to QuantConnect project `32900381`.
- Cloud compile `54a09ada5318ca08dfd15e3ac7ec12ad-b1d7a4c2bb865f244914254e68bd0b07` returned `BuildSuccess`.
- Paper deployment `L-bd51091b63e10262fac1b2ca8b877f49` was created and reached running state.
- `scripts/qc_command_smoke.py --command-label typed_order_command_probe` returned `command_api_success=true`.
- Twelve polls over about one minute returned 0 live logs and 0 live orders.

Status: `blocked_external_callback_not_verified`

No callback receipt, order, fill, rejection, or portfolio-change evidence is claimed.

## Verification

- `python -m pytest tests/test_qc_api.py tests/test_lean_command_flow.py -q` - passed.
- `python -m pytest tests/test_lean_command_flow.py tests/test_lean_runtime_bridge_static.py -q` - passed.
- `python -m pytest tests/test_qc_api.py tests/test_lean_command_flow.py tests/test_paper_order_flow_e2e.py tests/test_paper_order_flow.py tests/test_sync.py -q` - passed.

## Residual Risk

- QuantConnect Cloud accepted plain and typed command API payloads, but did not expose observable Python `on_command` callback behavior through logs or orders.
- PTD-02, PTD-05, FT-03, FT-04, and the running command-to-order phase goal remain externally blocked.

## Next Step

Investigate QuantConnect Cloud live command dispatch semantics beyond payload shape. Likely next probes are official built-in `OrderCommand` behavior in a throwaway/safe paper context, support/forum/API confirmation, or an alternate signal-delivery mechanism such as Object Store polling. Do not mark Phase 15 complete until real callback-to-order or callback-to-rejection evidence exists.

---
*Phase: 15-paper-trading-order-flow*
*Completed: blocked external callback verification on 2026-06-16*
