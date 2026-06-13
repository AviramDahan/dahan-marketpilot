# MarketPilot Scoring

Phase 5 scoring is an audit-only consumer of setup evidence. It turns
`SetupResult` evidence into shared score components, total score,
classification, confidence, hard rejection reasons, and explanation lines.

Default component weights total 100:

- trend structure: 25
- relative strength: 20
- momentum: 15
- setup quality: 20
- volume confirmation: 10
- risk quality: 10

Classifications are `BUY_CANDIDATE`, `WATCH`, `AVOID`, and `REJECTED`.
Hard rejection always overrides score. Missing required scoring evidence fails
closed and cannot become a neutral or positive score.

Portfolio and activation gates are explicit `not_evaluated` by default in
Phase 5. They cannot silently produce a `BUY_CANDIDATE`. Sector fit is recorded
as contextual gate evidence and is not a standalone hard rejection until a
verified sector/industry source exists.

Scoring output has no entry, stop, target, quantity, order, broker, Paper
Trading, Telegram, credential, fake backtest, or profitability behavior.

## Ranking

Ranking emits at most one audit candidate per symbol. The strongest setup
becomes `primary_setup`, while other valid setup scores for the same symbol are
retained as `supporting_setups`.

Tie-break order is total score, confidence, risk quality, then relative
strength.

Combined Swing remains disabled behind explicit readiness prerequisites:
independent validation for Trend Pullback, Volume Breakout, and Relative
Strength Leader; independent backtests; out-of-sample results; score
contribution understanding; duplicate-entry risk checks; and overfitting risk
checks.
