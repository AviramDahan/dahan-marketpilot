---
phase: 15-paper-trading-order-flow
plan: "12"
subsystem: quantconnect-order-authority
tags: [quantconnect, paper-trading, object-store, live-orders, gap-closure]

requires:
  - phase: 15-paper-trading-order-flow
    provides: "Phase 15-11 keep-running safety for next-open observation"
provides:
  - "Exact current-run order-tag filtering in Object Store smoke"
  - "LEAN Object Store signal deferral until symbol price data is available"
  - "Market-hours external evidence: live logs show Submitted and Filled"
  - "Residual blocker: `/live/orders/read` does not return current expected tag"
affects: [phase-15-paper-trading-order-flow, quantconnect-paper-operations]

key-files:
  created:
    - .planning/phases/15-paper-trading-order-flow/15-12-SUMMARY.md
  modified:
    - scripts/qc_object_store_signal_smoke.py
    - tests/test_qc_api.py
    - lean/main.py
    - tests/test_lean_command_flow.py
    - docs/paper_trading_order_flow.md
    - docs/testing.md
    - .planning/phases/15-paper-trading-order-flow/15-UAT.md
    - .planning/phases/15-paper-trading-order-flow/15-VERIFICATION.md

key-decisions:
  - "Only the exact current expected order tag can satisfy the Object Store smoke authority check."
  - "Stale MarketPilot-tagged orders from older deployments are not current order authority."
  - "A valid Object Store signal must remain retryable when LEAN has no tradeable symbol price yet."
  - "Live-log Submitted/Filled evidence is strong external evidence, but it still does not close the `/live/orders/read` authority gate."

requirements-completed: []

duration: 54min
completed: 2026-06-17T14:05:00Z
---

# Phase 15 Plan 12: Order-Authority Follow-Up Summary

**Status:** `live_logs_filled_but_orders_read_current_tag_missing`.

Phase 15 remains partial. The market-hours smoke produced a real QuantConnect
Paper Submitted/Filled event in live logs, but `/live/orders/read` did not return
the current expected MarketPilot order tag, so the official order-authority gate
is still open.

## Accomplishments

- Ran the Phase 15 market-hours Object Store Paper smoke with explicit
  `--keep-running`.
- Stopped every temporary Paper deployment created by the run.
- Found and fixed a smoke false-positive hazard:
  `/live/orders/read` can return stale MarketPilot-tagged orders from older
  deployments. The smoke now requires the exact current expected tag
  `mp:<signal_id>:<idempotency_key>`.
- Found and fixed a LEAN timing hazard:
  Object Store polling can run before SPY has tradeable price data. The LEAN
  adapter now keeps valid Object Store signals unprocessed and retries later
  instead of losing the signal.
- Updated UAT, verification, and operator docs with the new evidence and
  residual blocker.

## External Evidence

First market-hours run:

- Compile: `df0ca92b23043e5b021dbe5b03341c98-0f21c3d4172c2d7b70be5c238f76f388`,
  `BuildSuccess`.
- Deployment: `L-67a85a4c30502c949632f877d82e7eb6`.
- `/live/orders/read` returned a stale tagged order from deployment
  `L-103091222fcd6eee4aae06e1de635e38`, not the current signal.
- Deployment stop: `stop_success=true`.

Second market-hours run after exact-tag filtering:

- Compile: `51a72b4c363abe083946c0b90c8a4b7b-678e2b12dc8150d523273cc83be555bf`,
  `BuildSuccess`.
- Deployment: `L-63fc5246cde5e087050c40b14f590fd1`.
- Object Store receipt and acceptance were observed.
- LEAN logged `SPY: The security does not have an accurate price...`, and no
  current tagged order appeared in `/live/orders/read`.
- Deployment stop: `stop_success=true`.

Final market-hours run after price-data deferral:

- Object Store key:
  `32900381/marketpilot/signals/object-store-smoke-20260617135051.json`.
- Compile: `dc91c5ab5e0058488a8d1d9f2df34e67-b2ee161c2a598a4ba7551a28468e76ff`,
  `BuildSuccess`.
- Deployment: `L-3eccd7fbf41cc4b0aa944d500f760a90`.
- Expected current tag:
  `mp:qc-object-store-sig-20260617135051:qc-object-store-order-20260617135051`.
- Live logs showed:
  - Object Store signal received.
  - Object Store accepted: `SPY 1`.
  - QuantConnect `Submitted` event for SPY quantity 1.
  - QuantConnect `Filled` event for SPY quantity 1 at fill price `$751.31`.
- `/live/orders/read` returned one older tagged order from deployment
  `L-103091222fcd6eee4aae06e1de635e38`; it did not return the current expected
  tag.
- `/live/read` for the current deployment returned no order rows after stop.
- Object cleanup: `cleanup_success=true`.
- Deployment stop: `stop_success=true`.

## Verification

- `python -m pytest tests/test_qc_api.py -q` - passed.
- `python -m pytest tests/test_lean_command_flow.py tests/test_qc_api.py -q` -
  passed.
- `python -m pytest tests/test_qc_api.py tests/test_lean_command_flow.py tests/test_paper_order_flow_e2e.py tests/test_paper_order_flow.py tests/test_sync.py -q`
  - passed.
- Local secret scan against the known QuantConnect, Telegram, and account
  redaction patterns across `.planning`, docs, scripts, tests, `marketpilot`,
  and `lean` - no matches.
- Credentialed QuantConnect Object Store smoke - partial external:
  live-log Submitted/Filled observed, `/live/orders/read` current tag missing.

## Residual Risk

- The official `/live/orders/read` endpoint is still not returning the current
  tagged order/fill even when live logs show the order was submitted and filled.
- Phase 15 cannot be marked complete from live-log evidence alone.
- The next gap must determine whether the correct QuantConnect order-authority
  source is another API shape, a deployment/clone ID nuance, an endpoint
  pagination/history limitation, or a required post-stop/live-read timing rule.

## Next Step

Plan a narrow follow-up around QuantConnect order-authority retrieval semantics:
compare `/live/orders/read`, `/live/read`, deployment/clone identifiers, and any
officially supported order-history source for the current deployment. Do not
rerun broad smokes until the authority endpoint behavior is understood.

---
*Phase: 15-paper-trading-order-flow*
*Completed: market-hours live-log fill observed; `/live/orders/read` current-tag authority still pending on 2026-06-17*
