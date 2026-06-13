# Phase 04: Volume Breakout - Research

**Researched:** 2026-06-13
**Domain:** Python setup evaluator, completed daily-bar signal timing, no-look-ahead breakout evidence
**Confidence:** HIGH for codebase-local contracts; LOW for exact threshold defaults that were not locked in context

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

## Implementation Decisions

### Prior Resistance Calculation

- **D-01:** Prior resistance is calculated as the highest high from a
  configurable completed daily-bar lookback window, excluding the current bar.
- **D-02:** The default resistance lookback window is 20 completed daily bars.
- **D-03:** Breakout validity requires the completed daily close to be above
  prior resistance. An intraday high above resistance is not enough.
- **D-04:** A small configurable percentage buffer above resistance is required
  to avoid treating borderline closes as valid breakouts.

### Breakout Confirmation

- **D-05:** Volume confirmation uses the breakout bar's volume compared against
  a 20-day average volume baseline.
- **D-06:** The default volume confirmation threshold is at least 1.5x the
  average volume.
- **D-07:** Breakouts are rejected when price is overextended from EMA20 above a
  configurable threshold.
- **D-08:** `RISK_OFF` rejects Volume Breakout validity, matching the Phase 3
  Trend Pullback entry-gate behavior.

### Risk And Rejection Gates

- **D-09:** Excessive ATR% is a hard rejection using a configurable threshold.
- **D-10:** Phase 4 should calculate a conservative reward/risk proxy using the
  broken resistance area as the base/stop proxy. This must not create orders,
  real stops, targets, or position lifecycle behavior.
- **D-11:** Earnings risk remains a deferred verified-source gate. If no
  verified earnings data source exists, Phase 4 must not invent data and must
  not reject symbols based only on unverified earnings assumptions.
- **D-12:** Portfolio conflicts are represented only as future-compatible
  evidence/rejection placeholders. Phase 4 must not calculate real portfolio
  constraints before Phase 6.

### Evidence, Explanations, And Boundaries

- **D-13:** Every Volume Breakout result should include numeric evidence for
  resistance level, lookback window, breakout buffer, breakout close, volume
  ratio, EMA20 extension, ATR%, reward/risk proxy, and market regime.
- **D-14:** Phase 4 returns setup results with valid/rejected status, evidence,
  explanations, and rejection reasons only. It must not add score or
  classification behavior before Phase 5.
- **D-15:** Phase 4 code must exclude `BUY`, `WATCH`, `AVOID`, orders, position
  sizing, portfolio state, backtest result creation, Telegram delivery, and
  live/Paper deployment behavior.
- **D-16:** Prefer a module parallel to Trend Pullback:
  `config/volume_breakout.yaml`, `marketpilot/setups/volume_breakout.py`,
  matching tests, and documentation. Do not generalize `trend_pullback.py` into
  a broader framework during this phase unless planning proves it necessary.

### the agent's Discretion

The user selected the recommended option for every discussed decision except
the excessive ATR handling question, where the user chose "You choose." The
locked agent choice is the recommended conservative policy: excessive ATR% is a
hard rejection with a configurable threshold, consistent with SET-04 and Phase
3 Trend Pullback.

### Deferred Ideas (OUT OF SCOPE)

- Verified earnings-risk source and live earnings calendar integration are
  deferred to a later phase.
- Real portfolio constraints, position sizing, stop/target/order lifecycle, and
  portfolio conflict calculation are deferred to Phase 6.
- BUY/WATCH/AVOID classifications and full MarketPilot scoring are deferred to
  Phase 5.
- Backtest results and activation gates are deferred to Phase 7.
- Telegram alerts are deferred to notification phases.
- Live/Paper deployment behavior is deferred to Paper Trading phases.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SET-03 | Volume Breakout calculates prior resistance from the previous completed bars only, excluding the current bar. | Use a `prior_bars = bars[-lookback - 1:-1]` style slice or equivalent explicit exclusion, reject insufficient completed bars, and test that a current-bar high cannot become resistance. [CITED: .planning/REQUIREMENTS.md] [CITED: .planning/phases/04-volume-breakout/04-CONTEXT.md] |
| SET-04 | Volume Breakout requires volume confirmation, acceptable ATR, acceptable EMA20 extension, sufficient dollar volume, valid reward/risk, and non-RISK_OFF regime. | Mirror Trend Pullback hard-gate structure, add breakout-specific evidence and reasons, and keep result output limited to setup evidence. [CITED: .planning/REQUIREMENTS.md] [VERIFIED: codebase grep] |
</phase_requirements>

## Summary

Phase 4 should be implemented as a parallel setup module, not as a refactor of Trend Pullback. The local standard is a pure Python evaluator under `marketpilot/setups/`, a YAML config under `config/`, deterministic offline pytest files, and setup documentation under `docs/`. [CITED: .planning/phases/04-volume-breakout/04-CONTEXT.md] [VERIFIED: codebase grep]

