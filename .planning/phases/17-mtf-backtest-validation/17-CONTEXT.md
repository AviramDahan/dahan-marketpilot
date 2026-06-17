# Phase 17: MTF Backtest Validation - Context

**Gathered:** 2026-06-17T15:41:49+03:00
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 17 delivers comparative QuantConnect Cloud Backtest validation for the
three supported strategy modes:

- `daily_only`
- `daily_filter_4h_setup`
- `daily_filter_4h_setup_1h_optional`

It creates the operator, report, regression-alert, and validation-gate
contracts needed to compare modes safely. It must not bypass the still-pending
Phase 15 `/live/orders/read` authority gate, must not start Phase 16.2 burn-in,
and must not mark v1.1 complete.

</domain>

<decisions>
## Implementation Decisions

### Comparative Backtest Scope
- **D-01:** Treat `daily_only` as the benchmark mode and compare every MTF mode
  against it using identical universe, date window, fee/slippage/fill
  assumptions, risk settings, and code version metadata.
- **D-02:** Use QuantConnect Cloud Backtest API as the only source for real
  performance metrics. Local fixtures and schemas may test parsing and safety,
  but they must never contain or imply real performance claims.
- **D-03:** The default operator path should support manual runs first and a
  weekly scheduled comparison second. Weekly automation is monitor/report-only
  and cannot change strategy mode, Paper mode, Render settings, or QC
  deployments.
- **D-04:** Missing QC credentials, compile IDs, paid-tier access, or API
  failures must produce `not_run`/blocked evidence with prerequisite details
  rather than fabricated metrics.

### Report And Regression Evidence
- **D-05:** Reports must include at least Sharpe, drawdown, win rate,
  mode-vs-mode divergence, benchmark comparison, assumptions, limitations,
  artifact source, strategy mode, config hash/version, code version, project ID,
  compile/backtest IDs when real, and timestamp.
- **D-06:** Store machine-readable artifacts first, with a human-readable
  Markdown summary generated from the same data. Existing
  `marketpilot.backtest_reports` patterns should be extended instead of
  replaced.
- **D-07:** Material regression alerts are advisory and non-authoritative. They
  may emit notification-domain events or CI/workflow failures, but cannot submit
  orders, stop deployments, approve strategies, or mutate runtime safety gates.
- **D-08:** If a metric is unavailable or absent from a QuantConnect response,
  preserve raw evidence and classify the field as unavailable; do not infer or
  backfill values from unrelated metrics.

### Activation And Safety Gates
- **D-09:** Backtest validation can produce `validation_passed`, but Paper
  eligibility still requires explicit human approval into an approved Paper
  state. No automatic promotion from Phase 17 results is allowed.
- **D-10:** A mode can be recommended for review only after real QC results,
  no-look-ahead checks, chronological coverage, benchmark availability, risk
  checks, assumptions, and report completeness all pass.
- **D-11:** Preserve all v1.1 safety fences: simulated Paper only, no real-money
  brokerage path, no leverage/margin/shorts/options/futures/crypto/Forex, no
  dashboard order controls, no secret leakage, and no fake external
  verification.
- **D-12:** Phase 17 must remain independent of local-computer uptime for
  scheduled validation once deployed through GitHub Actions or another approved
  scheduler, but it must not depend on the Render worker that controls Paper
  runtime scheduling.

### the agent's Discretion
- The planner may choose the exact file/module split, naming, CLI shape, and
  CI workflow structure as long as it reuses the existing backtesting,
  validation, QC API, and notification contracts.
- The planner may set conservative default regression thresholds, but must make
  them explicit, configurable, and fail-closed.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project And Requirements
- `.planning/PROJECT.md` - Product authority, paper-only safety boundaries,
  supported strategy modes, and QuantConnect source-of-truth decisions.
- `.planning/REQUIREMENTS.md` - `MTF-01` through `MTF-05` and the v1.1
  completion gates.
- `.planning/ROADMAP.md` - Phase 17 scope, dependencies, and explicit warning
  not to bypass Phase 15, 16.1, or 16.2 operational readiness gates.

### Prior Phase Context
- `.planning/phases/04.1-multi-timeframe-signal-foundation/04.1-CONTEXT.md` -
  Strategy mode boundaries and completed-bar MTF assumptions.
- `.planning/phases/07-backtesting-and-validation/07-CONTEXT.md` - Backtesting
  authority, local harness boundaries, report coverage, and activation gates.
- `.planning/phases/13-qc-api-client-and-safety-foundation/13-CONTEXT.md` -
  QuantConnect API safety/client decisions.
- `.planning/phases/13-qc-api-client-and-safety-foundation/13-RESEARCH.md` -
  `/backtests/create` and `/backtests/read` endpoint notes.

### Existing Documentation
- `docs/backtesting.md` - Backtesting authority, no-look-ahead, and not-run
  evidence rules.
- `docs/backtest_reports.md` - Existing report contract documentation.
- `docs/validation.md` - Chronological and sensitivity validation contracts.
- `docs/activation_gates.md` - Paper eligibility and human approval rules.
- `docs/Dahan-MarketPilot-Master-Spec.md` - Product-level backtest,
  validation, report, CI, and activation expectations.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `marketpilot/qc_api.py` - Existing authenticated QC API client already
  allowlists `backtests/create`, `backtests/read`, and `backtests/list`.
- `marketpilot/backtesting.py` - Existing backtest authority enums,
  conservative assumptions, no-look-ahead checks, same-bar ambiguity handling,
  and `not_run` evidence helper.
- `marketpilot/backtest_reports.py` - Existing report dataclasses, artifact
  source safety, validation windows, report serialization, and Markdown
  renderer.
- `marketpilot/validation.py` - Existing chronological validation,
  sensitivity analysis, benchmark comparison, and activation gate evaluator.
- `marketpilot/timeframes.py` - Existing `StrategyMode` and completed-bar
  timeframe parsing used by MTF validation.
- `tests/fixtures/qc_api/backtests_read_success.json` - Existing QC backtest
  response fixture for parser and API wrapper tests.

### Established Patterns
- Real external results must be labeled `real_quantconnect`; fixtures,
  examples, schemas, and not-run records cannot contain real performance
  metrics.
- Validation and reporting artifacts are explicit data contracts with
  deterministic offline tests.
- Safety gates fail closed and preserve raw evidence instead of inventing local
  authority.
- Notification delivery is transport-neutral and advisory; delivery success or
  failure cannot control trading safety logic.

### Integration Points
- Add Phase 17 orchestration around QC compile/backtest/read wrappers without
  duplicating strategy rules.
- Extend report and validation modules to include mode comparison and
  regression classification.
- Add a GitHub Actions/manual workflow or script interface for weekly/manual
  validation, using secrets outside the repo.
- Feed activation-gate review artifacts without changing Paper mode
  automatically.

</code_context>

<specifics>
## Specific Ideas

- Recommended default path: manual comparative validation first, scheduled
  weekly run second.
- Recommended authority model: QuantConnect Cloud Backtest results are real;
  local tests prove contracts only.
- Recommended activation posture: results can recommend human review, never
  promote Paper eligibility automatically.

</specifics>

<deferred>
## Deferred Ideas

- Backtest-vs-live equity overlay divergence remains deferred until enough real
  Paper Trading history exists.
- Phase 16.2 multi-session burn-in remains separate and must not be replaced by
  Phase 17 backtest evidence.
- v1.2 strategy expansion, new setup types, and new asset classes remain out of
  scope.

</deferred>

---

*Phase: 17-MTF Backtest Validation*
*Context gathered: 2026-06-17T15:41:49+03:00*
