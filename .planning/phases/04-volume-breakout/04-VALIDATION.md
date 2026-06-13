# Phase 04: Volume Breakout - Validation Contract

**Created:** 2026-06-13
**Scope:** Planning artifact only. This file defines the checks execution agents must satisfy for Phase 04; it does not implement production code.

## Validation Goal

Phase 04 is valid only when Volume Breakout is independently testable as setup evidence, with current-bar-excluded prior resistance, completed-close breakout confirmation, SET-04 hard gates, and no order, stop, target, sizing, portfolio lifecycle, backtest, Telegram, Paper deployment, Live deployment, credential, fake performance, or profitability behavior.

## Phase Commands

| Gate | Command | Acceptance |
|------|---------|------------|
| Contract gate | `python -m pytest tests/test_volume_breakout_contract.py -x` | Config, setup contract, rejection vocabulary, and current-bar-excluded resistance helper pass. |
| Detection gate | `python -m pytest tests/test_volume_breakout_detection.py -x` | Completed-close breakout detection, high-only rejection, current-bar exclusion, and volume confirmation pass. |
| Rejection gate | `python -m pytest tests/test_volume_breakout_rejections.py -x` | SET-04 gates reject invalid candidates with evidence, including evaluator-calculated reward/risk proxy. |
| Explanation gate | `python -m pytest tests/test_volume_breakout_explanations.py -x` | Required numeric evidence and explanations exist without score, confidence, ranking, or classification behavior. |
| Safety gate | `python -m pytest tests/test_volume_breakout_safety.py -x` | Static and behavioral checks prove setup-only output and forbidden behavior absence. |
| Phase quick gate | `python -m pytest tests/test_volume_breakout_contract.py tests/test_volume_breakout_detection.py tests/test_volume_breakout_rejections.py tests/test_volume_breakout_explanations.py tests/test_volume_breakout_safety.py -x` | All Phase 04 targeted tests pass together. |
| Full project gate | `python -m pytest` | Existing project behavior remains green. |

## Requirement Coverage

| Requirement | Required Validation | Test File | Command | Acceptance Check |
|-------------|---------------------|-----------|---------|------------------|
| SET-03 | Prior resistance is calculated from previous completed bars only and excludes the current bar. | `tests/test_volume_breakout_contract.py`, `tests/test_volume_breakout_detection.py` | `python -m pytest tests/test_volume_breakout_contract.py::test_prior_resistance_excludes_current_bar_high tests/test_volume_breakout_detection.py::test_current_bar_high_does_not_affect_prior_resistance -x` | A fixture with a current-bar high far above prior highs still records prior resistance from prior bars only. |
| SET-03 | Incomplete bars and insufficient history fail closed. | `tests/test_volume_breakout_contract.py`, `tests/test_volume_breakout_detection.py` | `python -m pytest tests/test_volume_breakout_contract.py tests/test_volume_breakout_detection.py -x` | Invalid or incomplete completed-daily-bar inputs reject instead of inventing resistance. |
| SET-04 | Volume confirmation, ATR, EMA20 extension, dollar volume, reward/risk, and non-RISK_OFF gates are enforced. | `tests/test_volume_breakout_detection.py`, `tests/test_volume_breakout_rejections.py` | `python -m pytest tests/test_volume_breakout_detection.py tests/test_volume_breakout_rejections.py -x` | Each gate has a passing fixture and a failing fixture with matching rejection reason and numeric evidence. |
| SET-04 | Reward/risk is calculated by the evaluator, not accepted as a precomputed threshold input. | `tests/test_volume_breakout_rejections.py` | `python -m pytest tests/test_volume_breakout_rejections.py::test_calculates_reward_risk_proxy_from_projected_target_and_resistance -x` | With `latest.close=105`, `prior_resistance=100`, and `projected_target=115`, evidence records `risk_per_share_proxy=5`, `reward_per_share_proxy=10`, and `reward_risk_proxy=2.0`; lowering `projected_target` below the configured threshold rejects. |
| SET-04 | Result output remains setup evidence only. | `tests/test_volume_breakout_explanations.py`, `tests/test_volume_breakout_safety.py` | `python -m pytest tests/test_volume_breakout_explanations.py tests/test_volume_breakout_safety.py -x` | No BUY/WATCH/AVOID, score, confidence, ranking, order, stop, target, sizing, portfolio state, backtest result, Telegram delivery, or deployment field exists. |