The central technical risk is look-ahead bias. Prior resistance must be computed from completed bars before the signal bar only; the signal bar's high must never participate in the resistance window, and the breakout must be confirmed by the completed signal-bar close above `prior_resistance * (1 + breakout_buffer_pct / 100)`. [CITED: .planning/phases/04-volume-breakout/04-CONTEXT.md]

Volume Breakout should return only `SetupResult` evidence and rejection reasons. It must not produce orders, quantities, portfolio weights, BUY/WATCH/AVOID labels, backtest results, Telegram messages, or Paper/Live deployment behavior. [CITED: .planning/phases/04-volume-breakout/04-CONTEXT.md] [VERIFIED: tests/test_trend_pullback_safety.py]

**Primary recommendation:** Create `marketpilot/setups/volume_breakout.py`, `config/volume_breakout.yaml`, `docs/volume_breakout.md`, and mirrored test files that prove current-bar exclusion, completed-bar timing, volume confirmation, hard rejections, evidence completeness, and forbidden-behavior absence. [CITED: .planning/phases/04-volume-breakout/04-CONTEXT.md] [VERIFIED: codebase grep]

## Project Constraints (from AGENTS.md)

- Read `.planning/PROJECT.md`, `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`, and `.planning/STATE.md` before phase work. [CITED: AGENTS.md]
- Do not modify completed phases without a change plan. [CITED: AGENTS.md]
- Use focused commits only for completed, verified units and only under the repository commit policy; this research file was written without creating an implementation commit. [CITED: AGENTS.md]
- Keep project files, code, identifiers, configuration, tests, docs, commit messages, and GSD artifacts in English. [CITED: AGENTS.md]
- Never invent QuantConnect APIs, LEAN classes, Cloud endpoints, package behavior, tutorial details, backtest results, paper results, portfolio values, or profitability claims. [CITED: AGENTS.md]
- Never add real-broker code, real-money credentials, leverage, margin, short selling, options, futures, cryptocurrency trading, hidden live-trading switches, or dashboard order controls. [CITED: AGENTS.md]
- Keep QuantConnect as source of truth for future paper portfolio and backtest state; this phase does not touch that state. [CITED: AGENTS.md]
- Telegram failures must remain independent from trading safety, and Telegram secrets must never appear in logs, docs, tests, reports, or chat. [CITED: AGENTS.md]
- Verify external package legitimacy before adding dependencies; Phase 4 should add no new dependencies. [CITED: AGENTS.md] [VERIFIED: codebase grep]

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|--------------|----------------|-----------|
| Prior-resistance calculation | Backend / strategy domain | Tests | It is deterministic setup logic over completed daily-bar fixtures, not browser, dashboard, or QuantConnect Cloud state. [VERIFIED: marketpilot/setups/trend_pullback.py] |
| Current-bar exclusion and completed-bar timing | Backend / strategy domain | Tests | `SetupTiming` already records completed daily-bar metadata, and Trend Pullback rejects incomplete bars. [VERIFIED: marketpilot/setups/base.py] [VERIFIED: marketpilot/setups/trend_pullback.py] |
| Volume, ATR, EMA20 extension, dollar-volume, reward/risk gates | Backend / strategy domain | Configuration | Setup evaluator should consume numeric inputs and config thresholds, then emit evidence and rejections. [CITED: .planning/phases/04-volume-breakout/04-CONTEXT.md] |
| Data readiness | Backend / symbol data | Indicators | `SymbolData.future_signal_ready()` is the existing readiness boundary for setup eligibility. [VERIFIED: marketpilot/symbol_data.py] |
| Market regime gate | Backend / regime domain | Setup evaluator | `RegimeResult.future_entries_allowed` and `MarketRegime.RISK_OFF` already model future-entry gating. [VERIFIED: marketpilot/regime.py] |
| Orders, sizing, portfolio conflicts, Telegram, backtests | Out of scope | Later phases | Phase 4 may record placeholders only; real behavior is deferred to Phases 5-8. [CITED: .planning/phases/04-volume-breakout/04-CONTEXT.md] |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.10.10 available locally | Setup evaluator, dataclasses, enum contracts | Existing project source is Python and local runtime is available. [VERIFIED: python --version] |
| `dataclasses`, `enum`, `math`, `pathlib`, `typing` | stdlib | Frozen input/result contracts, validation helpers, config paths | Existing setup modules use these stdlib tools. [VERIFIED: marketpilot/setups/base.py] [VERIFIED: marketpilot/setups/trend_pullback.py] |
| PyYAML `yaml.safe_load` | 6.0.3 available locally | Load `config/volume_breakout.yaml` with fail-closed safety checks | Trend Pullback already uses `yaml.safe_load`; no new config parser is needed. [VERIFIED: marketpilot/setups/trend_pullback.py] [VERIFIED: python -c import yaml] |
| pytest | 7.3.1 available locally | Deterministic offline unit tests | Existing docs and Phase 3 verification use `python -m pytest`. [VERIFIED: python -m pytest --version] [CITED: docs/testing.md] |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `marketpilot.setups.base` | local | `SetupResult`, `SetupTiming`, `NumericEvidence`, `SetupStatus`, rejection vocabulary | Use for every Volume Breakout result. [VERIFIED: marketpilot/setups/base.py] |
| `marketpilot.symbol_data.SymbolData` | local | Data-quality and indicator readiness gate | Use before evaluating breakout-specific rules. [VERIFIED: marketpilot/symbol_data.py] |
| `marketpilot.indicators.IndicatorResult` | local | Required indicator readiness and numeric values | Use for EMA20/ATR/volume-related readiness inputs. [VERIFIED: marketpilot/indicators.py] |
| `marketpilot.regime.RegimeResult` | local | Non-RISK_OFF future-entry gate | Use to reject RISK_OFF and unready regime results. [VERIFIED: marketpilot/regime.py] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| New setup result dataclasses | Reuse `SetupResult` | New result types would break the Phase 3 contract and make Phase 5 scoring consume inconsistent evidence. [VERIFIED: marketpilot/setups/base.py] |
| Pandas rolling windows | Tuple/list slicing | Pandas is unnecessary for deterministic fixture tests and would add dependency surface. [ASSUMED] |
| QuantConnect runtime indicators | Offline numeric input contract | This phase must remain independently testable without QuantConnect, internet, or credentials. [CITED: docs/testing.md] |

