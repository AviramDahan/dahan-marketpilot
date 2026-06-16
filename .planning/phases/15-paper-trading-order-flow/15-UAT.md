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
| Real QuantConnect paper smoke | blocked_external_not_verified | Required QuantConnect environment variables were not configured locally on 2026-06-16. No external paper command, order, fill, or rejection evidence was produced. |
| Phase 15 full pass / phase-complete | blocked_external_not_verified | Offline tests passed, but real running-QuantConnect delivery is not externally verified. |

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

Status: `blocked_external_not_verified`

Environment presence check on 2026-06-16:

| Variable | Configured locally |
|----------|--------------------|
| `QUANTCONNECT_USER_ID` | no |
| `QUANTCONNECT_API_TOKEN` | no |
| `QC_PROJECT_ID` | no |
| `QC_DEPLOY_ID` | no |
| `QC_COMPILE_ID` | no |
| `QC_NODE_ID` | no |
| `QC_VERSION_ID` | no |

No credentialed QuantConnect paper smoke command was run. No real external
QuantConnect deployment, command delivery, order, fill, or rejection result is
claimed by this UAT record. Mocks and fake fills are local regression evidence
only.

## Human Verification Gate

Before Phase 15 can be marked fully passed, an operator must configure the
required QuantConnect paper-only environment outside chat and run the smallest
paper smoke path against a user-managed running paper deployment. The resulting
evidence must be sanitized and must include only safe identifiers, timestamps,
paper-only status, command delivery status, and observed QuantConnect
order/fill/rejection trace status. Secrets must never be recorded.