## Decision Coverage

| Decision | Validation Mapping | Acceptance Check |
|----------|--------------------|------------------|
| D-01 | `tests/test_volume_breakout_contract.py::test_prior_resistance_excludes_current_bar_high` | `calculate_prior_resistance()` uses only previous completed bars. |
| D-02 | `tests/test_volume_breakout_contract.py::test_volume_breakout_config_contains_safety_bounded_defaults` | Default `resistance.lookback_bars` is 20. |
| D-03 | `tests/test_volume_breakout_detection.py::test_rejects_intraday_high_without_completed_close_breakout` | A high above resistance with close below buffered resistance is rejected. |
| D-04 | `tests/test_volume_breakout_detection.py` | Breakout comparison uses `prior_resistance * (1 + breakout_buffer_pct / 100)`. |
| D-05 | `tests/test_volume_breakout_detection.py::test_detects_valid_volume_breakout_on_completed_close_and_volume` | Breakout-bar volume is compared with average volume. |
| D-06 | `tests/test_volume_breakout_contract.py` and `tests/test_volume_breakout_detection.py` | Default minimum volume ratio is 1.5 and weak volume rejects. |
| D-07 | `tests/test_volume_breakout_rejections.py` | EMA20 extension above config rejects with numeric evidence. |
| D-08 | `tests/test_volume_breakout_rejections.py` | `RISK_OFF` or `future_entries_allowed == False` rejects. |
| D-09 | `tests/test_volume_breakout_rejections.py` | ATR percentage above config rejects. |
| D-10 | `tests/test_volume_breakout_rejections.py::test_calculates_reward_risk_proxy_from_projected_target_and_resistance` | Evaluator computes `reward_risk_proxy = max(projected_target - latest.close, 0) / max(latest.close - prior_resistance, epsilon)` using broken resistance as base/stop proxy and never creates stops, targets, orders, or lifecycle behavior. |
| D-11 | `tests/test_volume_breakout_rejections.py` | Unverified earnings source records evidence but does not reject; verified explicit conflict rejects. |
| D-12 | `tests/test_volume_breakout_rejections.py` | Portfolio conflict behavior uses only explicit placeholder input and does not calculate real constraints. |
| D-13 | `tests/test_volume_breakout_explanations.py` | Required numeric evidence names exist for valid and rejected results. |
| D-14 | `tests/test_volume_breakout_explanations.py` | Results contain valid/rejected status, evidence, explanations, and reasons only. |
| D-15 | `tests/test_volume_breakout_safety.py` | Static scan and result checks reject forbidden trading, scoring, notification, deployment, and credential behavior. |
| D-16 | `tests/test_volume_breakout_contract.py`, `docs/volume_breakout.md` | Volume Breakout is a module parallel to Trend Pullback, not a broad setup framework refactor. |

## Acceptance Checklist

- [ ] All Phase 04 targeted pytest files exist.
- [ ] `config/volume_breakout.yaml` contains fail-closed defaults and disabled behaviors.
- [ ] `marketpilot/setups/volume_breakout.py` exposes setup evidence only.
- [ ] `reward_risk_proxy` is evaluator-calculated from `projected_target`, `latest.close`, and `prior_resistance`.
- [ ] `projected_target` is documented and tested as setup evidence input only, not an order target or lifecycle target.
- [ ] No Phase 04 artifact contains fake backtest results, fake portfolio values, credential examples, or profitability claims.
