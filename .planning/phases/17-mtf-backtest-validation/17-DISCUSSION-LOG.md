# Phase 17: MTF Backtest Validation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md - this log preserves the alternatives considered.

**Date:** 2026-06-17T15:41:49+03:00
**Phase:** 17-MTF Backtest Validation
**Areas discussed:** Comparative Backtest Scope, Report And Regression Evidence, Activation And Safety Gates

---

## Comparative Backtest Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Agent recommended | Compare all supported strategy modes against `daily_only` using identical assumptions and QC Cloud Backtest as authority. | yes |
| Narrow manual only | Build only ad hoc manual comparisons without scheduled validation. | |
| Broad automation | Let scheduled validation change strategy/Paper mode automatically. | |

**User's choice:** User authorized the agent to choose the recommended answers.
**Notes:** Selected the conservative authority-preserving path. Weekly automation is allowed only as monitor/report flow and cannot mutate Paper runtime behavior.

---

## Report And Regression Evidence

| Option | Description | Selected |
|--------|-------------|----------|
| Agent recommended | Machine-readable artifacts first, generated Markdown summary, explicit metric availability, no inferred values. | yes |
| Human report only | Produce only Markdown summaries, delaying stable data contracts. | |
| Aggressive normalization | Infer missing metrics from related values to reduce unavailable fields. | |

**User's choice:** User authorized the agent to choose the recommended answers.
**Notes:** Selected machine-readable evidence with explicit unavailable states. Real metrics require real QuantConnect artifacts.

---

## Activation And Safety Gates

| Option | Description | Selected |
|--------|-------------|----------|
| Agent recommended | Validation may recommend review, but explicit human approval is required before any Paper-eligible state. | yes |
| Automatic promotion | Promote the winning mode automatically after passing metrics. | |
| Report-only forever | Never connect validation output to activation review artifacts. | |

**User's choice:** User authorized the agent to choose the recommended answers.
**Notes:** Selected human-gated activation. Phase 17 must not bypass Phase 15 order authority, Phase 16.1 go-live evidence, or Phase 16.2 burn-in.

---

## the agent's Discretion

- The agent selected recommended answers because the user explicitly approved autonomous recommended choices.
- Planner may decide exact module and CI layout while preserving the locked safety and authority decisions.

## Deferred Ideas

- Backtest-vs-live equity overlay after sufficient Paper history.
- v1.2 strategy expansion or new asset classes.