**Installation:** No new packages should be installed for Phase 4. [VERIFIED: codebase grep]

## Package Legitimacy Audit

Phase 4 should install no external packages. Existing local dependencies Python, PyYAML, and pytest are already present in the project environment. [VERIFIED: python --version] [VERIFIED: python -m pytest --version] [VERIFIED: python -c import yaml]

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| None | N/A | N/A | N/A | N/A | N/A | No package install required. [VERIFIED: codebase grep] |

**Packages removed due to [SLOP] verdict:** none.
**Packages flagged as suspicious [SUS]:** none.

## Architecture Patterns

### System Architecture Diagram

```text
Completed daily bars + SymbolData + indicators + RegimeResult + config
        |
        v
Validate config safety and disabled behaviors
        |
        v
Reject if bars are incomplete or history is insufficient
        |
        v
Readiness gate: SymbolData.future_signal_ready(required_indicators)
        |
        v
Regime gate: reject RISK_OFF or future_entries_allowed == False
        |
        v
Prior resistance: max(high for previous completed bars only)
        |
        v
Breakout decision: latest completed close > buffered prior resistance?
        |
        +--> no: rejected SetupResult with evidence
        |
        v
Volume / ATR / EMA20 extension / dollar-volume / reward-risk gates
        |
        +--> any fail: rejected SetupResult with evidence
        |
        v
Valid SetupResult with SetupTiming(completed_daily_bar) and numeric evidence
```

### Recommended Project Structure

```text
marketpilot/
└── setups/
    ├── base.py                 # Shared setup result and rejection contracts
    ├── trend_pullback.py       # Existing pattern to mirror
    └── volume_breakout.py      # New Phase 4 evaluator
config/
└── volume_breakout.yaml        # New fail-closed setup config
docs/
└── volume_breakout.md          # New setup documentation
tests/
├── test_volume_breakout_contract.py
├── test_volume_breakout_detection.py
├── test_volume_breakout_rejections.py
├── test_volume_breakout_explanations.py
└── test_volume_breakout_safety.py
```

### Pattern 1: Parallel Setup Module

**What:** Add `VolumeBreakoutInput`, `load_volume_breakout_config()`, `evaluate_volume_breakout()`, and `contract_result()` in a new module parallel to Trend Pullback. [CITED: .planning/phases/04-volume-breakout/04-CONTEXT.md] [VERIFIED: marketpilot/setups/trend_pullback.py]

**When to use:** Use when implementing Phase 4; do not generalize existing setup modules unless planning proves the duplication is unsafe. [CITED: .planning/phases/04-volume-breakout/04-CONTEXT.md]

**Example:**

```python
# Source: marketpilot/setups/trend_pullback.py pattern, adapted for planning only.
def load_volume_breakout_config(path=DEFAULT_CONFIG_PATH) -> dict:
    with Path(path).open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    config = loaded.get("volume_breakout", loaded)
    if config.get("paper_trading_only") is not True:
        raise ValueError("volume_breakout config requires paper_trading_only: true.")
    if config.get("disabled_behaviors", {}).get("intrabar_validity") is not False:
        raise ValueError("Volume Breakout must use completed daily bars only.")
    return config
```

