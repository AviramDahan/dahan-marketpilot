# Research: Pitfalls

## Safety Pitfalls

- Accidentally adding a real-broker adapter or live-money mode.
- Allowing `PAPER_TRADING_ONLY` to be overridden silently.
- Letting dashboard controls submit or modify orders.
- Logging credentials, tokens, chat IDs, API tokens, or QuantConnect account details.
- Treating Telegram success as required for protective trading logic.

## QuantConnect Pitfalls

- Inventing APIs or relying on stale examples.
- Using current-bar data in prior-high or breakout calculations.
- Generating a signal from a completed bar and filling at the same close without a proven valid execution path.
- Treating incomplete, stale, NaN, infinite, or missing indicator data as neutral or positive.
- Reducing the universe silently to a tiny ticker list.
- Failing to clean indicators when symbols leave the universe.
- Assuming Paper Trading execution equals real execution.

## Backtesting Pitfalls

- Look-ahead bias.
- Survivorship bias from universe selection.
- Current-constituent bias in historical tests.
- Over-optimization across many windows or thresholds.
- Fabricating backtest results or placeholders that look real.
- Reporting aggregate results without year-by-year and chronological validation.
- Claiming profitability or future certainty.

## Dashboard Pitfalls

- Maintaining independent active paper state in Render.
- Hiding stale QuantConnect reads.
- Displaying NIS values without FX timestamp/source/staleness context.
- Exposing secrets in errors.
- Making reports look like live state.

## Licensing Pitfalls

- Copying QuantConnect code without tracking Apache-2.0 attribution requirements.
- Failing to distinguish project license from third-party code licenses.
- Omitting NOTICE or third-party attribution for directly reused code.

## Operational Pitfalls

- Running cloud workflows without explicit credential setup.
- Asking the user to paste secrets into chat.
- Creating commits when the user did not request them.
- Starting Phase 1 implementation during initialization.
