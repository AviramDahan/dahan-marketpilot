---
phase: 04-volume-breakout
verified: 2026-06-13T17:41:25Z
status: gaps_found
score: "7/8 must-haves verified"
overrides_applied: 0
gaps:
  - truth: "Signals are rejected for stale data."
    status: failed
    reason: "Phase 4 ROADMAP success criterion requires stale-data rejection, but evaluate_volume_breakout() calls SymbolData.future_signal_ready(REQUIRED_INDICATORS) without passing stale=True or otherwise checking SymbolData.last_update/staleness. A SymbolData instance with an old last_update and otherwise ready inputs still returns a valid Volume Breakout result."
    artifacts:
      - path: "marketpilot/setups/volume_breakout.py"
        issue: "No stale-data input, threshold, or last_update/stale flag is used in the setup readiness gate."
      - path: "tests/test_volume_breakout_rejections.py"
        issue: "No Volume Breakout stale-data rejection test exists."
    missing:
      - "Add a Volume Breakout stale-data gate or explicit stale input wired into SymbolData.future_signal_ready(..., stale=True)."
      - "Add a deterministic test proving stale data rejects the setup."
---

# Phase 4: Volume Breakout Verification Report

**Phase Goal:** Implement Volume Breakout as an independently testable setup with current-bar exclusion and volume confirmation.
**Verified:** 2026-06-13T17:41:25Z
**Status:** gaps_found
**Re-verification:** No - initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Prior resistance excludes the current bar and uses the configured completed-bar window. | VERIFIED | `calculate_prior_resistance()` uses `bars[-lookback_bars - 1 : -1]`; `config/volume_breakout.yaml` sets `lookback_bars: 20`; tests cover `test_prior_resistance_excludes_current_bar_high` and `test_current_bar_high_does_not_affect_prior_resistance`. |
| 2 | Breakout validity requires completed daily close above buffered resistance, not intraday high alone. | VERIFIED | `evaluate_volume_breakout()` compares `latest.close > buffered_resistance`; `test_rejects_intraday_high_without_completed_close_breakout` passes. |
| 3 | Breakout signals require volume confirmation, acceptable EMA20 extension, acceptable ATR, sufficient dollar volume, valid reward/risk, and non-RISK_OFF regime. | VERIFIED | Evaluator checks `volume_ratio`, `ema20_extension_pct`, `atr_pct`, `average_dollar_volume`, calculated `reward_risk_proxy`, and `MarketRegime.RISK_OFF`; targeted rejection tests pass. |
| 4 | Signals are rejected for earnings-risk conflict, poor reward/risk, and portfolio conflicts. | VERIFIED | Explicit earnings conflict, weak calculated reward/risk, and explicit portfolio conflict tests pass in `tests/test_volume_breakout_rejections.py`. |
| 5 | Signals are rejected for stale data. | FAILED | `marketpilot/setups/volume_breakout.py` calls `future_signal_ready(REQUIRED_INDICATORS)` without stale awareness. A local probe with `last_update=datetime(2000, 1, 1)` returned `valid` with no rejection reasons, while `readiness_for(..., stale=True)` returns `stale`. |
| 6 | Unit tests prove current-bar exclusion and no same-close fill/trade assumption. | VERIFIED | Current-bar exclusion tests pass; safety tests assert no `order`, `quantity`, `portfolio_weight`, `telegram_message`, `backtest_result`, `classification`, or `total_score` attributes. |
| 7 | Volume Breakout is independently testable and evidence-only, with no BUY/WATCH/AVOID classifications, orders, sizing, portfolio state, fake backtest/performance, Telegram delivery, or live/Paper deployment. | VERIFIED | Production setup files contain no forbidden trading/deployment/credential strings; docs and config state disabled behavior; Phase 4 targeted safety tests pass. |
| 8 | Documentation and tests cover the setup contract, evidence, rejection rules, and deferred boundaries. | VERIFIED | `docs/volume_breakout.md`, `docs/testing.md`, and `docs/safety.md` exist and are exercised by `tests/test_volume_breakout_safety.py`. |