### Pattern 2: Explicit Current-Bar Exclusion

**What:** Resistance is based on previous completed bars only, not on `bars[-1]`. [CITED: .planning/phases/04-volume-breakout/04-CONTEXT.md]

**When to use:** In the breakout evaluator before comparing the latest completed close to resistance. [CITED: .planning/phases/04-volume-breakout/04-CONTEXT.md]

**Example:**

```python
# Source: Phase 4 CONTEXT.md D-01 through D-04.
latest = bars[-1]
prior_bars = bars[-lookback - 1:-1]
prior_resistance = max(bar.high for bar in prior_bars)
buffered_resistance = prior_resistance * (1 + breakout_buffer_pct / 100)
close_breaks_out = latest.close > buffered_resistance
```

### Pattern 3: Evidence-First Rejection

**What:** Every gate should append `NumericEvidence` with value, threshold, and pass/fail before returning a `SetupResult`. [VERIFIED: marketpilot/setups/trend_pullback.py]

**When to use:** For resistance, close, buffer, volume ratio, EMA20 extension, ATR percentage, dollar volume, reward/risk proxy, regime, earnings source, and portfolio placeholder. [CITED: .planning/phases/04-volume-breakout/04-CONTEXT.md]

### Anti-Patterns to Avoid

- **Using current bar in resistance:** This creates look-ahead bias and can make a breakout impossible or falsely calibrated. Use previous completed bars only. [CITED: .planning/phases/04-volume-breakout/04-CONTEXT.md]
- **Intraday high breakout validity:** The locked decision requires completed close confirmation, not intraday high. [CITED: .planning/phases/04-volume-breakout/04-CONTEXT.md]
- **Same-close fill assumption:** Phase 4 can record signal timing but must not imply execution at the same close; tests should assert no fill/order fields exist. [CITED: .planning/ROADMAP.md] [VERIFIED: tests/test_trend_pullback_safety.py]
- **Adding scoring/classification early:** BUY/WATCH/AVOID and full MarketPilot scoring are Phase 5 scope. [CITED: .planning/phases/04-volume-breakout/04-CONTEXT.md]
- **Inventing earnings rejections:** Earnings risk remains evidence/deferred until a verified source exists. [CITED: .planning/phases/04-volume-breakout/04-CONTEXT.md]
- **Calculating real portfolio conflicts:** Phase 4 may include placeholder evidence only; real portfolio constraints belong to Phase 6. [CITED: .planning/phases/04-volume-breakout/04-CONTEXT.md]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Setup result vocabulary | Custom result objects | `SetupResult`, `SetupStatus`, `SetupTiming`, `NumericEvidence` | Existing contracts already support valid/rejected status, evidence, timing, and explanations. [VERIFIED: marketpilot/setups/base.py] |
| Data readiness | One-off checks in the breakout module | `SymbolData.future_signal_ready()` and `IndicatorResult` statuses | Existing readiness rejects missing, invalid, stale, and insufficient data. [VERIFIED: marketpilot/symbol_data.py] |
| Regime logic | New regime enum or string matching | `MarketRegime` and `RegimeResult.future_entries_allowed` | Existing regime result already models RISK_OFF entry gating. [VERIFIED: marketpilot/regime.py] |
| Config parser | Custom YAML parser or ad hoc strings | `yaml.safe_load` with fail-closed config checks | Existing setup config loader pattern is sufficient. [VERIFIED: marketpilot/setups/trend_pullback.py] |
| Backtest or order simulation | Fake fills, fake stops, fake portfolio values | No implementation in Phase 4 | Backtests, activation gates, orders, sizing, and portfolio lifecycle are later phases. [CITED: .planning/phases/04-volume-breakout/04-CONTEXT.md] |

**Key insight:** Volume Breakout is a setup-evidence module in this phase. Keeping it side-effect free makes current-bar exclusion easy to test and prevents premature trading behavior from leaking into a research-only setup contract. [CITED: .planning/phases/04-volume-breakout/04-CONTEXT.md] [VERIFIED: tests/test_trend_pullback_safety.py]

## Common Pitfalls

### Pitfall 1: Resistance Window Accidentally Includes The Signal Bar

**What goes wrong:** The evaluator uses `bars[-lookback:]` and includes `bars[-1].high` in `prior_resistance`. [ASSUMED]

**Why it happens:** Rolling-window code often treats the latest bar as part of the lookback unless exclusion is explicit. [ASSUMED]

**How to avoid:** Use an explicitly named `prior_bars` slice ending before the latest bar and add a test where the current bar's high is far above all prior highs. [CITED: .planning/phases/04-volume-breakout/04-CONTEXT.md]

