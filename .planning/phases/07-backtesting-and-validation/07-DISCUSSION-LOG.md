# Phase 7: Backtesting and Validation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution
> agents. Decisions are captured in CONTEXT.md - this log preserves the
> alternatives considered.

**Date:** 2026-06-14
**Phase:** 7-backtesting-and-validation
**Mode:** `/gsd-discuss-phase 7 --all`

---

## User Direction

The user explicitly gave the agent freedom to choose the Phase 7 answers:

```text
אני נותן לך יד חופשית לבחירת התשובות
```

The agent selected conservative, safety-first defaults for every gray area.

---

## Backtest Authority And Offline Harness

| Option | Description | Selected |
|--------|-------------|----------|
| A | QuantConnect Cloud/LEAN is official source of truth, plus deterministic local harness for no-look-ahead tests. | yes |
| B | Local harness only. | |
| C | QuantConnect only, no local harness. | |
| D | You choose. | user delegated |

**Decision:** A. QuantConnect official authority plus local deterministic tests.

---

## Shared Rule Pipeline

| Option | Description | Selected |
|--------|-------------|----------|
| A | Backtest and Paper adapters reuse the same setup -> scoring -> risk -> lifecycle -> exits pipeline. | yes |
| B | Duplicate some strategy logic inside backtest. | |
| C | Defer shared-rule enforcement to Phase 8. | |
| D | You choose. | user delegated |

**Decision:** A. Shared strategy-rule modules are mandatory.

---

## Real Versus Fixture Results

| Option | Description | Selected |
|--------|-------------|----------|
| A | Real backtest artifacts only from documented real runs; otherwise schemas/fixtures without performance claims. | yes |
| B | Prepare infrastructure only, no results of any kind. | |
| C | Allow simulated fixture results to look like performance. | |
| D | You choose. | user delegated |

**Decision:** A. No fake results or fake performance claims.

---

## Missing QuantConnect Access

| Option | Description | Selected |
|--------|-------------|----------|
| A | Mark cloud execution as not_run, document commands/prerequisites, continue offline tests. | yes |
| B | Stop the phase until credentials exist. | |
| C | Create placeholder performance results. | |
| D | You choose. | user delegated |

**Decision:** A. Continue safely with explicit not-run status.

---

## Execution Realism

| Option | Description | Selected |
|--------|-------------|----------|
| A | Next valid tradable price by default, no same-close fills, same-bar ambiguity fails closed. | yes |
| B | Simplify by allowing same-close fills in fixtures. | |
| C | Decide later in Phase 8. | |
| D | You choose. | user delegated |

**Decision:** A. Conservative timing and fill assumptions.

---

## Reporting And Validation Windows

| Option | Description | Selected |
|--------|-------------|----------|
| A | Full-period, year-by-year, IS/OOS, walk-forward/equivalent, sensitivity, benchmark, fees/slippage, activation gates. | yes |
| B | Only full-period summary. | |
| C | Only raw QuantConnect output. | |
| D | You choose. | user delegated |

**Decision:** A. Comprehensive report and validation coverage, with unavailable
windows explicitly labeled.

---

## Activation Gates

| Option | Description | Selected |
|--------|-------------|----------|
| A | Paper eligibility blocked by default until typed validation approval passes. | yes |
| B | Treat high score as enough for Paper eligibility. | |
| C | Defer all approval state to Phase 8. | |
| D | You choose. | user delegated |

**Decision:** A. Validation approval state defaults to not approved for Paper.

---

## Notification Preview

| Option | Description | Selected |
|--------|-------------|----------|
| A | Historical backtests send no real notifications; preview uses typed fake collector only. | yes |
| B | No notification preview support. | |
| C | Real Telegram messages from backtests. | |
| D | You choose. | user delegated |

**Decision:** A. Preview mode only, transport-neutral, no Telegram delivery.

---

## Deferred Ideas

- Actual QuantConnect Paper Trading remains Phase 8.
- Real Telegram delivery remains Phase 8.
- Render dashboard display remains Phase 9.

