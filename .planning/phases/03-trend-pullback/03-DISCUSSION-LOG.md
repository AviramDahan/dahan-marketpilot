# Phase 3: Trend Pullback - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md - this log preserves the alternatives considered.

**Date:** 2026-06-13
**Phase:** 3-Trend Pullback
**Areas discussed:** Pullback Structure, Recovery Confirmation, Hard Rejections, Signal Timing And Evidence

---

## Pullback Structure

| Question | Option | Description | Selected |
|----------|--------|-------------|----------|
| Valid pullback shape | A | Touch or approach EMA20/EMA50 | Yes |
| Valid pullback shape | B | Broader pullback inside an uptrend | |
| Valid pullback shape | C | Codex chooses | |
| Pullback duration | A | 2-10 trading days | Yes |
| Pullback duration | B | 1-5 trading days | |
| Pullback duration | C | Codex chooses | |
| EMA50 structure | A | Break below EMA50 rejects | Yes |
| EMA50 structure | B | Allow small wick/deviation if recovery is strong | |
| EMA50 structure | C | Codex chooses | |

**User's choice:** A A A
**Notes:** User accepted the recommended conservative pullback structure.

---

## Recovery Confirmation

| Question | Option | Description | Selected |
|----------|--------|-------------|----------|
| Recovery confirmation | A | Completed daily close above prior candle high | Yes |
| Recovery confirmation | B | Close back above EMA20 | |
| Recovery confirmation | C | Codex chooses | |
| Volume confirmation | A | Recovery volume above a short average | Yes |
| Volume confirmation | B | Record volume only as evidence | |
| Volume confirmation | C | Codex chooses | |
| RSI/MACD role | A | Supporting evidence, not a hard gate | Yes |
| RSI/MACD role | B | RSI or MACD must cross a threshold | |
| RSI/MACD role | C | Codex chooses | |

**User's choice:** A A A
**Notes:** User accepted recovery confirmation by daily close, volume support, and RSI/MACD as evidence only.

---

## Hard Rejections

| Question | Option | Description | Selected |
|----------|--------|-------------|----------|
| Immediate rejects | A | RISK_OFF, unready data, EMA50 break, excessive ATR, weak reward/risk | Yes |
| Immediate rejects | B | Only unready data and RISK_OFF | |
| Immediate rejects | C | Codex chooses | |
| Earnings risk | A | Deferred verified-source gate; do not reject without verified data | Yes |
| Earnings risk | B | Fixture-only field to simulate earnings risk | |
| Earnings risk | C | Codex chooses | |
| Missing full stop/target lifecycle | A | Minimal reward/risk proxy | Yes |
| Missing full stop/target lifecycle | B | Document reward/risk as missing | |
| Missing full stop/target lifecycle | C | Codex chooses | |

**User's choice:** A A A
**Notes:** User accepted strict rejection behavior while keeping earnings risk deferred and reward/risk limited to a proxy.

---

## Signal Timing And Evidence

| Question | Option | Description | Selected |
|----------|--------|-------------|----------|
| Signal validity timing | A | Valid only after completed daily candle close | Yes |
| Signal validity timing | B | Intrabar validity if conditions are met | Initially selected, then corrected |
| Signal validity timing | C | Codex chooses | |
| Required evidence | A | Numeric values, rejection reasons, readiness, regime, and timing | Yes |
| Required evidence | B | Only valid/rejected with a short reason | |
| Required evidence | C | Codex chooses | |
| Classification output | A | No BUY/WATCH/AVOID; only setup result and evidence | Yes |
| Classification output | B | Return WATCH for valid setup | |
| Classification output | C | Codex chooses | |

**User's choice:** B A A initially; Q1 corrected and confirmed as A after conflict with completed-daily-bar project constraints was explained.
**Notes:** Final locked decision is A A A. Intrabar validity is deferred and out of scope for Phase 3.

---

## the agent's Discretion

- Routine implementation details such as exact config key names, fixture layout,
  and dataclass names may be chosen by the planner.
- No strategic gray area was left to open-ended discretion.

## Deferred Ideas

- Intrabar signal validity.
- Verified earnings-risk data source.
- Full stop/target/order lifecycle.
- BUY/WATCH/AVOID classifications and full MarketPilot scoring.
- Backtest results and activation gates.
- Telegram alerts.