**Warning signs:** A fixture with prior highs near 100, current high 120, and close 106 fails to detect resistance near 100. [ASSUMED]

### Pitfall 2: Intraday High Treated As Breakout

**What goes wrong:** A bar with high above resistance but close below resistance is accepted. [CITED: .planning/phases/04-volume-breakout/04-CONTEXT.md]

**Why it happens:** Breakout terminology often focuses on highs, but the project locked close-based confirmation. [CITED: .planning/phases/04-volume-breakout/04-CONTEXT.md]

**How to avoid:** Add a rejection reason for close-not-above-buffered-resistance and fixture it directly. [ASSUMED]

**Warning signs:** Evidence records `breakout_high` as passed while `breakout_close` failed, yet result is valid. [ASSUMED]

### Pitfall 3: Evidence Missing For Failed Gates

**What goes wrong:** Rejected results include reasons but omit the numeric evidence needed for audit and Phase 5 scoring. [VERIFIED: marketpilot/setups/trend_pullback.py]

**Why it happens:** Early returns before evidence collection drop useful audit facts. [ASSUMED]

**How to avoid:** Follow the Trend Pullback pattern of building evidence and reasons together, then calling a single `_build_result()`. [VERIFIED: marketpilot/setups/trend_pullback.py]

**Warning signs:** A rejected result has `SetupRejectionReason.EXCESSIVE_ATR` but no `atr_pct` evidence item. [ASSUMED]

### Pitfall 4: Same-Bar Execution Leakage

**What goes wrong:** The setup result grows `order`, `quantity`, `target`, `stop`, `fill_price`, or same-close execution fields. [CITED: .planning/phases/04-volume-breakout/04-CONTEXT.md]

**Why it happens:** Breakout setups often imply an entry, but this phase is only setup evidence. [CITED: .planning/phases/04-volume-breakout/04-CONTEXT.md]

**How to avoid:** Mirror `test_trend_pullback_safety.py` and assert forbidden attributes and strings are absent. [VERIFIED: tests/test_trend_pullback_safety.py]

**Warning signs:** Production setup files contain `MarketOrder`, `SetHoldings`, `Liquidate`, `BUY`, `WATCH`, `AVOID`, `BacktestResult`, `token`, or `password`. [VERIFIED: tests/test_trend_pullback_safety.py]

## Code Examples

### Breakout Evidence Contract

```python
# Source: marketpilot/setups/base.py and Phase 4 CONTEXT.md.
evidence.extend(
    [
        NumericEvidence("resistance_lookback_bars", lookback, lookback, len(prior_bars) == lookback),
        NumericEvidence("prior_resistance", round(prior_resistance, 4), "previous_completed_highs", True),
        NumericEvidence("breakout_buffer_pct", breakout_buffer_pct, "config", True),
        NumericEvidence("breakout_close", latest.close, round(buffered_resistance, 4), latest.close > buffered_resistance),
        NumericEvidence("volume_ratio", round(volume_ratio, 4), min_volume_ratio, volume_ratio >= min_volume_ratio),
        NumericEvidence("ema20_extension_pct", round(ema20_extension_pct, 4), max_ema20_extension_pct, ema20_extension_pct <= max_ema20_extension_pct),
        NumericEvidence("atr_pct", atr_pct, max_atr_pct, atr_pct <= max_atr_pct),
        NumericEvidence("projected_target", projected_target, "setup_evidence", projected_target > latest.close),
        NumericEvidence("risk_per_share_proxy", risk_per_share_proxy, "latest.close - prior_resistance", True),
        NumericEvidence("reward_per_share_proxy", reward_per_share_proxy, "projected_target - latest.close", reward_per_share_proxy > 0),
        NumericEvidence("reward_risk_proxy", reward_risk_proxy, min_reward_risk_proxy, reward_risk_proxy >= min_reward_risk_proxy),
        NumericEvidence("regime", setup_input.regime.regime.value, "entry_allowed", setup_input.regime.future_entries_allowed),
    ]
)
```

### Recommended Config Shape

```yaml
# Source: config/trend_pullback.yaml pattern plus Phase 4 CONTEXT.md.
volume_breakout:
  paper_trading_only: true
  timing_mode: completed_daily_bar
  resistance:
    lookback_bars: 20
    breakout_buffer_pct: 0.25
    require_close_above_buffered_resistance: true
  volume:
    average_volume_period: 20
    min_volume_ratio: 1.5
    min_dollar_volume: 20000000
  risk:
    max_atr_pct: 8.0
    max_ema20_extension_pct: 10.0
    min_reward_risk_proxy: 1.5
    reward_risk_epsilon: 0.01
  deferred_gates:
    earnings_risk_source_verified: false
    portfolio_conflict_check_available: false
  disabled_behaviors:
    intrabar_validity: false
    create_orders: false
    portfolio_sizing: false
    buy_watch_avoid_classifications: false
    backtest_result_creation: false
    telegram_delivery: false
```

