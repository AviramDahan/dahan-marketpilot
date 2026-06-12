# Phase 4: Volume Breakout - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md - this log preserves the alternatives considered.

**Date:** 2026-06-13
**Phase:** 4-Volume Breakout
**Areas discussed:** Prior resistance calculation, Breakout confirmation, Risk and rejection gates, Evidence explanations and phase boundaries

---

## Prior Resistance Calculation

| Question | Option A | Option B | Option C | Selected |
|----------|----------|----------|----------|----------|
| How should prior resistance be calculated? | Highest high from N completed daily bars, excluding current bar | Swing highs only | You choose | A |
| What default resistance lookback should be used? | 20 completed daily bars | 50 completed daily bars | You choose | A |
| Should breakout validity require a close above resistance or is an intraday high enough? | Close above resistance required | High above resistance may be enough | You choose | A |
| Should a small configurable buffer be required above resistance? | Configurable percentage buffer | No buffer | You choose | A |

**User's choice:** A, A, A, then A for the follow-up missing answer.
**Notes:** Current-bar exclusion and completed daily-bar timing remain locked from prior phases.

---

## Breakout Confirmation

| Question | Option A | Option B | Option C | Selected |
|----------|----------|----------|----------|----------|
| What volume confirmation is required for a breakout? | Breakout bar volume above 20-day average by configurable ratio | Breakout bar volume above 50-day average | You choose | A |
| What default volume ratio should be required? | 1.5x average volume | 2.0x average volume | You choose | A |
| Should a breakout be rejected when price is too extended from EMA20? | Reject overextension above configurable threshold | Do not reject overextension in this phase | You choose | A |
| How should RISK_OFF be handled? | RISK_OFF rejects Volume Breakout | RISK_OFF is evidence only | You choose | A |

**User's choice:** A, then A A A for remaining answers.
**Notes:** The user accepted the recommended conservative confirmation policy.

---

## Risk And Rejection Gates

| Question | Option A | Option B | Option C | Selected |
|----------|----------|----------|----------|----------|
| How should excessive ATR be handled? | Reject when ATR% exceeds configurable threshold | Record ATR as evidence only | You choose | C |
| How should reward/risk proxy be calculated in this phase? | Use broken resistance as conservative stop/base proxy | Use ATR-only stop proxy | You choose | A |
| How should earnings risk be handled when no verified source exists? | Evidence/deferred only without verified source | Reject whenever earnings source is not verified | You choose | A |
| How should portfolio conflicts be represented in this phase? | Placeholder rejection/evidence only | Ignore until Phase 6 | You choose | A |

**User's choice:** C, A, A, A.
**Notes:** For the delegated ATR question, the agent selected the recommended conservative hard-rejection policy.

---

## Evidence Explanations And Phase Boundaries

| Question | Option A | Option B | Option C | Selected |
|----------|----------|----------|----------|----------|
| Which evidence must appear in the Volume Breakout result? | Full evidence set | Minimal resistance/close/volume evidence | You choose | A |
| How should Phase 4 connect to Phase 5 scoring? | Evidence and rejections only until Phase 5 | Temporary internal breakout score now | You choose | A |
| Which words or behaviors must stay out of Phase 4 code? | Exclude all forbidden behaviors | Only orders/live trading are forbidden | You choose | A |
| What implementation shape should Phase 4 prefer? | Parallel Volume Breakout module | Generalize trend_pullback.py now | You choose | A |

**User's choice:** A A A A.
**Notes:** Phase 4 should mirror the Trend Pullback module shape and stay setup-only.

---

## the agent's Discretion

- The user delegated excessive ATR handling. The locked decision is to reject
  excessive ATR% using a configurable threshold.

## Deferred Ideas

- Verified earnings-risk source and live earnings calendar integration.
- Real portfolio constraints, position sizing, stop/target/order lifecycle, and
  portfolio conflict calculation.
- BUY/WATCH/AVOID classifications and full MarketPilot scoring.
- Backtest results and activation gates.
- Telegram alerts.
- Live/Paper deployment behavior.
