---
phase: 04-volume-breakout
verified: 2026-06-13T18:05:51Z
status: passed
score: "8/8 must-haves verified"
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: "7/8"
  gaps_closed:
    - "Signals are rejected for stale data."
  gaps_remaining: []
  regressions: []
---

# Phase 4: Volume Breakout Verification Report

**Phase Goal:** Implement Volume Breakout as an independently testable setup with current-bar exclusion and volume confirmation.
**Verified:** 2026-06-13T18:05:51Z
**Status:** passed
**Re-verification:** Yes - after gap closure 04-04

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Prior resistance excludes the current bar and uses the configured completed-bar window. | VERIFIED | `calculate_prior_resistance()` uses `bars[-lookback_bars - 1 : -1]` in `marketpilot/setups/volume_breakout.py:78`; `config/volume_breakout.yaml` sets `lookback_bars: 20`; tests cover high current-bar exclusion. |
| 2 | Breakout validity requires completed daily close above buffered resistance, not intraday high alone. | VERIFIED | `evaluate_volume_breakout()` compares `latest.close > buffered_resistance`; `tests/test_volume_breakout_detection.py::test_rejects_intraday_high_without_completed_close_breakout` passed in the Phase 4 suite. |
| 3 | Breakout signals require volume confirmation, acceptable EMA20 extension, acceptable ATR, sufficient dollar volume, valid reward/risk, and non-RISK_OFF regime. | VERIFIED | Evaluator checks `volume_ratio`, `ema20_extension_pct`, `atr_pct`, `average_dollar_volume`, evaluator-calculated `reward_risk_proxy`, and `MarketRegime.RISK_OFF`/`future_entries_allowed`; targeted rejection tests passed. |
| 4 | Signals are rejected for stale data, earnings-risk conflict, poor reward/risk, or portfolio conflicts. | VERIFIED | The prior stale-data gap is closed: `VolumeBreakoutInput.symbol_data_stale` exists, `future_signal_ready(REQUIRED_INDICATORS, stale=setup_input.symbol_data_stale)` is wired, stale results reject with `DATA_NOT_READY`, and evidence includes `symbol_data_stale=True, passed=False`. Earnings conflict, weak reward/risk, and portfolio conflict tests also passed. |
| 5 | Stale-data rejection is auditable and uses the existing SymbolData readiness boundary. | VERIFIED | `marketpilot/symbol_data.py` returns `IndicatorReadiness.STALE` when `stale=True`; `marketpilot/setups/volume_breakout.py:106` delegates stale readiness to `SymbolData.future_signal_ready(...)`; `tests/test_volume_breakout_rejections.py::test_rejects_stale_symbol_data_readiness` passed. Inline probe returned `rejected`, `DATA_NOT_READY=True`, and `symbol_data_stale=True, passed=False`. |
| 6 | Unit tests prove current-bar exclusion and no same-close fill/trade assumption. | VERIFIED | Current-bar exclusion tests passed; safety tests assert no `order`, `quantity`, `portfolio_weight`, `telegram_message`, `backtest_result`, `classification`, or `total_score` attributes. No same-close fill field or order path exists. |
| 7 | Volume Breakout is independently testable and evidence-only, with no BUY/WATCH/AVOID classifications, orders, sizing, portfolio state, fake backtest/performance, Telegram delivery, or live/Paper deployment. | VERIFIED | Production setup files contain no forbidden strings for BUY/WATCH/AVOID, order APIs, credentials, Telegram, backtest result creation, or deployment behavior; config explicitly disables these behaviors and tests enforce the boundary. |
| 8 | Documentation and tests cover the setup contract, evidence, rejection rules, stale-data gate, and deferred boundaries. | VERIFIED | `docs/volume_breakout.md`, `docs/testing.md`, and `docs/safety.md` document stale readiness, setup-only output, hard gates, deferred scoring/risk/backtest/deployment boundaries, and no fake results/profitability claims. |