The defaults for `breakout_buffer_pct` and `max_ema20_extension_pct` are configurable Phase 4 planning defaults, not market-optimized performance claims. [ASSUMED]

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Intrabar or same-bar signal assumptions | Completed daily-bar setup timing with later valid tradable-price execution assumption | Locked by project constraints before Phase 3 and reused in Phase 4 | Volume Breakout must not validate intraday highs or same-close fills. [CITED: .planning/PROJECT.md] [CITED: .planning/phases/03-trend-pullback/03-CONTEXT.md] |
| Setup-specific ad hoc outputs | Shared `SetupResult` with numeric evidence and rejection reasons | Established in Phase 3 | Phase 4 should reuse the same result contract. [VERIFIED: marketpilot/setups/base.py] |
| Strategy behavior mixed with setup detection | Setup detection only; scoring/order/backtest behavior deferred | Locked in Phase 4 context | Planner should split evidence implementation from future scoring and order lifecycle. [CITED: .planning/phases/04-volume-breakout/04-CONTEXT.md] |

**Deprecated/outdated:**
- Treating a current bar high as resistance source or breakout trigger is out of scope for Phase 4. [CITED: .planning/phases/04-volume-breakout/04-CONTEXT.md]
- Returning BUY/WATCH/AVOID labels from setup modules is out of scope until Phase 5. [CITED: .planning/phases/04-volume-breakout/04-CONTEXT.md]
- Creating fake backtest or portfolio artifacts is forbidden. [CITED: docs/safety.md]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Pandas is unnecessary for Phase 4 and tuple/list slicing is sufficient. | Standard Stack | Low; planner can still avoid new dependencies unless implementation complexity proves otherwise. |
| A2 | `breakout_buffer_pct: 0.25` is a reasonable initial configurable default. | Code Examples | Medium; too small or too large a default changes setup selectivity, so tests should verify configurability rather than market quality. |
| A3 | `max_ema20_extension_pct: 10.0` is the Phase 4 configurable planning default. | Code Examples | Medium; threshold affects rejection frequency and should remain configurable. |
| A4 | `max_atr_pct: 8.0`, `min_reward_risk_proxy: 1.5`, and `reward_risk_epsilon: 0.01` can mirror conservative setup gating until unified scoring/risk phases refine them. | Code Examples | Medium; thresholds are conservative planning defaults, not validated performance parameters. |
| A5 | Early-return code is the likely cause of missing failed-gate evidence. | Common Pitfalls | Low; evidence completeness can be enforced by tests regardless of implementation style. |

## Open Questions (RESOLVED)

1. **Exact breakout buffer and EMA20 extension thresholds**
   - Resolution: Use `resistance.breakout_buffer_pct: 0.25` and `risk.max_ema20_extension_pct: 10.0` as configurable Phase 4 defaults. These values are planning defaults for deterministic setup validation, not market-optimized performance claims. [CITED: .planning/phases/04-volume-breakout/04-CONTEXT.md] [CITED: docs/Dahan-MarketPilot-Master-Spec.md]
   - Plan reflection: Plan 04-01 writes the defaults into `config/volume_breakout.yaml`; Plan 04-02 tests config-driven breakout and extension behavior rather than claiming the defaults are profitable.

2. **Exact reward/risk proxy formula**
   - Resolution: The evaluator calculates the proxy; it is not accepted as a precomputed input. `projected_target` is supplied on `VolumeBreakoutInput` as setup evidence only, not as an order target or lifecycle target. Use `risk_per_share_proxy = max(latest.close - prior_resistance, epsilon)`, `reward_per_share_proxy = max(projected_target - latest.close, 0)`, and `reward_risk_proxy = reward_per_share_proxy / risk_per_share_proxy`, with `epsilon` defaulting to `0.01` unless config provides a positive override. [CITED: .planning/phases/04-volume-breakout/04-CONTEXT.md]
   - Plan reflection: Plan 04-02 now requires tests proving the evaluator calculates `risk_per_share_proxy`, `reward_per_share_proxy`, and `reward_risk_proxy` from `latest.close`, `prior_resistance`, and `projected_target`, and that no stop, target, order, or lifecycle behavior is created.

3. **Dollar-volume source**
   - Resolution: Add an explicit numeric setup input field `average_dollar_volume` and evidence item `average_dollar_volume`; do not duplicate Phase 2 universe internals inside Volume Breakout. [CITED: .planning/REQUIREMENTS.md]
   - Plan reflection: Plan 04-02 validates `average_dollar_volume` as an input gate and rejects only from the explicit local value and config threshold.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| Python | Local setup code and tests | yes | 3.10.10 | None needed. [VERIFIED: python --version] |
