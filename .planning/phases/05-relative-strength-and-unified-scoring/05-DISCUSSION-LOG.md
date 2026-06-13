# Phase 5: Relative Strength and Unified Scoring - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md - this log preserves the alternatives considered.

**Date:** 2026-06-13
**Phase:** 5-Relative Strength and Unified Scoring
**Areas discussed:** Relative Strength Leader, MarketPilot Score, Classification and Confidence, Setup Ranking and Combined Swing Gate

---

## Relative Strength Leader

| Question | Option | Description | Selected |
|----------|--------|-------------|----------|
| How should Relative Strength Leader operate in Phase 5? | A | Independent setup and confirmation for other setups. | yes |
| How should Relative Strength Leader operate in Phase 5? | B | Independent setup only. | |
| How should Relative Strength Leader operate in Phase 5? | C | Ranking/confirmation factor only. | |
| How should Relative Strength Leader operate in Phase 5? | D | Agent chooses. | |
| Which benchmark must be a hard gate? | A | SPY hard gate, QQQ evidence/bonus. | yes |
| Which benchmark must be a hard gate? | B | SPY and QQQ hard gates. | |
| Which benchmark must be a hard gate? | C | Both benchmarks evidence only. | |
| Which benchmark must be a hard gate? | D | Agent chooses. | |
| Which relative strength windows are required? | A | RS20 and RS60 positive versus SPY. | yes |
| Which relative strength windows are required? | B | RS20 only. | |
| Which relative strength windows are required? | C | RS60 only. | |
| Which relative strength windows are required? | D | Agent chooses. | |
| How should QQQ be handled for non-technology or non-growth stocks? | A | Always measure QQQ but do not reject if QQQ is negative. | agent |
| How should QQQ be handled for non-technology or non-growth stocks? | B | Apply QQQ hard gate only to relevant sectors. | |
| How should QQQ be handled for non-technology or non-growth stocks? | C | Do not use QQQ in this phase. | |
| How should QQQ be handled for non-technology or non-growth stocks? | D | Agent chooses. | user |

**User's choice:** A, A, A, then D.  
**Notes:** The agent chose the recommended QQQ policy: always measure QQQ as evidence/bonus, but do not reject a symbol solely because QQQ relative strength is weak.

---

## MarketPilot Score

| Question | Option | Description | Selected |
|----------|--------|-------------|----------|
| How should MarketPilot Score be built? | A | Use master spec weights: trend 25, relative strength 20, momentum 15, setup quality 20, volume confirmation 10, risk quality 10. | agent |
| How should MarketPilot Score be built? | B | Increase relative strength and momentum weights. | |
| How should MarketPilot Score be built? | C | Start with component evidence only. | |
| How should MarketPilot Score be built? | D | Agent chooses. | user |
| How should score categories work across setups? | A | Shared score categories with setup-specific evidence mapping. | agent |
| How should score categories work across setups? | B | Different weights per setup. | |
| How should score categories work across setups? | C | Per-setup score only, no unified ranking. | |
| How should score categories work across setups? | D | Agent chooses. | user |
| How should hard rejections interact with scoring? | A | Hard rejection overrides score while preserving evidence where possible. | agent |
| How should hard rejections interact with scoring? | B | Hard rejection zeros total score. | |
| How should hard rejections interact with scoring? | C | Hard rejection only reduces score. | |
| How should hard rejections interact with scoring? | D | Agent chooses. | user |
| How should missing scoring data be handled? | A | Fail closed for required missing/invalid/stale data. | agent |
| How should missing scoring data be handled? | B | Missing component receives 0 points without automatic rejection. | |
| How should missing scoring data be handled? | C | Missing component receives neutral score. | |
| How should missing scoring data be handled? | D | Agent chooses. | user |

**User's choice:** D, D, D, D.  
**Notes:** The agent chose the recommended conservative scoring policy for all delegated questions.

---

## Classification And Confidence