**Score:** 8/8 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `marketpilot/setups/base.py` | Shared setup result and rejection vocabulary | VERIFIED | Contains shared `SetupResult`, `SetupTiming`, `NumericEvidence`, and Volume Breakout rejection reasons. |
| `marketpilot/setups/volume_breakout.py` | Volume Breakout config, helper, evaluator, evidence, and setup-only result | VERIFIED | 256 substantive lines; implements current-bar-excluded resistance, SET-04 gates, stale-readiness delegation, evidence, and setup-only result construction. |
| `config/volume_breakout.yaml` | Fail-closed defaults and disabled behaviors | VERIFIED | Contains completed daily-bar timing, 20-bar lookback, 1.5x volume threshold, risk thresholds, and disabled trading/deployment behaviors. |
| `tests/test_volume_breakout_contract.py` | Contract and current-bar exclusion tests | VERIFIED | Passed under targeted Phase 4 run. |
| `tests/test_volume_breakout_detection.py` | Completed-close breakout and volume tests | VERIFIED | Passed under targeted Phase 4 run. |
| `tests/test_volume_breakout_rejections.py` | SET-04 and stale-data rejection tests | VERIFIED | Contains and passes `test_rejects_stale_symbol_data_readiness`; covers RISK_OFF, readiness, ATR, EMA20 extension, dollar volume, reward/risk, earnings conflict, and portfolio conflict. |
| `tests/test_volume_breakout_explanations.py` | Evidence and explanation tests | VERIFIED | Passed under targeted Phase 4 run. |
| `tests/test_volume_breakout_safety.py` | Forbidden-behavior and setup-only safety tests | VERIFIED | Passed under targeted Phase 4 run. |
| `docs/volume_breakout.md` | Setup documentation | VERIFIED | Documents current-bar exclusion, close confirmation, SET-04 gates, stale readiness, evidence, and deferred boundaries. |
| `docs/testing.md` | Testing documentation | VERIFIED | Lists Phase 4 deterministic offline tests including stale SymbolData readiness rejection. |
| `docs/safety.md` | Safety documentation | VERIFIED | Records Volume Breakout setup-only boundary and paper-only disclaimer. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `tests/test_volume_breakout_contract.py` | `marketpilot/setups/volume_breakout.py` | Imports config/helper/contract functions | VERIFIED | Tests import and exercise `load_volume_breakout_config`, `calculate_prior_resistance`, and `contract_result`. |
| `marketpilot/setups/volume_breakout.py` | `config/volume_breakout.yaml` | `DEFAULT_CONFIG_PATH` and `yaml.safe_load` | VERIFIED | Loader reads the YAML config and fails closed on unsafe timing/paper settings. |
| `marketpilot/setups/volume_breakout.py` | `marketpilot/setups/base.py` | `SetupResult`, `NumericEvidence`, `SetupRejectionReason` | VERIFIED | Evaluator returns shared setup result contracts. |
| `marketpilot/setups/volume_breakout.py` | `marketpilot/symbol_data.py` | `SymbolData.future_signal_ready(REQUIRED_INDICATORS, stale=setup_input.symbol_data_stale)` | VERIFIED | Stale readiness now flows through the existing SymbolData readiness gate before valid setup output. |
| `tests/test_volume_breakout_rejections.py` | `marketpilot/setups/volume_breakout.py` | `valid_input(symbol_data_stale=True)` | VERIFIED | Test proves stale readiness rejects with `DATA_NOT_READY` and failed `symbol_data_stale` evidence. |
| `tests/test_volume_breakout_safety.py` | production setup files | Static forbidden-behavior scan | VERIFIED | Safety test scans `base.py` and `volume_breakout.py` for forbidden behavior strings. |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `marketpilot/setups/volume_breakout.py` | `prior_resistance` | `calculate_prior_resistance(setup_input.bars, lookback_bars)` | Yes | VERIFIED - computed from previous completed bars only. |
| `marketpilot/setups/volume_breakout.py` | `volume_ratio` | `latest.volume / setup_input.average_volume` | Yes | VERIFIED - rejects weak or invalid volume. |
| `marketpilot/setups/volume_breakout.py` | `reward_risk_proxy` | `projected_target`, `latest.close`, `prior_resistance`, config threshold | Yes | VERIFIED - evaluator calculates the proxy; no precomputed input field exists. |
| `marketpilot/setups/volume_breakout.py` | `symbol_data_stale` | `VolumeBreakoutInput.symbol_data_stale` -> `SymbolData.future_signal_ready(..., stale=...)` -> `DATA_NOT_READY` rejection | Yes | VERIFIED - stale data is rejected and evidence is emitted before early result building. |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Stale data is rejected | `python -m pytest tests/test_volume_breakout_rejections.py::test_rejects_stale_symbol_data_readiness -x` | `1 passed in 0.03s` | PASS |
| Phase 4 targeted tests pass | `python -m pytest tests/test_volume_breakout_contract.py tests/test_volume_breakout_detection.py tests/test_volume_breakout_rejections.py tests/test_volume_breakout_explanations.py tests/test_volume_breakout_safety.py -x` | `25 passed in 0.12s` | PASS |
| Full test suite passes | `python -m pytest` | `119 passed in 0.36s` | PASS |
| Stale rejection evidence is auditable | Inline Python probe importing the test fixture and evaluating `symbol_data_stale=True` | Output: `rejected`, `True`, `symbol_data_stale=True, passed=False` | PASS |

