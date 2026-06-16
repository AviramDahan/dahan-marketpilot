# Phase 15 Plan Quality Validation

**Phase:** 15 - Paper Trading & Order Flow  
**Goal:** Pipeline signals are delivered to a running QC paper algorithm and fill results are tracked with full audit traceability.  
**Plans checked:** 15-01-PLAN.md through 15-05-PLAN.md  
**Verdict:** BLOCK  
**Validated at:** 2026-06-16

## Executive Verdict

The five plans are structurally well-formed and mostly cover the intended local implementation path: QuantConnect API wrappers, command payload construction, pre-submit safety gates, LEAN `on_command` order placement, live-order polling, audit records, and offline E2E tests.

However, execution should not proceed as-is because two blocking quality issues remain:

1. `15-RESEARCH.md` still contains unresolved open questions, including the live-orders payload shape and account-specific `/live/create` requirements. The plan set depends on these areas for PTD-01, FT-01, FT-03, and FT-04.
2. Plan 15-05 permits the credentialed QuantConnect paper smoke check to be recorded as `not_run` while still treating the human checkpoint as acceptable. That is honest reporting, but it does not verify the phase goal that signals are delivered to a running QC paper algorithm.

## Coverage Summary

| Requirement | Plans | Verdict | Evidence |
|---|---:|---|---|
| PTD-01 | 15-01, 15-02, 15-05 | FLAG | Deployment wrapper and deploy idempotency are planned, but `/live/create` account-specific fields remain an unresolved research question. |
| PTD-02 | 15-01, 15-02, 15-03, 15-05 | FLAG | Commands API wrapper, local command sender, and LEAN receiver are planned; external running-algorithm verification can still be `not_run`. |
| PTD-03 | 15-01, 15-05 | PASS | Stop/liquidate wrappers remain paper-gated and covered by tests/docs. |
| PTD-04 | 15-02, 15-05 | PASS | Duplicate deploy keys are rejected before API calls; offline E2E covers duplicate path. |
| PTD-05 | 15-03, 15-05 | PASS | LEAN `on_command` validates MarketPilot payloads and places tagged `market_order` only on accepted commands. |
| FT-01 | 15-01, 15-04, 15-05 | FLAG | `/live/orders/read` wrapper and polling are planned, but exact response shape remains unresolved. |
| FT-02 | 15-04, 15-05 | PASS | Audit append of QC-derived order/fill evidence is planned with `source_authority=quantconnect` and `local_authority=false`. |
| FT-03 | 15-04, 15-05 | FLAG | Partial fill/rejection handling is planned, but rejection/tag field locations depend on unresolved real payload shape. |
| FT-04 | 15-04, 15-05 | PASS | Signal/order/fill trace query is planned through idempotency key, signal id, QC order id, tag, and audit records. |
| SAFE-05 | 15-02, 15-03, 15-05 | PASS | Stale-window checks are planned before Commands API delivery and again inside LEAN. |

## Plan Structure

| Plan | Wave | Depends On | Tasks | Structure | Scope |
|---|---:|---|---:|---|---|
| 15-01 | 1 | none | 2 | PASS | PASS |
| 15-02 | 2 | 15-01 | 2 | PASS | PASS |
| 15-03 | 3 | 15-02 | 2 | PASS | PASS |
| 15-04 | 3 | 15-02 | 2 | PASS | PASS |
| 15-05 | 4 | 15-03, 15-04 | 3 | PASS | PASS |

`gsd-tools query verify.plan-structure` returned `valid: true` for all five plans. The dependency graph is acyclic and wave assignments are coherent: API boundary first, local sender second, LEAN receiver and fill polling in parallel after sender contracts, final E2E/docs/UAT last.

## Key Links

| Link | Verdict | Evidence |
|---|---|---|
| `paper_order_flow.py` -> `QCApiClient.create_live_command` | PASS | Plan 15-02 explicitly calls `QCApiClient.create_live_command()` after sync, stale, and duplicate gates. |
| `lean/main.py` -> `lean_command_receiver.py` | PASS | Plan 15-03 wires `on_command` through pure normalization/validation helpers. |
| LEAN accepted command -> tagged paper order | PASS | Plan 15-03 requires exactly one `self.market_order(symbol, quantity, tag=tag)` for accepted commands. |
| QC live orders -> audit JSONL | PASS | Plan 15-04 requires `poll_quantconnect_order_updates()` to call the QC live-orders wrapper and append authoritative audit records. |
| Audit JSONL -> trace query | PASS | Plan 15-04 requires `read_signal_order_fill_trace()` to reconstruct chain without becoming authoritative state. |
| External running QC paper algorithm -> phase verification | BLOCK | Plan 15-05 allows external smoke evidence to be `not_run`; that preserves honesty but does not verify the phase goal. |

## Verification Commands

The planned automated commands are mostly sufficient for deterministic offline behavior:

- `pytest tests/test_qc_api.py -q`
- `pytest tests/test_paper_order_flow.py -q`
- `pytest tests/test_lean_command_flow.py tests/test_lean_static_safety.py tests/test_lean_runtime_bridge_static.py -q`
- `pytest tests/test_paper_order_flow_e2e.py tests/test_paper_order_flow.py tests/test_lean_command_flow.py tests/test_qc_api.py tests/test_sync.py -q`
- `pytest -q` if the local Python version satisfies project requirements

These commands do not and should not require QuantConnect credentials. The gap is not offline testing; the gap is that final phase verification can still pass with no credentialed running-paper check.

## Dimension Results

| Dimension | Verdict | Notes |
|---|---|---|
| Requirement Coverage | FLAG | All required IDs appear in plan frontmatter, but PTD-01, PTD-02, FT-01, and FT-03 depend on unresolved external payload/setup questions. |
| Task Completeness | PASS | All tasks have files, action, verify, and done fields. |
| Dependency Correctness | PASS | No missing references or cycles found. |
| Key Links Planned | FLAG | Internal wiring is planned; external running-algorithm verification link is not mandatory before acceptance. |
| Scope Sanity | PASS | Plans have 2, 2, 2, 2, and 3 tasks respectively. |
| Verification Derivation | BLOCK | User-observable phase goal includes running QC delivery; final plan allows `not_run` external smoke to satisfy the checkpoint. |
| Context Compliance | PASS | Plans honor D-01 through D-12 and do not implement deferred ideas. |
| Scope Reduction Detection | PASS | No plan reduces a locked decision to static/stub/future work. |
| Architectural Tier Compliance | PASS | REST calls stay in `QCApiClient`; local sender gates; order placement stays in LEAN. |
| Nyquist Compliance | PASS | Each implementation task has an automated pytest command; no watch-mode or full E2E-only sampling issue found. |
| Cross-Plan Data Contracts | PASS | Command payload, tag, idempotency key, and audit fields are carried through the planned pipeline. |
| AGENTS.md Compliance | PASS | Plans preserve paper-only, no secrets, offline tests, no new packages, and QuantConnect authority. |
| Research Resolution | BLOCK | `15-RESEARCH.md` has `## Open Questions` without `(RESOLVED)` and lists unresolved questions. |
| Pattern Compliance | PASS | Plans follow `15-PATTERNS.md` boundary rules; no analog file-classification table is present to enforce per-file analog references. |

## Blockers

```yaml
issues:
  - plan: null
    dimension: research_resolution
    severity: BLOCKER
    description: "15-RESEARCH.md has unresolved open questions for live-orders response shape, account-specific live-create requirements, and order-event evidence recovery."
    evidence:
      - "15-RESEARCH.md section: ## Open Questions"
      - "Questions affect PTD-01, FT-01, FT-03, and FT-04."
    fix_hint: "Resolve the open questions or mark the section as '## Open Questions (RESOLVED)' with explicit resolutions. If real QC credentials are required, convert unresolved payload/setup unknowns into a mandatory manual verification gate that cannot be accepted as phase-complete when not_run."
  - plan: "15-05"
    task: 3
    dimension: verification_derivation
    severity: BLOCKER
    description: "The human credentialed QuantConnect paper smoke checkpoint allows 'not_run' to be accepted, so the plans may complete without verifying delivery to a running QC paper algorithm."
    evidence:
      - "Plan 15-05 Task 3 says to record the external smoke check as not_run when credentials are not configured."
      - "Task done condition allows approval when external check is not_run."
    fix_hint: "Change final acceptance so external delivery to a running QC paper algorithm is either actually evidenced, or explicitly mark PTD-02/running-QC delivery as not verified and do not treat the phase goal as complete. Alternative: split external QC smoke verification into a separate gated phase and narrow Phase 15's goal to offline-capable implementation."
```

## Warnings

```yaml
issues:
  - plan: "15-02"
    task: 2
    dimension: task_completeness
    severity: WARNING
    description: "Pre-submit Phase 14 sync freshness is required, but the plan does not name the exact freshness threshold or fields used to decide 'stale sync record'."
    evidence:
      - "D-09 requires a stale sync record to block signal delivery."
      - "Plan 15-02 says to enforce Phase 14 freshness but does not specify TTL/max age."
    fix_hint: "Add the exact sync freshness rule, such as which timestamp field is checked and what max age makes the record stale, or reference the Phase 14 constant/function that owns the decision."
```

## Required Changes Before Execution

1. Resolve or explicitly gate the `15-RESEARCH.md` open questions. Do not leave the current `## Open Questions` section unresolved.
2. Revise Plan 15-05 so `not_run` external QC smoke evidence cannot be treated as proof that the phase goal is achieved. If credentials are unavailable, verification must honestly say external running-QC delivery is not verified.
3. Add an explicit Phase 14 sync freshness threshold to Plan 15-02 to prevent executor-defined stale-window behavior.

## Recommendation

Return these plans to the planner for revision. The local/offline architecture is sound enough to keep, but the current plan set should not be executed as a phase-complete path until the research and external-verification blockers are closed.
