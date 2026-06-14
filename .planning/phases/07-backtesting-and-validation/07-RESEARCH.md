# Phase 7 Research: Backtesting and Validation

**Date:** 2026-06-14
**Status:** Planning research complete

## Research Summary

Phase 7 must validate the strategy pipeline before Paper Trading. Official
performance authority belongs to QuantConnect Cloud/LEAN when real runs are
available, while deterministic local tests prove no-look-ahead, timing,
reporting, and activation-gate behavior without credentials.

## Findings

- Backtest and Paper behavior must share rule modules. The backtest layer should
  adapt completed-bar setup, scoring, ranking, risk, lifecycle, exits, audit,
  and preview events instead of duplicating strategy decisions.
- Local harness tests should focus on correctness properties: no future bars,
  current-bar exclusion, next-valid-fill timing, same-bar ambiguity, stale data,
  and strategy-mode alignment.
- Real performance reports must come only from documented real runs. Fixtures
  may test parsers and schemas but must be labeled as fixtures and must not look
  like real performance claims.
- Validation reports should separate full-period, year-by-year, in-sample,
  out-of-sample, walk-forward/equivalent chronological validation, sensitivity,
  benchmark comparison, fee/slippage assumptions, activation gates, and not-run
  cloud checks.
- Activation state must default to not approved for Paper Trading until
  validation gates explicitly pass.

## Deferrals

- Actual QuantConnect Paper Trading remains Phase 8.
- Real Telegram delivery remains Phase 8.
- Dashboard presentation remains Phase 9.

