# Phase 7 Patterns: Backtesting and Validation

**Date:** 2026-06-14
**Status:** Planning patterns complete

## Existing Patterns To Reuse

- Frozen dataclasses and string enums from `marketpilot/scoring.py`,
  `marketpilot/risk.py`, `marketpilot/order_lifecycle.py`, and
  `marketpilot/exits.py`.
- YAML config loaders with `paper_trading_only: true`, `yaml.safe_load`, mapping
  validation, and explicit disabled unsafe behavior flags.
- Deterministic offline pytest files under `tests/`.
- Safety tests that scan production files for forbidden behavior.
- Documentation synchronized with implementation in the same phase.

## Suggested Modules

- `marketpilot/backtesting.py` for execution assumptions, local harness input,
  simulated event output, and no-look-ahead validation helpers.
- `marketpilot/backtest_reports.py` for report schema, parser fixtures,
  chronological windows, benchmark comparison, and limitation text.
- `marketpilot/validation.py` for walk-forward/sensitivity validation and
  activation-gate decisions.
- `config/backtesting.yaml` for fees, slippage, fill model, timing assumptions,
  validation windows, benchmark symbols, and disabled unsafe behavior flags.