| pytest | Phase 4 deterministic tests | yes | 7.3.1 | None needed. [VERIFIED: python -m pytest --version] |
| PyYAML | YAML config loader | yes | 6.0.3 | None needed because already used by Trend Pullback. [VERIFIED: python -c import yaml] |
| QuantConnect credentials/API | Not required by Phase 4 | N/A | N/A | Keep offline. [CITED: docs/testing.md] |
| Telegram/Render/broker credentials | Not required by Phase 4 | N/A | N/A | Keep offline. [CITED: docs/testing.md] |

**Missing dependencies with no fallback:** none. [VERIFIED: python --version] [VERIFIED: python -m pytest --version]

**Missing dependencies with fallback:** none. [VERIFIED: python --version] [VERIFIED: python -m pytest --version]

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 7.3.1 [VERIFIED: python -m pytest --version] |
| Config file | existing project pytest configuration or default pytest discovery; no Phase 4-specific config found. [VERIFIED: rg --files tests] |
| Quick run command | `python -m pytest tests/test_volume_breakout_contract.py tests/test_volume_breakout_detection.py tests/test_volume_breakout_rejections.py tests/test_volume_breakout_explanations.py tests/test_volume_breakout_safety.py -x` |
| Full suite command | `python -m pytest` [CITED: docs/testing.md] |

### Phase Requirements -> Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| SET-03 | Prior resistance excludes the current bar and uses the configured completed-bar lookback. | unit | `python -m pytest tests/test_volume_breakout_detection.py::test_prior_resistance_excludes_current_bar_high -x` | No - Wave 0 |
| SET-03 | Incomplete current bar is rejected and never treated as intrabar validity. | unit | `python -m pytest tests/test_volume_breakout_detection.py::test_incomplete_current_bar_is_rejected_not_treated_as_intrabar_signal -x` | No - Wave 0 |
| SET-04 | Valid breakout requires close above buffered resistance plus 1.5x volume confirmation. | unit | `python -m pytest tests/test_volume_breakout_detection.py::test_detects_valid_volume_breakout_on_completed_close_and_volume -x` | No - Wave 0 |
| SET-04 | Reject RISK_OFF, data not ready, excessive ATR, overextension, weak dollar volume, weak reward/risk, and deferred earnings source without fabricating data. | unit | `python -m pytest tests/test_volume_breakout_rejections.py -x` | No - Wave 0 |
| SET-04 | Result includes required numeric evidence and no scoring/order/backtest/Telegram fields. | unit/static | `python -m pytest tests/test_volume_breakout_explanations.py tests/test_volume_breakout_safety.py -x` | No - Wave 0 |

### Sampling Rate

- **Per task commit:** `python -m pytest tests/test_volume_breakout_contract.py tests/test_volume_breakout_detection.py tests/test_volume_breakout_rejections.py tests/test_volume_breakout_explanations.py tests/test_volume_breakout_safety.py -x`
- **Per wave merge:** `python -m pytest`
- **Phase gate:** Full suite green before `$gsd-verify-work`. [CITED: docs/testing.md]

### Wave 0 Gaps

- [ ] `tests/test_volume_breakout_contract.py` - covers setup vocabulary, config defaults, current-bar exclusion contract, and new rejection reasons.
- [ ] `tests/test_volume_breakout_detection.py` - covers valid breakout, close-based trigger, current-bar exclusion, incomplete bar rejection, and volume confirmation.
- [ ] `tests/test_volume_breakout_rejections.py` - covers readiness, RISK_OFF, ATR, EMA20 extension, dollar volume, reward/risk, and deferred earnings/portfolio placeholders.
- [ ] `tests/test_volume_breakout_explanations.py` - covers evidence names and no score/confidence/ranking/classification.
- [ ] `tests/test_volume_breakout_safety.py` - covers forbidden production strings and missing trade/order/deployment attributes.
- [ ] `docs/volume_breakout.md` - documents setup contract, detection rules, rejection rules, evidence, and deferred boundaries.
- [ ] `config/volume_breakout.yaml` - contains fail-closed defaults and disabled behaviors.

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | no | No user authentication or credential flow in Phase 4. [CITED: .planning/phases/04-volume-breakout/04-CONTEXT.md] |
| V3 Session Management | no | No sessions in Phase 4. [CITED: .planning/phases/04-volume-breakout/04-CONTEXT.md] |
| V4 Access Control | no | No user-facing authorization surface in Phase 4. [CITED: .planning/phases/04-volume-breakout/04-CONTEXT.md] |
| V5 Input Validation | yes | Validate completed bars, finite positive numbers, indicator readiness, config mappings, and fail closed on incomplete data. [VERIFIED: marketpilot/setups/trend_pullback.py] [VERIFIED: marketpilot/symbol_data.py] |
| V6 Cryptography | no | No crypto or secret handling in Phase 4. [CITED: docs/safety.md] |
| V8 Data Protection | yes | Do not write credentials, fake performance, fake portfolio values, or secret examples to docs/tests. [CITED: docs/safety.md] |
| V10 Malicious Code | yes | Add static tests forbidding order APIs, Telegram delivery, token/password strings, and fake backtest artifacts in setup files. [VERIFIED: tests/test_trend_pullback_safety.py] |

