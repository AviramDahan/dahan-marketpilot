# Phase 2: QuantConnect Foundation and Universe - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md - this log preserves the alternatives considered.

**Date:** 2026-06-13
**Phase:** 02-quantconnect-foundation-and-universe
**Areas discussed:** LEAN validation, universe scope, regime boundary, universe data, SymbolData, indicators, tests and verification, documentation, QuantConnect Cloud API

---

## LEAN Validation

| Option | Description | Selected |
|--------|-------------|----------|
| Documented gate | First Phase 2 plan verifies official QuantConnect/LEAN docs and compile path; later code waits for that verification. | yes |
| Static-first | Keep using mostly local/static tests; real LEAN compile is deferred until setup exists. | |
| You choose | Codex chooses the safest option for the project. | |

**User's choice:** A - Documented gate.
**Notes:** User answered `A,A,A` for the first question group.

---

## Universe Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Full foundation | Build universe and data-quality contracts now; no strategy signals or scoring yet. | yes |
| Minimal slice | Build only a small dynamic-universe proof and defer most universe/data-quality details. | |
| You choose | Codex chooses the right scope boundary. | |

**User's choice:** A - Full foundation.
**Notes:** Phase 2 should build the full foundation but stay below strategy/scoring scope.

---

## Regime Boundary

| Option | Description | Selected |
|--------|-------------|----------|
| Gate only | RISK_ON / NEUTRAL / RISK_OFF can gate future new entries; no liquidation behavior or exit override. | yes |
| Advisory only | Calculate regime for display/tests only; strategies decide later whether to use it. | |
| You choose | Codex chooses the behavior most consistent with requirements. | |

**User's choice:** A - Gate only.
**Notes:** Regime can become an entry gate later, but must not liquidate or override exits.

---

## Universe Data

| Option | Description | Selected |
|--------|-------------|----------|
| Strict requirements | Required universe criteria reject symbols when missing or invalid. | yes |
| Graded requirements | Some criteria produce warnings first and only some reject. | |
| You choose | Codex chooses the appropriate strictness. | |

**User's choice:** A - Strict requirements.
**Notes:** User answered `A,A,A` for the second question group.

---

## SymbolData

| Option | Description | Selected |
|--------|-------------|----------|
| Readiness-first | SymbolData owns indicators, data quality, readiness, and cleanup. | yes |
| Lightweight cache | SymbolData is only a thin wrapper around symbol/history in Phase 2. | |
| You choose | Codex chooses the responsibility boundary. | |

**User's choice:** A - Readiness-first.
**Notes:** Indicator readiness should be explicit before any future signal logic can use it.

---

## Indicators

| Option | Description | Selected |
|--------|-------------|----------|
| Full foundation set | Build EMA/RSI/MACD/ROC/ATR/volume/relative-strength foundations and tests, without classifications. | yes |
| Regime indicators only | Build mainly SPY/QQQ EMA regime now; defer setup indicators. | |
| You choose | Codex chooses indicator depth. | |

**User's choice:** A - Full foundation set.
**Notes:** Full indicator foundation is in Phase 2 scope, but BUY/WATCH/AVOID and setup decisions are not.

---

## Tests And Verification

| Option | Description | Selected |
|--------|-------------|----------|
| Offline-first + optional LEAN | Most tests are deterministic/offline; LEAN compile/cloud checks are external gates when setup exists. | yes |
| LEAN-required | Phase 2 cannot be complete without a real LEAN compile. | |
| You choose | Codex chooses the verification policy. | |

**User's choice:** A - Offline-first + optional LEAN.
**Notes:** User answered `A,A,A` for the third question group.

---

## Files And Documentation

| Option | Description | Selected |
|--------|-------------|----------|
| Docs synchronized | Every new contract is documented: universe, data quality, indicators, regime, LEAN setup, and deferred boundaries. | yes |
| Code/tests first | Documentation updates minimally after code works. | |
| You choose | Codex chooses documentation level. | |

**User's choice:** A - Docs synchronized.
**Notes:** This continues the Phase 1 documentation synchronization contract.

---

## QuantConnect Cloud API

| Option | Description | Selected |
|--------|-------------|----------|
| Verify only now | Phase 2 verifies and documents APIs/workflows, but requires no credentials and runs no cloud backtest or Paper deployment. | yes |
| Prepare credential hooks | Add placeholders/config hooks for Cloud API without secrets. | |
| You choose | Codex chooses the safe boundary. | |

**User's choice:** A - Verify only now.
**Notes:** No credentials, cloud backtest, or Paper deployment in Phase 2.

---

## the agent's Discretion

None. The user selected the recommended option for all discussed areas.

## Deferred Ideas

- Cloud backtest execution.
- Paper Trading deployment and Live Node setup.
- Telegram regime alerts.
- Render dashboard data integration.
- Strategy signals, scoring, classifications, portfolio sizing, orders, fills, stops, targets, and exits.

## UX Note

The user requested future text-mode Hebrew choice prompts use code blocks with `[A]`, `[B]`, `[C]` labels. Numbered or mixed RTL/LTR option lists were visually unstable.
