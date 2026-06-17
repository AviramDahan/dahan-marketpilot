# Phase 15 Verification: Paper Trading Order Flow

SIMULATED PAPER TRADING ONLY - NOT FINANCIAL ADVICE.

## Verification Summary

Phase 15 local implementation is covered by deterministic offline tests. Real
QuantConnect read-only paper connectivity, cloud file sync, cloud compile, live
paper deployment creation, Commands API acceptance, and the disabled-by-default
command-smoke runner are verified. Real command callback-to-order delivery
remains `blocked_external_callback_not_verified` because accepted plain and
typed commands produced no observable `on_command` debug log and no live order
during polling. Phase 15-07 added an isolated no-order dispatch probe and
aligned the MarketPilot smoke payload with the official generic `on_command`
contract. The credentialed external probe compiled and deployed successfully,
but still observed no generic command dispatch marker in live logs. Phase 15-08
implemented a supported Object Store signal-inbox fallback. Phase 15-09 added a
fail-fast Object Store preflight and then fixed the API client to avoid sending
a JSON `Content-Type` on multipart uploads. Object Store writes now pass
externally. Phase 15-10 corrected `/live/logs/read` pagination to the official
`startLine`/`endLine` request shape. The deployed algorithm then produced Object
Store receipt and acceptance logs, plus a QuantConnect paper order event with
status `Submitted`. `/live/orders/read` still returned 0 orders during the
polling window, so order/fill/rejection authority remained unverified. Phase
15-12 then tightened the smoke to ignore stale MarketPilot orders from older
deployments and defer Object Store signals until the target symbol has a
tradeable price. A credentialed market-hours rerun observed live-log
`Submitted` and `Filled` events, but `/live/orders/read` still did not return
the current expected order tag. Phase 15-13 expanded the order polling range and
waited through the delayed QuantConnect live-order snapshot. `/live/orders/read`
then returned the exact current expected tag with submitted and filled order
events, closing the Phase 15 order-authority gate for simulated Paper Trading.

Offline tests do not prove real QuantConnect execution. Mocked command delivery,
mocked live orders, fake LEAN objects, and fake fills are not external evidence.

## Automated Commands