### Known Threat Patterns for Python Setup Logic

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Look-ahead bias through current-bar resistance | Tampering | Explicit prior-bar slice, named evidence, and fixture proving current-bar high is excluded. [CITED: .planning/phases/04-volume-breakout/04-CONTEXT.md] |
| Invalid numeric data treated as passing | Tampering | Reuse readiness and finite-number validation; reject missing, invalid, NaN, infinite, zero/negative risk values. [VERIFIED: marketpilot/symbol_data.py] [VERIFIED: marketpilot/setups/trend_pullback.py] |
| Secret leakage in docs/tests | Information Disclosure | Keep Phase 4 offline and static-test forbidden `token`, `password`, and credential strings. [CITED: docs/safety.md] [VERIFIED: tests/test_trend_pullback_safety.py] |
| Hidden trading behavior in setup module | Elevation of Privilege | Static tests forbid order APIs, BUY/WATCH/AVOID labels, Paper/Live deployment text, Telegram delivery, and backtest result classes. [VERIFIED: tests/test_trend_pullback_safety.py] |

## Sources

### Primary (HIGH confidence)

- `AGENTS.md` - project constraints, language policy, safety boundaries, commit policy, and documentation sync. [CITED: AGENTS.md]
- `.planning/phases/04-volume-breakout/04-CONTEXT.md` - locked Phase 4 decisions, deferred boundaries, file shape, and evidence requirements. [CITED: .planning/phases/04-volume-breakout/04-CONTEXT.md]
- `.planning/REQUIREMENTS.md` - SET-03 and SET-04 requirement text. [CITED: .planning/REQUIREMENTS.md]
- `.planning/ROADMAP.md` - Phase 4 success criteria and plan breakdown. [CITED: .planning/ROADMAP.md]
- `marketpilot/setups/base.py` - setup result contract. [VERIFIED: codebase grep]
- `marketpilot/setups/trend_pullback.py` - evaluator/config/evidence/rejection pattern. [VERIFIED: codebase grep]
- `config/trend_pullback.yaml` - fail-closed setup config pattern. [VERIFIED: codebase grep]
- `tests/test_trend_pullback_*.py` - mirrored test architecture and forbidden-behavior checks. [VERIFIED: codebase grep]
- `docs/testing.md`, `docs/safety.md`, `docs/indicators.md`, `docs/market_regime.md`, `docs/trend_pullback.md` - documentation patterns and safety/testing constraints. [CITED: docs/testing.md] [CITED: docs/safety.md]

### Secondary (MEDIUM confidence)

- GSD `init.phase-op 4` through local shim - confirmed phase path, missing research, context existence, and config availability. [VERIFIED: gsd-tools init.phase-op]
- Local runtime probes - confirmed Python 3.10.10, pytest 7.3.1, and PyYAML 6.0.3 availability. [VERIFIED: python --version] [VERIFIED: python -m pytest --version] [VERIFIED: python -c import yaml]

### Tertiary (LOW confidence)

- GSD research-plan seam cached a codebase-local digest under provider `codebase`, but the classifier returned LOW for the provider id. The actual implementation guidance is therefore grounded in direct local file reads and grep, not external web results. [VERIFIED: gsd-tools research-plan] [VERIFIED: gsd-tools classify-confidence]

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - no new package or framework decision is required; local Python, pytest, PyYAML, and setup contracts were verified. [VERIFIED: python --version] [VERIFIED: codebase grep]
- Architecture: HIGH - Phase 4 context and Phase 3 implementation strongly define the module/config/test/doc pattern. [CITED: .planning/phases/04-volume-breakout/04-CONTEXT.md] [VERIFIED: marketpilot/setups/trend_pullback.py]
- Pitfalls: MEDIUM - look-ahead and side-effect risks are directly grounded in context, while some implementation failure modes are inferred and tagged as assumptions. [CITED: .planning/phases/04-volume-breakout/04-CONTEXT.md] [ASSUMED]
- Exact threshold defaults: LOW - buffer and EMA20 extension defaults are recommended planning defaults, not locked decisions. [ASSUMED]

**Research date:** 2026-06-13
**Valid until:** 2026-07-13 for codebase-local contracts, or until Phase 3 setup contracts change.
