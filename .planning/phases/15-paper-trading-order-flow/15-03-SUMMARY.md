---
phase: 15-paper-trading-order-flow
plan: 03
subsystem: paper-order-flow
tags: [quantconnect, lean, commands-api, paper-trading, idempotency, pytest]

requires:
  - phase: 15-paper-trading-order-flow
    provides: "Plan 15-02 MarketPilot signal command payloads, idempotency keys, and shared order tag helpers"
  - phase: 10.1-close-gap-runtime-orchestrator-for-strategy-to-paper-e2e-flo
    provides: "Thin LEAN runtime adapter pattern with strategy/risk logic delegated to MarketPilot runtime modules"
provides:
  - "Pure LEAN command receiver helpers for MarketPilot signal normalization, schema validation, stale expiry checks, duplicate idempotency rejection, and order tag construction"
  - "DahanMarketPilotRuntime on_command hook that submits exactly one tagged paper market_order for accepted MarketPilot signal commands"
  - "DahanMarketPilotRuntime on_order_event evidence capture with order id, status, fill quantity/price, tag, signal id, and idempotency key"
  - "Offline fake-LEAN tests and static safety tests preserving Phase 10.1 bans while allowing only the audited tagged market_order path"
affects: [phase-15-plan-04-fill-tracking, phase-15-plan-05-e2e-verification, phase-16-scheduler]

tech-stack:
  added: []
  patterns: [pure-lean-command-receiver, audited-tagged-market-order, sanitized-order-event-evidence, fake-lean-tests]

key-files:
  created:
    - marketpilot/lean_command_receiver.py
    - .planning/phases/15-paper-trading-order-flow/15-03-SUMMARY.md
  modified:
    - lean/main.py
    - tests/test_lean_command_flow.py
    - tests/test_lean_static_safety.py
    - tests/test_lean_runtime_bridge_static.py

key-decisions:
  - "LEAN accepts only MarketPilot signal commands with paper-only, freshness, schema, supported-symbol, and duplicate-idempotency validation before any order call."
  - "The only allowed LEAN order path is one tagged self.market_order(validation.symbol, validation.quantity, tag=validation.tag) inside on_command."
  - "Order-event evidence is sanitized trace context only and does not become local order/fill authority."

patterns-established:
  - "Command normalization and validation live in a pure marketpilot module with no AlgorithmImports, QCAlgorithm, REST client, network, scoring, ranking, risk, or reconciliation imports."
  - "The LEAN adapter stores in-algorithm seen idempotency keys and rejects duplicate commands before market_order."
  - "Static safety tests permit market_order only when the source also contains def on_command and tag=validation.tag."

requirements-completed: [PTD-02, PTD-05, SAFE-05]

duration: 9min
completed: 2026-06-16T11:56:03Z
---

# Phase 15 Plan 03: LEAN Command Receiver Summary

**LEAN-side MarketPilot signal receiver with paper-only validation, duplicate/stale rejection, and audited tagged paper market orders**

## Performance

- **Duration:** 9 min
- **Started:** 2026-06-16T11:46:41Z
- **Completed:** 2026-06-16T11:56:03Z
- **Tasks:** 2
- **Files modified:** 6
- **Local Python:** 3.10.10

## Accomplishments

- Added `marketpilot/lean_command_receiver.py` with pure dataclasses and helpers for dict/attribute payload normalization, strict command validation, UTC timestamp parsing, symbol/quantity checks, stale expiry rejection, duplicate idempotency rejection, and shared order tag creation.
- Added `DahanMarketPilotRuntime.on_command()` that returns `False` for rejected commands without order placement and places exactly one tagged `market_order` for accepted MarketPilot paper signal commands.
- Added `DahanMarketPilotRuntime.on_order_event()` evidence capture for order id, status, fill quantity, fill price, tag, signal id, and idempotency key while omitting message/secret-like fields.
- Added offline fake-LEAN tests and static safety assertions proving the controlled order path is narrow and no brokerage, live-money, credential, liquidation, leverage, margin, unsupported-asset, scoring, ranking, risk, or reconciliation logic was duplicated in `lean/main.py`.

## Task Commits

1. **Task 1 RED: LEAN command receiver helper tests** - `c969eb6` (test)
2. **Task 1 GREEN: LEAN command receiver helpers** - `e63505b` (feat)
3. **Task 2 RED: LEAN command hook and static safety tests** - `a995114` (test)
4. **Task 2 GREEN: LEAN command receiver hooks** - `0eab592` (feat)

## Files Created/Modified