| Question | Option | Description | Selected |
|----------|--------|-------------|----------|
| Which classification labels should Phase 5 use? | A | BUY_CANDIDATE, WATCH, AVOID, REJECTED. | yes |
| Which classification labels should Phase 5 use? | B | BUY_CANDIDATE, WATCH, REJECTED only. | |
| Which classification labels should Phase 5 use? | C | WATCH, AVOID, REJECTED only. | |
| Which classification labels should Phase 5 use? | D | Agent chooses. | |
| What should the default classification boundaries be? | A | Master spec boundaries. | yes |
| What should the default classification boundaries be? | B | Stricter BUY_CANDIDATE >= 80 and WATCH 65-79. | |
| What should the default classification boundaries be? | C | No BUY_CANDIDATE until after backtests. | |
| What should the default classification boundaries be? | D | Agent chooses. | |
| How should confidence be calculated? | A | Evidence reliability and completeness. | agent |
| How should confidence be calculated? | B | Confidence equals total score. | |
| How should confidence be calculated? | C | Confidence based only on data quality/readiness. | |
| How should confidence be calculated? | D | Agent chooses. | user |
| How should Phase 5 handle unavailable portfolio constraints and activation gates? | A | Explicit unavailable/not_evaluated placeholders can downgrade otherwise strong candidates to WATCH. | agent |
| How should Phase 5 handle unavailable portfolio constraints and activation gates? | B | Ignore them in Phase 5. | |
| How should Phase 5 handle unavailable portfolio constraints and activation gates? | C | Assume they pass until built. | |
| How should Phase 5 handle unavailable portfolio constraints and activation gates? | D | Agent chooses. | user |

**User's choice:** A, A, D, D.  
**Notes:** The agent chose the recommended confidence and unavailable-gate policies.

---

## Setup Ranking And Combined Swing Gate

| Question | Option | Description | Selected |
|----------|--------|-------------|----------|
| How should candidates be ranked when multiple setups are valid for the same symbol? | A | One candidate per symbol with best primary setup and supporting setups retained as evidence. | yes |
| How should candidates be ranked when multiple setups are valid for the same symbol? | B | Separate candidate per setup for the same symbol. | |
| How should candidates be ranked when multiple setups are valid for the same symbol? | C | Always choose first setup by fixed order. | |
| How should candidates be ranked when multiple setups are valid for the same symbol? | D | Agent chooses. | |
| What is the score tie-breaker? | A | Higher confidence, then better risk quality, then stronger relative strength. | agent |
| What is the score tie-breaker? | B | Relative strength first, then confidence. | |
| What is the score tie-breaker? | C | Fixed setup priority. | |
| What is the score tie-breaker? | D | Agent chooses. | user |
| How should Combined Swing remain locked? | A | Explicit readiness gate until independent validation, backtests, OOS results, understood components, and no duplicate/overfit risk. | agent |
| How should Combined Swing remain locked? | B | Do not mention Combined Swing in code. | |
| How should Combined Swing remain locked? | C | Create skeleton with no logic. | |
| How should Combined Swing remain locked? | D | Agent chooses. | user |
| What output should Phase 5 produce for ranking? | A | RankedCandidate audit objects with score, components, classification, confidence, evidence, timing, and explanation. | agent |
| What output should Phase 5 produce for ranking? | B | Simple symbols plus scores. | |
| What output should Phase 5 produce for ranking? | C | Signal objects with entry/stop/target/order intent. | |
| What output should Phase 5 produce for ranking? | D | Agent chooses. | user |

**User's choice:** A, D, D, D.  
**Notes:** The agent chose the recommended ranking, readiness-gate, and audit-output policies.

---

## The Agent's Discretion

- QQQ is always measured as evidence/bonus and never a standalone hard rejection.
- Master specification score weights are the default scoring model.
- Shared score categories are used across setups with setup-specific evidence mapping.
- Hard rejection overrides score while preserving audit evidence where possible.
- Required missing/invalid/stale scoring data fails closed.
- Confidence measures reliability and completeness rather than duplicating total score.
- Later portfolio constraints and activation gates are explicit unavailable/not-evaluated placeholders.
- Tie-breakers are confidence, risk quality, then relative strength.
- Combined Swing stays disabled behind an explicit readiness gate.
- RankedCandidate output remains audit-only and contains no order intent.

## Deferred Ideas

- Full portfolio constraints, position sizing, stops, targets, orders, fills,
  and exits remain deferred to Phase 6.
- Independent backtests, out-of-sample validation, activation gates, and
  Combined Swing validation remain deferred to Phase 7.
- Telegram alerts remain deferred to notification phases.
- Paper Trading deployment remains deferred to Phase 8.
- Dashboard presentation remains deferred to Phase 9.
