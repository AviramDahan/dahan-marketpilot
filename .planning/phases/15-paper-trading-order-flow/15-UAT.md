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
| Phase 15-07 command-dispatch diagnosis tooling | blocked_external_dispatch_not_observed | Added a guarded no-order dispatch probe, official generic command payload alignment, and sanitized command receipt evidence. Credentialed external run compiled and deployed an echo probe, and command API returned success, but no dispatch marker appeared in live logs. |
| Phase 15-08 Object Store fallback tooling | blocked_external_object_store_write_not_verified | Added guarded Object Store API wrappers, Object Store signal smoke runner, and LEAN Object Store polling through shared validation. External compile/deploy succeeded, but `/object/set` returned `Organization not found`; no algorithm receipt or order evidence is claimed. |
| Phase 15-09 Object Store preflight diagnostics | passed_external_object_store_write | Reordered the Object Store smoke so `/object/set` runs before compile/deploy and added `--diagnose-only`. After fixing multipart uploads to avoid a JSON `Content-Type`, credentialed diagnose-only returned `success=true`, metadata was readable, and cleanup succeeded without compile/deploy/order polling. |
| Phase 15-09 full Object Store fallback smoke | object_store_written_no_algorithm_receipt_observed | Full fallback smoke wrote the signal object, compiled successfully, deployed Paper algorithm `L-35940c556bcc768d5ca186f28d868441`, restored `main.py`, cleaned up the object, and stopped the temporary deployment. Eighteen polls showed 0 live logs, 0 tagged orders, and no receipt marker. |
| Phase 15-10 live-log corrected Object Store smoke | object_store_delivery_receipt_or_rejection_observed | Corrected `/live/logs/read` request fields to `startLine`/`endLine`. Full fallback smoke observed Object Store receipt, acceptance, and a QuantConnect paper order event with status `Submitted`; `/live/orders/read` still returned 0 orders during the polling window. |
| Phase 15-11 Object Store smoke deployment safety | passed_external_auto_stop | Added default auto-stop for temporary Paper deployments and explicit `--keep-running` override. A short credentialed smoke created a Paper deployment and returned `stop_success=true`. |
| Phase 15-12 market-hours Object Store order-authority follow-up | live_logs_filled_but_orders_read_current_tag_missing | Added exact current-tag filtering to the smoke and LEAN price-data deferral. Credentialed market-hours smoke for deployment `L-3eccd7fbf41cc4b0aa944d500f760a90` observed Object Store receipt, acceptance, and QuantConnect live-log `Submitted` and `Filled` events for SPY quantity 1 at fill price `$751.31`. `/live/orders/read` still returned only an older tagged order from deployment `L-103091222fcd6eee4aae06e1de635e38`, not the current expected tag. Deployment stop succeeded. |
| Phase 15-13 snapshot-wait Object Store order-authority follow-up | passed_external_order_authority | Expanded `/live/orders/read` polling to `start=0,end=1000`, waited through QuantConnect's delayed live-order snapshot, and captured the exact current tag from `/live/orders/read`. Deployment `L-d62998269941f7f00ba48804a092c2b7` returned order id `1`, status `3`, tag `mp:qc-object-store-sig-20260617143733:qc-object-store-order-20260617143733`, Submitted and Filled order events, fill quantity `1`, fill price `$750.08`, object cleanup success, and deployment stop success. |
| Phase 15 full pass / phase-complete | passed_external_order_authority | Offline tests, cloud sync, compile, live create, read-only smoke, command API acceptance, Object Store write, Object Store signal receipt, live-log Submitted/Filled evidence, and authoritative `/live/orders/read` current-tag order/fill evidence are verified for simulated Paper Trading only. |

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

Status: `passed_external_order_authority`

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
| Phase 15-07 dispatch probe | blocked_external_dispatch_not_observed; no-order echo compile `677437f56a306fab73f489b921f92652-dbdb35fb652acd584047b1e67f1a13b0` returned `BuildSuccess`, deploy `L-2c24272bebaead4a441fadf048662324` returned `Running`, command API returned success, but 12 polls showed 0 logs and no marker |
| Phase 15-07 official payload alignment | passed_offline; `typed_order_command_probe` now uses flat fields instead of a nested `parameters` envelope, while the default `marketpilot_signal` remains a generic no-`$type` payload |
| Phase 15-07 delayed follow-up command | blocked_external_dispatch_not_observed; after waiting about 60 seconds, a second generic command to deploy `L-2c24272bebaead4a441fadf048662324` returned command API success, but 18 polls still showed 0 logs and no marker |
| Phase 15-08 Object Store local fallback | passed_offline; wrappers are allowlisted, writes/deletes are namespace-limited to `32900381/marketpilot/signals/*.json`, the smoke runner dry-runs with redaction, and fake LEAN Object Store payloads reuse command validation |
| Phase 15-08 Object Store external smoke | blocked_external_object_store_write_not_verified; compile `cc45d0b42ae58f274bd3b813432bcbcf-845d50c9f70c2df38cedff8fdf2e5eba` returned `BuildSuccess`, deploy `L-1d49f38582cfbf61646aa479f54fbaa7` returned `Running`, `/object/set` returned `Organization not found`, `/object/properties` returned `File not found`, 18 polls showed 0 logs and 0 orders, and the temporary deploy was stopped |
| Phase 15-09 Object Store diagnose-only smoke | passed_external_object_store_write; project `32900381`, organization `ed947707222a7b9aeb5de9d0974e5994`, `/object/set` returned `success=true`, `/object/properties` returned JSON metadata for key `32900381/marketpilot/signals/object-store-smoke-20260616221505.json`, cleanup succeeded, and no compile/deploy/order polling was performed |
| Phase 15-09 full Object Store fallback smoke | object_store_written_no_algorithm_receipt_observed; key `32900381/marketpilot/signals/object-store-smoke-20260616221527.json` was written, compile `462cdc22a9803673f0b85cbe82d09db0-4e5dd314ca2c676616079f237105ca84` reached `BuildSuccess`, Paper deploy `L-35940c556bcc768d5ca186f28d868441` reached `Running`, object cleanup succeeded, the deployment was stopped, and 18 polls showed 0 logs, 0 tagged orders, and no receipt marker |
| Phase 15-10 live-log corrected Object Store fallback smoke | object_store_delivery_receipt_or_rejection_observed; key `32900381/marketpilot/signals/object-store-smoke-20260616222641.json` was written, compile `17cf8c855b9f015b657bb8ee93dde36f-fc7dc35aac534131b7f46de7f1f4338f` reached `BuildSuccess`, Paper deploy `L-103091222fcd6eee4aae06e1de635e38` reached `Running`, live logs showed `MarketPilot Object Store signal received.`, `MarketPilot object_store accepted: SPY 1`, and a QuantConnect `New Order Event` with status `Submitted`; `/live/orders/read` returned 0 orders during the smoke window; object cleanup and deployment stop succeeded |
| Phase 15-11 short auto-stop smoke | passed_external_auto_stop; key `32900381/marketpilot/signals/object-store-smoke-20260616223659.json` was written, compile `afa175c1bfd2ec3fbe9761e785d36564-3a1e17366ee80c002632e087f0b2adc5` reached `BuildSuccess`, Paper deploy `L-d54a7a1b3ffb938b43db9cab1a0f2560` was created, object cleanup succeeded, `stop_attempted=true`, and `stop_success=true` |