| Command | Status | Evidence Class |
|---------|--------|----------------|
| `pytest tests/test_paper_order_flow_e2e.py tests/test_paper_order_flow.py tests/test_lean_command_flow.py tests/test_qc_api.py -q` | passed | offline deterministic |
| `pytest tests/test_paper_order_flow_e2e.py tests/test_paper_order_flow.py tests/test_lean_command_flow.py tests/test_qc_api.py tests/test_sync.py -q` | passed | offline deterministic |
| `pytest -q` | passed_with_version_caveat | offline deterministic full local suite under Python 3.10.10; project metadata requires Python >=3.11 for strict/release verification |
| Authenticated QuantConnect `/live/list`, `/live/read`, `/live/orders/read` smoke | passed_external_read_only | project `32900381`, deploy `L-223eafd89aaac127343bb441bf96e423`, status `running`, equity `27027.03`, orders read success with 0 orders |
| QuantConnect cloud file sync, compile, live create, command API smoke | partial_external_command_api_only | synced `main.py` plus 28 `marketpilot/` files; compile `76fe4ebdce72ca35574db67ad60b0433-9fbcc5e87d8c7d73346eda85b8851386` was `BuildSuccess`; deploy `L-6e97706430e5dfec3e6615282153ad47` was `Running`; `/live/commands/create` returned `success=true`; logs/orders stayed empty |
| Phase 15-06 gap smoke command | blocked_external_callback_not_verified | synced callback-tolerant receiver, compile `54a09ada5318ca08dfd15e3ac7ec12ad-b1d7a4c2bb865f244914254e68bd0b07` was `BuildSuccess`; deploy `L-bd51091b63e10262fac1b2ca8b877f49` was `Running`; `typed_order_command_probe` returned `command_api_success=true`; 12 polls showed 0 logs and 0 orders |
| Phase 15-07 no-order dispatch probe | blocked_external_dispatch_not_observed | `qc_command_dispatch_probe.py` refuses by default, dry-run redacts secrets, produces a no-order Python echo algorithm, and builds official generic command payloads. External compile `677437f56a306fab73f489b921f92652-dbdb35fb652acd584047b1e67f1a13b0` was `BuildSuccess`; deploy `L-2c24272bebaead4a441fadf048662324` was `Running`; command API returned success; 12 immediate polls plus 18 delayed polls showed 0 logs and no marker. |
| Phase 15-08 Object Store fallback smoke | blocked_external_object_store_write_not_verified | `qc_object_store_signal_smoke.py` refuses by default, dry-run redacts secrets, writes only namespaced `marketpilot/signals/*.json` probe objects, and deploys an injected-key Paper algorithm when requested. External compile `cc45d0b42ae58f274bd3b813432bcbcf-845d50c9f70c2df38cedff8fdf2e5eba` was `BuildSuccess`; deploy `L-1d49f38582cfbf61646aa479f54fbaa7` was `Running`; `/object/set` returned `Organization not found`; 18 polls showed 0 logs and 0 orders; the temporary deploy was stopped. |
| Phase 15-09 Object Store diagnose-only smoke | passed_external_object_store_write | `qc_object_store_signal_smoke.py --diagnose-only` performs `/object/set` before any compile/deploy. After removing the session-level JSON content type from multipart uploads, credentialed diagnose-only used project `32900381`, organization `ed947707222a7b9aeb5de9d0974e5994`, and key `32900381/marketpilot/signals/object-store-smoke-20260616221505.json`; `/object/set` returned `success=true`, `/object/properties` returned JSON metadata, cleanup succeeded, and no compile/deploy/order polling was performed. |
| Phase 15-09 full Object Store fallback smoke | object_store_written_no_algorithm_receipt_observed | Full fallback smoke wrote key `32900381/marketpilot/signals/object-store-smoke-20260616221527.json`, compiled `462cdc22a9803673f0b85cbe82d09db0-4e5dd314ca2c676616079f237105ca84` to `BuildSuccess`, deployed Paper algorithm `L-35940c556bcc768d5ca186f28d868441`, restored `main.py`, cleaned up the object, and stopped the temporary deployment. Eighteen polls observed 0 live logs, 0 tagged orders, and no receipt marker. |
| Phase 15-10 corrected live-log Object Store fallback smoke | object_store_delivery_receipt_or_rejection_observed | Corrected `/live/logs/read` to send `format`, `startLine`, `endLine`, and `deploymentLogs`. Full fallback smoke wrote key `32900381/marketpilot/signals/object-store-smoke-20260616222641.json`, compiled `17cf8c855b9f015b657bb8ee93dde36f-fc7dc35aac534131b7f46de7f1f4338f` to `BuildSuccess`, deployed Paper algorithm `L-103091222fcd6eee4aae06e1de635e38`, observed `MarketPilot Object Store signal received.` and `MarketPilot object_store accepted: SPY 1` in live logs, observed a QuantConnect `New Order Event` with status `Submitted`, cleaned up the object, and stopped the deployment. `/live/orders/read` returned 0 orders during the smoke window. |
| Phase 15-11 short auto-stop smoke | passed_external_auto_stop | Object Store fallback smokes now stop temporary Paper deployments by default and require `--keep-running` for explicit next-open observation. A short credentialed smoke wrote key `32900381/marketpilot/signals/object-store-smoke-20260616223659.json`, compiled `afa175c1bfd2ec3fbe9761e785d36564-3a1e17366ee80c002632e087f0b2adc5` to `BuildSuccess`, deployed `L-d54a7a1b3ffb938b43db9cab1a0f2560`, cleaned up the object, and returned `stop_success=true`. |
| Phase 15-12 exact-tag market-hours smoke | live_logs_filled_but_orders_read_current_tag_missing | Fixed the smoke to require the current expected order tag and fixed LEAN Object Store handling to defer valid signals until the symbol has tradeable price data. Credentialed market-hours smoke wrote key `32900381/marketpilot/signals/object-store-smoke-20260617135051.json`, compiled `dc91c5ab5e0058488a8d1d9f2df34e67-b2ee161c2a598a4ba7551a28468e76ff` to `BuildSuccess`, deployed `L-3eccd7fbf41cc4b0aa944d500f760a90`, observed receipt and acceptance logs, and observed QuantConnect live-log `Submitted` and `Filled` events for SPY quantity 1 at fill price `$751.31`. `/live/orders/read` returned only an older tagged order from `L-103091222fcd6eee4aae06e1de635e38`, not the current expected tag. Object cleanup and deployment stop succeeded. |
| Phase 15-13 snapshot-wait order authority smoke | passed_external_order_authority | Expanded `/live/orders/read` polling to `start=0,end=1000` and waited through the QuantConnect live-order snapshot delay. Credentialed Paper-only smoke wrote key `32900381/marketpilot/signals/object-store-smoke-20260617143733.json`, compiled `be2643e583a354020fbc7a08e1a136fc-e62f04e374002b91ed7c97cf9ee17189` to `BuildSuccess`, deployed `L-d62998269941f7f00ba48804a092c2b7`, observed Object Store receipt and acceptance, and `/live/orders/read` returned order id `1` with exact tag `mp:qc-object-store-sig-20260617143733:qc-object-store-order-20260617143733`, status `3`, Submitted and Filled events, fill quantity `1`, and fill price `$750.08`. Object cleanup and deployment stop succeeded. |

