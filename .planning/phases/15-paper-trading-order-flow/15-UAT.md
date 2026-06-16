# Phase 15 UAT: Paper Trading Order Flow

## Scope

This UAT record covers Phase 15 simulated paper order flow only. It must not be
read as evidence of real-money trading, real brokerage access, or profitability.

SIMULATED PAPER TRADING ONLY - NOT FINANCIAL ADVICE.

## Acceptance Summary

| Area | Status | Evidence |
|------|--------|----------|
| Offline deterministic E2E behavior | passed_offline | `pytest tests/test_paper_order_flow_e2e.py tests/test_paper_order_flow.py tests/test_lean_command_flow.py tests/test_qc_api.py -q` passed during Task 1. |
| Targeted Phase 15 and sync regression command | passed_offline | `pytest tests/test_paper_order_flow_e2e.py tests/test_paper_order_flow.py tests/test_lean_command_flow.py tests/test_qc_api.py tests/test_sync.py -q` passed during Task 2. |
| Full local pytest suite | passed_with_version_caveat | `pytest -q` passed under local Python 3.10.10; project metadata requires Python >=3.11 for strict/release verification. |
| Real QuantConnect paper read smoke | passed_external_read_only | On 2026-06-16T12:46:23Z, authenticated QuantConnect API reads verified project `32900381`, deploy `L-223eafd89aaac127343bb441bf96e423`, deployment status `running`, algorithm status `running`, equity `27027.03`, and successful `/live/orders/read` with 0 orders. |
| Real QuantConnect paper command/order smoke | blocked_external_callback_not_verified | Phase 15-06 synced the callback-tolerant receiver, compiled successfully, deployed to Paper, and `/live/commands/create` returned success for `typed_order_command_probe`. However, no `on_command` debug log and no live order appeared after polling, so command callback/order execution is not externally verified. |
| Phase 15 full pass / phase-complete | blocked_external_callback_not_verified | Offline tests, cloud sync, compile, live create, read-only smoke, and command API acceptance passed, but real `on_command` to order delivery is not externally verified. |

## Offline User Acceptance Checks

| Check | Result | Notes |
|-------|--------|-------|
| Runtime `OrderIntent` becomes MarketPilot signal command | passed_offline | E2E test verifies payload fields and `command_delivery_is_order_execution=false`. |
| Fresh command passes local sync/stale/duplicate gates | passed_offline | Uses fake fresh Phase 14 sync JSONL in `tmp_path`. |
| Mocked Commands API delivery does not imply order execution | passed_offline | Submission result keeps `order_executed=false`. |
| Fake LEAN `on_command` accepts fresh command and places one tagged paper order | passed_offline | Fake algorithm records `market_order("MSFT", 10, tag="mp:sig-001:order-intent-abc123")`. |
| Duplicate signal rejected before API delivery | passed_offline | Second local submission produces `duplicate_signal_rejected` and no second fake API call. |
| Duplicate command rejected inside LEAN | passed_offline | Second direct LEAN command injection returns false and no second order. |
| Stale signal skipped locally | passed_offline | Local result is `signal_skipped`, no fake API call. |
| Stale direct LEAN injection rejected | passed_offline | Fake LEAN receiver returns false and places no order. |
| Partial fill evidence mirrored from mocked QC order polling | passed_offline | Audit trace includes `paper_fill_observed` with `status=partially_filled`. |
| Rejection reason mirrored from mocked QC order polling | passed_offline | Audit trace includes `paper_order_rejected` with reason text from fake QC payload. |
| Signal-to-order-to-fill trace queryable | passed_offline | Trace helper reconstructs records by `signal_id` or `idempotency_key`. |

## External QuantConnect Smoke Status

Status: `partial_external_verified_command_api_only`

Environment/API check on 2026-06-16:

| Item | Status |
|------|--------|
| `QUANTCONNECT_USER_ID` | configured for this operator-run smoke; value not recorded |
| `QUANTCONNECT_API_TOKEN` | configured for this operator-run smoke; value not recorded |
| `QC_PROJECT_ID` | discovered as `32900381` |
| `QC_DEPLOY_ID` | discovered as `L-223eafd89aaac127343bb441bf96e423` |
| `QC_VERSION_ID` | discovered as LEAN version `17835` |
| `QC_COMPILE_ID` | not discovered; only required for creating a new deployment |
| `QC_NODE_ID` | not discovered; only required for creating a new deployment |
| `/live/list` | passed; deployment visible as Paper `Running` |
| `/live/read` | passed; parsed snapshot status `running`, equity `27027.03` |
| `/live/orders/read` | passed; success true, 0 orders |
| Phase 15 cloud file sync | passed; `main.py` plus 28 `marketpilot/` files present in QC project |
| Cloud compile | passed; compile `76fe4ebdce72ca35574db67ad60b0433-9fbcc5e87d8c7d73346eda85b8851386`, `BuildSuccess` |
| Paper deployment create | passed; deploy `L-6e97706430e5dfec3e6615282153ad47`, status `Running` |
| `/live/commands/create` | passed; API returned `success=true` for a `marketpilot_signal` smoke command |
| `on_command` debug/order evidence | blocked; no `MarketPilot command received` log and no order after polling `/live/logs/read` and `/live/orders/read` |
| Phase 15-06 smoke helper | passed_offline; refuses by default unless `MARKETPILOT_QC_COMMAND_SMOKE_ENABLED=1`; dry-run output redacts secrets |
| Phase 15-06 command normalization | passed_offline; accepts lower-case payloads, PascalCase dynamic attributes, `parameters` envelope, and nested `marketpilot_signal` while preserving unsafe-order rejection |
| Phase 15-06 cloud compile | passed; compile `54a09ada5318ca08dfd15e3ac7ec12ad-b1d7a4c2bb865f244914254e68bd0b07`, `BuildSuccess` |
| Phase 15-06 Paper deployment create | passed; deploy `L-bd51091b63e10262fac1b2ca8b877f49`, status `Running` |
| Phase 15-06 typed command smoke | blocked_external_callback_not_verified; `typed_order_command_probe` returned `command_api_success=true`, 12 polls over ~60s returned 0 logs and 0 orders |

Credentialed QuantConnect command delivery was accepted by the API, but no real
external LEAN callback, order, fill, or rejection result is claimed by this UAT
record. Mocks and fake fills are local regression evidence only.

The current blocker is narrower than initial setup: QuantConnect accepts both
plain and typed command requests, but the Python `on_command` receiver did not
produce debug or order evidence during the smoke windows.

## Human Verification Gate

Before Phase 15 can be marked fully passed, an operator must resolve why
QuantConnect's accepted live command does not trigger observable `on_command`
behavior in the Paper deployment, then rerun the smallest safe command smoke.
The resulting evidence must be sanitized and must include only safe identifiers,
timestamps, paper-only status, command delivery status, and observed
QuantConnect order/fill/rejection trace status. Secrets must never be recorded.
