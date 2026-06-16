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
but still observed no generic command dispatch marker in live logs.

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

## Requirement Evidence Matrix

| Requirement | Offline Evidence | External QuantConnect Evidence | Status |
|-------------|------------------|--------------------------------|--------|
| PTD-01 | `deploy_paper_algorithm()` tests cover live-paper payload and deployment idempotency. | `/live/create` created Paper deployment `L-6e97706430e5dfec3e6615282153ad47` from successful compile. | passed_external |
| PTD-02 | E2E test covers `submit_signal_command()` to mocked `create_live_command()` and fake LEAN `on_command`; Phase 15-07 adds a no-order generic dispatch probe. | `/live/commands/create` returned `success=true` for plain, typed, and no-order generic echo probes, but no `on_command` debug/order/marker evidence appeared. | blocked_external_dispatch_not_observed |
| PTD-03 | `tests/test_qc_api.py` covers paper-gated stop/liquidate wrapper behavior. | not required for 15-05 smoke, no external stop/liquidate run. | passed_offline_only |
| PTD-04 | Unit and E2E tests reject duplicate deploy/signal idempotency keys before API calls. | not run externally. | passed_offline_only |
| PTD-05 | `tests/test_lean_command_flow.py` and E2E tests prove fake LEAN command acceptance creates one tagged paper order path; `lean/main.py` now records sanitized command receipt evidence before parsing. | Phase 15 receiver code compiled and deployed, including tolerant payload normalization, but callback/order behavior was not observed after command API acceptance. | blocked_external_callback_not_verified |
| FT-01 | `poll_quantconnect_order_updates()` tests poll fake `read_live_orders()` and map tags to signal ids. | `/live/orders/read` succeeded externally with 0 orders; no tagged command/order trace exists yet. | partial_external_verified_read_only |
| FT-02 | Audit JSONL tests prove QC-derived fill records append with `source_authority=quantconnect` and `local_authority=false`. | `/live/read` and `/live/orders/read` shape verified externally; no real fill evidence exists yet. | partial_external_verified_read_only |
| FT-03 | Offline tests cover partial fills and rejected orders with reasons from mocked QC payloads. | no real order/fill/rejection exists yet. | passed_offline_only_until_external_callback_smoke |
| FT-04 | Trace query tests reconstruct command/order/fill and rejection chains by signal id or idempotency key. | no real signal/order/fill trace exists yet. | passed_offline_only_until_external_callback_smoke |
| SAFE-05 | Unit and E2E tests prove stale signals are skipped locally and rejected inside fake LEAN before order placement. | not required for external proof if no command can be sent. | passed_offline |

## External Smoke Gate

Status: `partial_external_command_api_only`

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

## Secret Handling

No secret values are stored or committed. Documentation lists environment
variable names only.

## Residual Risk

Account-specific `/live/create`, `/live/read`, `/live/orders/read`, compile,
file sync, and command API acceptance are now verified. A no-order generic
Python echo algorithm also failed to produce observable command-dispatch logs.
QuantConnect Python `on_command` callback behavior or live log visibility still
requires remediation and sanitized evidence before Phase 15 can be marked fully
passed.