## Requirement Evidence Matrix

| Requirement | Offline Evidence | External QuantConnect Evidence | Status |
|-------------|------------------|--------------------------------|--------|
| PTD-01 | `deploy_paper_algorithm()` tests cover live-paper payload and deployment idempotency. | `/live/create` created Paper deployment `L-6e97706430e5dfec3e6615282153ad47` from successful compile. | passed_external |
| PTD-02 | E2E test covers `submit_signal_command()` to mocked `create_live_command()` and fake LEAN `on_command`; Phase 15-08 adds fake LEAN Object Store payload polling through the same validation path. | `/live/commands/create` returned `success=true` for plain, typed, and no-order generic echo probes, but no `on_command` debug/order/marker evidence appeared. Object Store fallback now writes externally and the deployed Paper algorithm logged receipt and acceptance. | passed_external_via_object_store_fallback |
| PTD-03 | `tests/test_qc_api.py` covers paper-gated stop/liquidate wrapper behavior. | not required for 15-05 smoke, no external stop/liquidate run. | passed_offline_only |
| PTD-04 | Unit and E2E tests reject duplicate deploy/signal idempotency keys before API calls. | not run externally. | passed_offline_only |
| PTD-05 | `tests/test_lean_command_flow.py` and E2E tests prove fake LEAN command and Object Store payload acceptance create one tagged paper order path; `lean/main.py` records sanitized command/Object Store receipt evidence before parsing. Phase 15-12 adds price-data deferral before processing Object Store keys. | Phase 15 receiver code compiled and deployed. Object Store receipt and acceptance were observed in live logs, and `/live/orders/read` returned the current tagged Paper order with submitted and filled events. | passed_external_order_authority |
| FT-01 | `poll_quantconnect_order_updates()` tests poll fake `read_live_orders()` and map tags to signal ids. Phase 15-12 smoke now filters exact current tags and ignores stale MarketPilot orders. | `/live/orders/read` returned exact current tag `mp:qc-object-store-sig-20260617143733:qc-object-store-order-20260617143733` for deployment `L-d62998269941f7f00ba48804a092c2b7`. | passed_external_order_authority |
| FT-02 | Audit JSONL tests prove QC-derived fill records append with `source_authority=quantconnect` and `local_authority=false`. | `/live/orders/read` returned a Filled event with fill quantity `1` and fill price `$750.08`; QuantConnect remains the source authority for the fill. | passed_external_order_authority |
| FT-03 | Offline tests cover partial fills and rejected orders with reasons from mocked QC payloads. | `/live/orders/read` returned real submitted and filled order events. Rejection parsing remains covered offline. | passed_external_filled_path |
| FT-04 | Trace query tests reconstruct command/order/fill and rejection chains by signal id or idempotency key. | The current signal id and idempotency key were recovered from the exact QuantConnect order tag returned by `/live/orders/read`. | passed_external_order_authority |
| SAFE-05 | Unit and E2E tests prove stale signals are skipped locally and rejected inside fake LEAN before order placement. Object Store stale payloads also reject through shared validation. | The external fresh Object Store payload passed shared validation; stale and duplicate rejection paths remain covered offline. | passed_offline_and_external_fresh_path |

## External Smoke Gate

Status: `passed_external_order_authority`

Authenticated QuantConnect smoke on 2026-06-16T12:46:23Z:

- `/live/list`: passed; Paper deployment is visible as `Running`.
- `/live/read`: passed; parsed snapshot reports deployment `running`,
  algorithm `running`, equity `27027.03`, 0 holdings, 0 orders, and 0 fills.
- `/live/orders/read`: passed; response `success=true`, 0 orders.

Follow-up smoke synced Phase 15 code to QuantConnect, compiled it, created a
new Paper deployment, and sent a `marketpilot_signal` command through
`/live/commands/create`. The API returned `success=true`, but repeated
`/live/logs/read` and `/live/orders/read` polling showed no `on_command` debug
log and 0 orders.