Credentialed QuantConnect command delivery was accepted by the API, but no real
external LEAN callback, order, fill, or rejection result is claimed by this UAT
record. Mocks and fake fills are local regression evidence only.

The current blocker is narrower than initial setup: QuantConnect accepts both
plain and typed command requests, but the Python `on_command` receiver did not
produce debug or order evidence during the smoke windows. Phase 15-07 separated
the next external check into a no-order generic Python echo probe before any
MarketPilot order path was tested again. The echo probe also failed to produce
observable command-dispatch logs despite successful deploy and command API
acceptance.

Phase 15-08 then tested a supported Object Store signal-inbox fallback. Local
wrappers, smoke tooling, and LEAN polling are implemented and tested, and a
credentialed Paper compile/deploy succeeded. However, the QuantConnect Object
Store write itself returned `Organization not found` for the active
organization id visible in both `/account/read`, `projects/read`, and the
Organization UI URL. Because the object was not created, no algorithm receipt,
order, fill, rejection, or portfolio-change evidence is claimed.

Phase 15-09 narrowed this into a prerequisite check: the Object Store smoke now
writes the probe object before any Paper compile/deploy, and `--diagnose-only`
can test Object Store access without starting an algorithm. After the API client
stopped applying JSON `Content-Type` to multipart uploads, the credentialed
diagnose-only run returned `object_store_write_available`. The full fallback
smoke wrote the object, compiled, deployed, and cleaned up successfully, but no
receipt marker, logs, or tagged order appeared during 18 polls.

Phase 15-10 found that the local live-log wrapper used the wrong pagination
field names. After changing `/live/logs/read` to `startLine`/`endLine` with
`deploymentLogs=true`, the full fallback smoke observed deployment logs, Object
Store receipt, Object Store acceptance, and a QuantConnect paper order event
with status `Submitted`. The order was submitted while the market was closed
and QuantConnect converted it for next market open; `/live/orders/read` did not
return a tagged order during the smoke window, so fill/rejection authority is
still pending.

Phase 15-11 added default auto-stop for temporary Paper deployments created by
the Object Store smoke. Leaving a deployment active for next-open observation
now requires the explicit `--keep-running` flag and operator approval. A short
credentialed smoke verified `stop_success=true`.

Phase 15-12 ran during US market hours. The first run exposed a false-positive
hazard: `/live/orders/read` returned a stale MarketPilot-tagged order from a
prior deployment, so the smoke now requires an exact current-run order tag. A
second run exposed an early price-data gap; `lean/main.py` now defers accepted
Object Store signals until the symbol has a tradeable price instead of marking
the Object Store key processed. The final credentialed run compiled and deployed
`L-3eccd7fbf41cc4b0aa944d500f760a90`, observed Object Store receipt and
acceptance, and live logs showed `Submitted` and `Filled` for SPY quantity 1 at
fill price `$751.31`. `/live/orders/read` still returned no order with the
current expected tag, so the authority gate remains open. The temporary
deployment was stopped successfully.

Phase 15-13 closed the remaining `/live/orders/read` authority gate by waiting
long enough for QuantConnect's delayed live-order snapshot and reading
`start=0,end=1000`. The credentialed Paper-only run wrote Object Store key
`32900381/marketpilot/signals/object-store-smoke-20260617143733.json`,
compiled `be2643e583a354020fbc7a08e1a136fc-e62f04e374002b91ed7c97cf9ee17189`
to `BuildSuccess`, deployed `L-d62998269941f7f00ba48804a092c2b7`, observed
Object Store receipt and acceptance, and `/live/orders/read` returned order id
`1` with exact tag
`mp:qc-object-store-sig-20260617143733:qc-object-store-order-20260617143733`,
status `3`, Submitted and Filled order events, fill quantity `1`, and fill
price `$750.08`. Object cleanup and deployment stop both succeeded.

## Human Verification Gate

Closed for Phase 15 simulated Paper Trading order flow on 2026-06-17. The
remaining v1.1 work is not Phase 15 order authority; it is deployed product
go-live evidence and multi-session burn-in in later phases.