### Probe Execution

| Probe | Command | Result | Status |
|-------|---------|--------|--------|
| Conventional phase probes | `Get-ChildItem -Recurse scripts -Filter 'probe-*.sh'` and phase probe grep | No `scripts/**/tests/probe-*.sh` probes are part of Phase 4. | SKIPPED |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| SET-03 | 04-01, 04-02 | Volume Breakout calculates prior resistance from previous completed bars only, excluding the current bar. | SATISFIED | Code slice excludes `bars[-1]`; contract and detection tests pass. |
| SET-04 | 04-02, 04-03, 04-04 | Volume Breakout requires volume confirmation, acceptable ATR, acceptable EMA20 extension, sufficient dollar volume, valid reward/risk, non-RISK_OFF regime, and data readiness including stale SymbolData readiness. | SATISFIED | Evaluator implements all named gates; stale readiness passes through `future_signal_ready(..., stale=...)`; targeted and full suites pass. |
| ROADMAP SC 1 | ROADMAP Phase 4 | Prior resistance excludes the current bar and uses the configured completed-bar window. | SATISFIED | `calculate_prior_resistance()` slice and tests prove exclusion. |
| ROADMAP SC 2 | ROADMAP Phase 4 | Breakout signals require volume confirmation, acceptable extension, acceptable ATR, and valid reward/risk. | SATISFIED | Rejection tests cover each gate and evidence item. |
| ROADMAP SC 3 | ROADMAP Phase 4 | Signals are rejected for stale data, earnings-risk conflict, poor reward/risk, or portfolio conflicts. | SATISFIED | Stale, earnings conflict, weak reward/risk, and portfolio conflict tests pass. |
| ROADMAP SC 4 | ROADMAP Phase 4 | Unit tests prove current-bar exclusion and no same-close fill assumption. | SATISFIED | Current-bar exclusion tests and setup-only safety tests pass; no order/fill fields exist. |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `docs/volume_breakout.md` | 70, 117 | `placeholder` | INFO | Intentional Phase 6 portfolio-conflict handoff boundary; not a stub in Phase 4 because real portfolio constraints are explicitly deferred. |

### Human Verification Required

None. Phase 4 is deterministic offline setup logic and was programmatically checkable.

### Gaps Summary

No blocking gaps remain. The prior stale-data gap is closed in code, tests, and docs. Phase 4 now satisfies SET-03, SET-04, all ROADMAP success criteria, and the setup-only safety boundary.

### Tooling Note

`gsd-tools` was not available in this shell session, so roadmap, artifact, and key-link checks were performed directly against `ROADMAP.md`, plan frontmatter, source code, tests, and documentation.

---

_Verified: 2026-06-13T18:05:51Z_
_Verifier: the agent (gsd-verifier)_