Phase 15-06 then added a disabled-by-default smoke helper and tolerant command
normalization for PascalCase attributes, nested `marketpilot_signal`, and typed
`parameters` envelopes. The synced code compiled and deployed to Paper, and a
`typed_order_command_probe` command returned `command_api_success=true`. Twelve
polls over about one minute still showed 0 live logs and 0 live orders. PTD-02,
PTD-05, FT-03, FT-04, and the running command-to-order phase goal must not be
marked externally verified until the callback/order gap is resolved.

Phase 15-07 added `scripts/qc_command_dispatch_probe.py` to compile and deploy
a no-order Python echo algorithm for generic Commands API dispatch diagnosis.
The probe is disabled by default behind `MARKETPILOT_QC_DISPATCH_PROBE_ENABLED=1`,
redacts secret-bearing output, restores the target project file by default, and
looks only for a sanitized log marker. Local dry-run passed. Credentialed
external dispatch ran against project `32900381`: the echo compile succeeded,
the Paper deploy reached `Running`, and `/live/commands/create` returned
success, but repeated `/live/logs/read` polls returned 0 logs and no marker.

Phase 15-08 added `scripts/qc_object_store_signal_smoke.py` and Object Store
API wrappers to test a supported fallback delivery path. The local smoke is
disabled by default behind `MARKETPILOT_QC_OBJECT_STORE_SMOKE_ENABLED=1`,
redacts secret-bearing output, and writes/deletes only under the MarketPilot
signal namespace. Credentialed external fallback diagnostics compiled and
deployed the injected-key Paper algorithm, but `/object/set` returned
`Organization not found` for the active organization id. Since no object was
created, the live algorithm had no signal to receive; repeated logs/orders
polling showed 0 logs and 0 orders.

Phase 15-09 made Object Store write availability a preflight. The smoke now
stops before compile/deploy when `/object/set` is unavailable, and
`--diagnose-only` verifies the prerequisite without touching live algorithms.
After fixing multipart uploads to avoid the inherited JSON content type,
credentialed diagnose-only returned `object_store_write_available`. The full
fallback smoke then wrote the signal object, compiled, deployed, restored the
project file, cleaned up the object, and stopped the temporary deployment, but
18 polls still showed 0 live logs, 0 tagged orders, and no receipt marker.

Phase 15-10 corrected the live-log API payload from `start`/`end` to
`startLine`/`endLine` with `deploymentLogs=true`. The rerun then observed
deployment logs, the Object Store receipt marker, acceptance marker, and a
QuantConnect paper order event with status `Submitted`. `/live/orders/read`
still returned 0 orders during the polling window, likely because the order was
submitted while the market was closed and was converted to fill at next market
open.

Phase 15-11 added auto-stop safety to the Object Store smoke. Temporary Paper
deployments are stopped by default after polling; next-open observation requires
the explicit `--keep-running` flag. A short credentialed smoke verified external
`stop_success=true`.

Phase 15-12 ran the market-hours order-authority follow-up. The first
credentialed run showed that `/live/orders/read` can return stale
MarketPilot-tagged orders from older deployments, so the smoke now filters only
the exact expected tag for the current signal. A second run showed that
Object Store polling can happen before SPY has a tradeable price, so
`lean/main.py` now leaves valid Object Store signals unprocessed until price
data exists. The final run observed current deployment receipt, acceptance,
`Submitted`, and `Filled` in live logs, but `/live/orders/read` still returned
only the older tagged order from deployment `L-103091222fcd6eee4aae06e1de635e38`.
The current deployment `L-3eccd7fbf41cc4b0aa944d500f760a90` was stopped after
the evidence capture.

Phase 15-13 completed the order-authority gate. The smoke now records top-level
`qc_order_evidence_*` fields so exact order evidence is not hidden by generic
redaction or truncated observations. A retry after the QuantConnect deploy
processing window returned `object_store_delivery_order_observed`; order id `1`
for deployment `L-d62998269941f7f00ba48804a092c2b7` matched the current
expected tag and included submitted and filled events with fill quantity `1`
and fill price `$750.08`. Cleanup and stop both succeeded.

## Secret Handling

No secret values are stored or committed. Documentation lists environment
variable names only.

## Residual Risk

Account-specific `/live/create`, `/live/read`, `/live/orders/read`, compile,
file sync, command API acceptance, Object Store fallback code paths, algorithm
receipt, and current-tag order/fill authority are now externally verified for
simulated Paper Trading. The remaining v1.1 risk is not Phase 15 order
authority; it is deployed product go-live evidence, local-computer
independence, and multi-session burn-in covered by Phase 16.1 and Phase 16.2.