- `marketpilot/lean_command_receiver.py` - Pure command normalization and validation boundary used by LEAN.
- `lean/main.py` - Added command idempotency state, `on_command`, sanitized `on_order_event`, and small local helper methods.
- `tests/test_lean_command_flow.py` - Offline helper and fake-LEAN tests for accepted commands, stale/duplicate/malformed/non-paper rejections, exactly-one order placement, and order-event evidence.
- `tests/test_lean_static_safety.py` - Static LEAN safety policy updated to allow only the audited tagged `market_order` path.
- `tests/test_lean_runtime_bridge_static.py` - Runtime bridge static safety policy updated to keep `market_order` out of the bridge while permitting the audited LEAN command hook.
- `.planning/phases/15-paper-trading-order-flow/15-03-SUMMARY.md` - Plan execution summary.

## Verification

- `pytest tests/test_lean_command_flow.py -q` - passed, 13 tests after Task 1 GREEN.
- `pytest tests/test_lean_command_flow.py tests/test_lean_static_safety.py tests/test_lean_runtime_bridge_static.py -q` - passed, 36 tests after Task 2 GREEN and again after commits.
- `rg "SetBrokerageModel|set_brokerage_model|InteractiveBrokers|live_money|real_money|Liquidate|liquidate|api_key|token|password" lean/main.py marketpilot/lean_command_receiver.py` - passed; no matches in implementation files.
- Broader token scan confirmed the only `market_order` outside tests is `self.market_order(validation.symbol, validation.quantity, tag=validation.tag)` in `lean/main.py`; other unsafe terms appear only as controlled test-policy strings.
- Official QuantConnect docs were rechecked for Python `market_order` and order tags before implementation.

## Decisions Made

- LEAN command validation is deliberately limited to command schema, paper-only flags, freshness, idempotency, symbol/quantity safety, and tag construction; upstream scoring/ranking/risk/reconciliation remains outside `lean/main.py`.
- Rejected commands are represented as local rejection evidence on the algorithm instance and do not mutate `marketpilot_seen_command_keys`.
- Accepted commands mutate the seen-key set before returning and use the shared `build_order_tag()` format from Plan 15-02 for traceability.
- `on_order_event` reads the tag back from the LEAN transaction manager when available and records only minimal trace fields.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- The first RED test patch was accidentally applied from the Codex shell directory instead of the target repository. It was deleted immediately and re-added under the target repo before verification or commit.
- A pre-existing unrelated worktree change appeared briefly in `marketpilot/paper_order_flow.py`; it was not staged, committed, modified, or reverted by this plan.
- The fake-LEAN test harness sets `algorithm.time` to a fixed UTC timestamp so stale-command tests are deterministic and independent of wall-clock execution time.

## Known Stubs

None. Stub-pattern scan hits in modified files are test literals, string arguments, or static-policy strings; they are not unfinished UI/data placeholders or unwired behavior.

## Threat Flags

None beyond the plan's declared trust boundaries. This plan intentionally adds the LEAN Commands API receiver and LEAN paper-order boundary with mitigations for payload tampering, stale replay, duplicate replay, uncontrolled order paths, and secret-free order-event evidence.

## Auth Gates

None. All verification was deterministic and offline; no QuantConnect credentials were used or requested.

## Residual Risks

- Real QuantConnect paper runtime execution was not performed; this plan verified behavior through offline fake-LEAN tests and static source checks only.
- `on_order_event` evidence depends on LEAN transaction-manager tag recovery when available; authoritative fill/rejection state remains deferred to Plan 15-04 via `/live/orders/read`.
- Local tests ran under Python 3.10.10 while project metadata requires Python >=3.11 for strict/release validation.

## User Setup Required

None for this plan. Future credentialed paper smoke checks still require user-managed QuantConnect credentials and a paper live node outside chat.

## Next Phase Readiness

Plan 15-04 can now poll authoritative QuantConnect live orders and map returned order/fill/rejection state back to the `mp:<signal_id>:<idempotency_key>` tags produced by the LEAN receiver.

## Self-Check: PASSED

- Found created/modified files: `marketpilot/lean_command_receiver.py`, `lean/main.py`, `tests/test_lean_command_flow.py`, `tests/test_lean_static_safety.py`, `tests/test_lean_runtime_bridge_static.py`, and `.planning/phases/15-paper-trading-order-flow/15-03-SUMMARY.md`.
- Found task commits: `c969eb6`, `e63505b`, `a995114`, `0eab592`.
- Verified no tracked files were deleted by the 15-03 task commits.
- Re-ran `pytest tests/test_lean_command_flow.py tests/test_lean_static_safety.py tests/test_lean_runtime_bridge_static.py -q` successfully after task commits.

---
*Phase: 15-paper-trading-order-flow*
*Completed: 2026-06-16*