**Score:** 7/8 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `marketpilot/setups/base.py` | Shared setup result and rejection vocabulary | VERIFIED | Includes Volume Breakout rejection reasons such as `INVALID_PRIOR_RESISTANCE`, `BREAKOUT_NOT_CONFIRMED`, `VOLUME_CONFIRMATION_WEAK`, `EMA20_EXTENSION_EXCESSIVE`, `INSUFFICIENT_DOLLAR_VOLUME`, `EARNINGS_RISK_CONFLICT`, and `PORTFOLIO_CONFLICT`. |
| `marketpilot/setups/volume_breakout.py` | Volume Breakout config, helper, evaluator, evidence, and setup-only result | PARTIAL | Substantive and wired to tests, but missing stale-data rejection required by ROADMAP success criterion 3. |
| `config/volume_breakout.yaml` | Fail-closed defaults and disabled behaviors | VERIFIED | Contains completed daily-bar timing, 20-bar lookback, 1.5x volume threshold, risk thresholds, and disabled trading/deployment behaviors. |
| `tests/test_volume_breakout_contract.py` | Contract and current-bar exclusion tests | VERIFIED | Passes under targeted test run. |
| `tests/test_volume_breakout_detection.py` | Completed-close breakout and volume tests | VERIFIED | Passes under targeted test run. |
| `tests/test_volume_breakout_rejections.py` | SET-04 rejection tests | PARTIAL | Covers SET-04 gates, but does not cover stale-data rejection from ROADMAP success criterion 3. |
| `tests/test_volume_breakout_explanations.py` | Evidence and explanation tests | VERIFIED | Passes under targeted test run. |
| `tests/test_volume_breakout_safety.py` | Forbidden-behavior and setup-only safety tests | VERIFIED | Passes under targeted test run. |
| `docs/volume_breakout.md` | Setup documentation | VERIFIED | Documents current-bar exclusion, close confirmation, gates, evidence, and deferred boundaries. |
| `docs/testing.md` | Testing documentation | VERIFIED | Lists Phase 4 deterministic offline tests. |
| `docs/safety.md` | Safety documentation | VERIFIED | Records Volume Breakout setup-only boundary and paper-only disclaimer. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `tests/test_volume_breakout_contract.py` | `marketpilot/setups/volume_breakout.py` | Imports config/helper/contract functions | VERIFIED | Tests import and exercise `load_volume_breakout_config`, `calculate_prior_resistance`, and `contract_result`. |
| `marketpilot/setups/volume_breakout.py` | `config/volume_breakout.yaml` | `DEFAULT_CONFIG_PATH` and `yaml.safe_load` | VERIFIED | Loader reads the YAML config and fails closed on unsafe timing/paper settings. |
| `marketpilot/setups/volume_breakout.py` | `marketpilot/setups/base.py` | `SetupResult`, `NumericEvidence`, `SetupRejectionReason` | VERIFIED | Evaluator returns shared setup result contracts. |
| `marketpilot/setups/volume_breakout.py` | `marketpilot/symbol_data.py` | `SymbolData.future_signal_ready(REQUIRED_INDICATORS)` | PARTIAL | Readiness is wired for missing/invalid/rejected data, but stale mode is not wired. |
| `tests/test_volume_breakout_safety.py` | production setup files | Static forbidden-behavior scan | VERIFIED | Safety test scans `base.py` and `volume_breakout.py`. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `marketpilot/setups/volume_breakout.py` | `prior_resistance` | `calculate_prior_resistance(setup_input.bars, lookback_bars)` | Yes | VERIFIED - computed from previous completed bars only. |
| `marketpilot/setups/volume_breakout.py` | `volume_ratio` | `latest.volume / setup_input.average_volume` | Yes | VERIFIED - rejects weak or invalid volume. |
| `marketpilot/setups/volume_breakout.py` | `reward_risk_proxy` | `projected_target`, `latest.close`, `prior_resistance` | Yes | VERIFIED - evaluator calculates the proxy; no precomputed field exists. |
| `marketpilot/setups/volume_breakout.py` | `stale data` | `SymbolData.last_update` or `future_signal_ready(..., stale=True)` | No | FAILED - no stale flag or timestamp check flows into evaluation. |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Phase 4 targeted tests pass | `python -m pytest tests/test_volume_breakout_contract.py tests/test_volume_breakout_detection.py tests/test_volume_breakout_rejections.py tests/test_volume_breakout_explanations.py tests/test_volume_breakout_safety.py -x` | `24 passed in 0.14s` | PASS |
| Full test suite passes | `python -m pytest` | `118 passed in 0.34s` | PASS |
| Stale data is rejected | Inline Python probe with ready inputs and `SymbolData.last_update=datetime(2000, 1, 1)` | Result was `valid` with `[]` rejection reasons | FAIL |

### Probe Execution

| Probe | Command | Result | Status |
|-------|---------|--------|--------|
| Conventional phase probes | N/A | No `scripts/**/tests/probe-*.sh` probes are part of Phase 4. | SKIPPED |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| SET-03 | 04-01, 04-02 | Volume Breakout calculates prior resistance from previous completed bars only, excluding the current bar. | SATISFIED | Code slice excludes `bars[-1]`; targeted tests pass. |
| SET-04 | 04-02, 04-03 | Volume Breakout requires volume confirmation, acceptable ATR, acceptable EMA20 extension, sufficient dollar volume, valid reward/risk, and non-RISK_OFF regime. | SATISFIED | Evaluator implements all named SET-04 gates and tests pass. |
| ROADMAP SC 3 | ROADMAP Phase 4 | Signals are rejected for stale data, earnings-risk conflict, poor reward/risk, or portfolio conflicts. | BLOCKED | Earnings, reward/risk, and portfolio conflict are covered; stale data is not. |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `docs/volume_breakout.md` | 70, 115 | `placeholder` | INFO | Intentional deferred Phase 6 portfolio-conflict placeholder documented as out of scope; not a blocker. |

### Human Verification Required

None. Phase 4 is deterministic offline setup logic and was programmatically checkable.

### Gaps Summary

Phase 4 largely implements the Volume Breakout setup and SET-03/SET-04 requirements, with passing targeted and full tests. The blocking gap is ROADMAP success criterion 3: stale-data rejection is not implemented in `evaluate_volume_breakout()`. Existing `SymbolData` can represent stale readiness only when the caller passes `stale=True`, but Volume Breakout never passes or derives that flag, and has no test for it.

---

_Verified: 2026-06-13T17:41:25Z_
_Verifier: the agent (gsd-verifier)_
