# Phase 05: Relative Strength and Unified Scoring - Research

**Researched:** 2026-06-13  
**Domain:** deterministic swing-setup evidence, relative strength, candidate scoring, ranking, and safety-gated classification [VERIFIED: codebase grep]  
**Confidence:** HIGH, with an environment caveat that the local default Python is 3.10 while `pyproject.toml` requires Python >=3.11 [VERIFIED: shell]

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

## Implementation Decisions

### Relative Strength Leader

- **D-01:** Relative Strength Leader operates both as an independent setup and
  as confirmation evidence for other setups. It must not create Combined Swing
  behavior in Phase 5.
- **D-02:** SPY relative strength is the hard benchmark gate. QQQ relative
  strength is always measured as numeric evidence, bonus, warning, or context,
  but weak QQQ relative strength must not reject a symbol by itself.
- **D-03:** Relative Strength Leader requires both 20-day and 60-day relative
  strength versus SPY to be positive.
- **D-04:** QQQ should be measured for every candidate, including
  non-technology and non-growth stocks, but sector relevance must not be used as
  a hard gate until sector/industry data is verified.

### MarketPilot Score

- **D-05:** MarketPilot Score is a 0-100 score using the master specification
  default weights: trend structure 25, relative strength 20, momentum 15, setup
  quality 20, volume confirmation 10, and risk quality 10. The weights must
  total 100 and be configurable/tested.
- **D-06:** All setups use the same score categories so candidates can be
  compared. Each setup may map different setup-specific evidence into those
  shared score categories.
- **D-07:** Hard rejection overrides score. Component evidence and component
  scores should be preserved where possible for audit, but final classification
  must be `REJECTED` when a hard rejection is present.
- **D-08:** Missing, invalid, or stale required scoring data fails closed. It
  must never become neutral or positive score.

### Classification And Confidence

- **D-09:** Phase 5 classifications are `BUY_CANDIDATE`, `WATCH`, `AVOID`, and
  `REJECTED`.
- **D-10:** Default classification boundaries follow the master specification:
  `BUY_CANDIDATE` requires score >= 75, confidence >= 75, hard filters passing,
  market regime permitting new positions, expected reward/risk at least 2.0,
  portfolio constraints passing, and setup approval by the strategy activation
  gate. `WATCH` covers score 60-74, strong setups awaiting confirmation, or
  valid setups not approved for Paper execution. `AVOID` covers score below 60
  without a hard rejection. `REJECTED` covers hard rejection or critical
  failure.
- **D-11:** Confidence is not a duplicate of total score. It reflects evidence
  reliability and completeness, including readiness, data quality, component
  agreement, completed daily-bar timing validity, and deferred unknowns.
- **D-12:** Phase 5 must not fake portfolio constraints or activation gates.
  Represent unavailable or not-evaluated gates explicitly. Missing later-phase
  approval gates can downgrade an otherwise strong candidate to `WATCH`, but
  must not create orders, Paper approval behavior, or live behavior.

### Setup Ranking And Combined Swing Gate

- **D-13:** Ranking should produce at most one candidate per symbol. The
  strongest setup becomes the primary setup; additional valid setups are
  retained as supporting setups, confirmations, and evidence.
- **D-14:** Score ties are broken by higher confidence, then better risk
  quality, then stronger relative strength.
- **D-15:** Combined Swing remains disabled behind an explicit readiness gate.
  It may not become active until Trend Pullback, Volume Breakout, and Relative
  Strength Leader are independently validated, each setup has independent
  backtest and out-of-sample results, score component contributions are
  understood, and combining setups does not create duplicate entries or
  overfitting.
- **D-16:** Phase 5 output should be auditable `RankedCandidate` objects with
  symbol, primary setup, supporting setups, total score, component scores,
  classification, confidence, evidence, hard rejections, timing, and
  explanation. It must not include entry, stop, target, quantity, order intent,
  or broker/Paper behavior.

### the agent's Discretion

The user delegated several choices to the agent with "you choose." The locked
agent choices are the recommended conservative options: always measure QQQ as
evidence without a QQQ hard rejection; use master specification score weights;
use shared score categories with setup-specific evidence mapping; let hard
rejection override score; fail closed on required missing/invalid/stale scoring
data; calculate confidence as evidence reliability, not score duplication; use
explicit unavailable/not-evaluated placeholders for later portfolio and
activation gates; use confidence, risk quality, and relative strength as
tie-breakers; keep Combined Swing disabled behind an explicit readiness gate;
and output audit candidates only, not trade/order objects.

### Deferred Ideas (OUT OF SCOPE)

- Full portfolio constraints, position sizing, stops, targets, orders, fills,
  exits, duplicate-order prevention, and portfolio conflict calculation remain
  deferred to Phase 6.
- Independent backtests, out-of-sample results, activation gates, and Combined
  Swing validation remain deferred to Phase 7.
- Telegram candidate and classification alerts remain deferred to notification
  phases.
- Paper Trading deployment and any approved Paper behavior remain deferred to
  Phase 8.
- Dashboard presentation of ranked candidates remains deferred to Phase 9.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SET-05 | Relative Strength Leader measures outperformance versus SPY and QQQ while enforcing healthy structure, liquidity, ATR, 52-week high proximity, and overextension limits. [VERIFIED: `.planning/REQUIREMENTS.md`] | Implement `marketpilot/setups/relative_strength.py`, `config/relative_strength.yaml`, and tests using existing `relative_strength()`, `distance_from_high()`, `SymbolData.future_signal_ready()`, and `RegimeResult.future_entries_allowed` contracts. [VERIFIED: codebase grep] |
| SET-06 | Trend Pullback, Volume Breakout, and Relative Strength Leader are implemented and validated independently before any Combined Swing strategy. [VERIFIED: `.planning/REQUIREMENTS.md`] | Keep RSL as an independent setup module and add an explicit disabled Combined Swing readiness gate; do not merge setup logic into a combined strategy. [VERIFIED: Phase 05 CONTEXT.md] |
| SCO-01 | Candidate scoring includes setup quality, trend, momentum, relative strength, volume, risk/reward, market regime, sector/portfolio fit, data quality, and earnings-risk policy. [VERIFIED: `.planning/REQUIREMENTS.md`] | Add a scoring layer that maps setup evidence into shared score categories and records unavailable later-phase gates as explicit evidence. [VERIFIED: Phase 05 CONTEXT.md] |
| SCO-02 | Every signal and rejection includes numeric evidence, component scores, total score, classification, confidence, and hard rejection reasons. [VERIFIED: `.planning/REQUIREMENTS.md`] | Produce `RankedCandidate` audit objects from `SetupResult` evidence and rejection reasons, preserving hard rejection override. [VERIFIED: `marketpilot/setups/base.py`] |
| SCO-03 | Score classifications and confidence boundaries are configurable, documented, unit-tested, and included in reports. [VERIFIED: `.planning/REQUIREMENTS.md`] | Add `config/scoring.yaml`, unit tests for boundaries/confidence, and `docs/scoring.md`; report integration remains a later phase, but report-ready fields should exist. [VERIFIED: Phase 05 CONTEXT.md] |
</phase_requirements>

## Summary

Phase 5 should add two layers, not one large strategy rewrite: a new Relative Strength Leader setup that returns `SetupResult` evidence, and a separate scoring/ranking layer that consumes all setup results. [VERIFIED: `marketpilot/setups/base.py`, Phase 05 CONTEXT.md] The existing setup modules already enforce completed daily-bar timing, readiness-first rejection, regime gating, setup evidence, and no order/deployment behavior. [VERIFIED: codebase grep]

The primary implementation path is to mirror the Trend Pullback and Volume Breakout module pattern for RSL, then add `marketpilot/scoring.py` and `marketpilot/ranking.py` as consumers of setup evidence. [VERIFIED: codebase grep] RSL should reject weak SPY RS20/RS60, bad structure, unready/stale data, RISK_OFF, excessive ATR, poor liquidity, excessive EMA20 extension, and excessive 52-week-high distance. [VERIFIED: Phase 05 CONTEXT.md; ASSUMED for exact 52-week-high default threshold]

**Primary recommendation:** implement RSL as a setup-only module first, then implement configurable MarketPilot scoring/ranking as audit-only output with explicit disabled Combined Swing readiness. [VERIFIED: Phase 05 CONTEXT.md]

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|--------------|----------------|-----------|
| Relative Strength Leader setup detection | API / Backend strategy domain | Database / Storage: none | Existing setup logic is pure Python under `marketpilot/setups/` and returns deterministic evidence, not persisted state. [VERIFIED: codebase grep] |
| Indicator readiness and missing-data failure | API / Backend strategy domain | - | `SymbolData.future_signal_ready()` and `IndicatorResult` already own readiness and invalid-value rejection. [VERIFIED: `marketpilot/symbol_data.py`, `marketpilot/indicators.py`] |
| Market regime gating | API / Backend strategy domain | - | `RegimeResult.future_entries_allowed` is an entry gate only and does not create exits or orders. [VERIFIED: `marketpilot/regime.py`, `docs/market_regime.md`] |
| MarketPilot Score and classification | API / Backend strategy domain | CDN / Static: future reports only | Scoring is deterministic business logic over setup evidence; reports/dashboard consumption is deferred. [VERIFIED: Phase 05 CONTEXT.md] |
| Candidate ranking | API / Backend strategy domain | Dashboard: future display only | Ranking should produce audit `RankedCandidate` objects without dashboard state mutation. [VERIFIED: Phase 05 CONTEXT.md] |
| Combined Swing readiness gate | API / Backend strategy domain | Validation/backtest phase | Combined Swing is disabled until independent setup validation and later backtests/OOS results exist. [VERIFIED: Phase 05 CONTEXT.md] |

## Project Constraints (from AGENTS.md)

- Communicate with the user in Hebrew, but all repository files, identifiers, docs, tests, GSD artifacts, and commit messages must be English. [VERIFIED: AGENTS.md]
- Do not modify completed phases without a change plan. [VERIFIED: AGENTS.md]
- Keep GSD planning artifacts, technical documentation, and project docs synchronized before any commit. [VERIFIED: AGENTS.md]
- Verify current official QuantConnect APIs before using them; this phase should avoid new QuantConnect API usage unless separately verified. [VERIFIED: AGENTS.md]
- Never invent backtest results, Paper Trading results, portfolio values, or profitability claims. [VERIFIED: AGENTS.md]
- Do not add real broker code, real-money credentials, leverage, margin, short selling, options, futures, crypto, dashboard order controls, Paper/Live deployment, or hidden live-trading switches. [VERIFIED: AGENTS.md]
- QuantConnect remains the source of truth for future simulated portfolio/order/backtest state. [VERIFIED: AGENTS.md]
- Telegram failures must remain independent from trading safety, and Telegram secrets must never appear in logs, docs, tests, reports, or chat. [VERIFIED: AGENTS.md]
- Core tests must be deterministic offline and must not require QuantConnect, Telegram, Render, broker credentials, internet, or real market access. [VERIFIED: AGENTS.md, docs/testing.md]
- No project-defined skills were found under `.codex/skills/` or `.agents/skills/`. [VERIFIED: shell]

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib dataclasses/enums | Python 3.11 required by project metadata; local `python` is 3.10.10 [VERIFIED: `pyproject.toml`, shell] | Immutable contracts for setup/scoring results. [VERIFIED: codebase grep] | Existing setup contracts use dataclasses and enums; keep the same pattern. [VERIFIED: `marketpilot/setups/base.py`] |
| PyYAML | Installed 6.0.3, latest 6.0.3 [VERIFIED: pip index] | Load `config/*.yaml` with safe YAML parsing. [VERIFIED: codebase grep] | Existing setup config loaders use `yaml.safe_load`. [VERIFIED: `marketpilot/setups/trend_pullback.py`, `marketpilot/setups/volume_breakout.py`] |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | Installed 7.3.1, latest 9.0.3 [VERIFIED: pip index] | Deterministic offline unit tests. [VERIFIED: docs/testing.md] | Use for RSL contract/detection/rejection/explanation/safety tests and scoring/ranking tests. [VERIFIED: existing tests] |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Custom dataclasses/enums | Pydantic models | Do not add a new dependency for internal deterministic contracts in this phase. [ASSUMED] |
| Pure Python scoring | pandas/numpy ranking | Avoid introducing data-frame dependencies before the codebase has a need; existing tests use simple fixtures. [ASSUMED] |

**Installation:**

No new packages should be installed in Phase 5. [VERIFIED: codebase grep]

**Version verification:**

```powershell
pip index versions PyYAML
pip index versions pytest
python --version
python -m pytest --version
```

The local environment has Python 3.10.10, pytest 7.3.1, and PyYAML 6.0.3; Python 3.11 is not installed through the Windows `py` launcher. [VERIFIED: shell]

## Package Legitimacy Audit

> Phase 5 should not install external packages. The audit below records existing project dependencies only. [VERIFIED: `pyproject.toml`]

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| PyYAML | PyPI | Existing project dependency; latest published 2025-09-25 [VERIFIED: package-legitimacy seam] | Unknown to seam [VERIFIED: package-legitimacy seam] | `https://pyyaml.org/` [VERIFIED: package-legitimacy seam] | SUS, reason `unknown-downloads` [VERIFIED: package-legitimacy seam] | Keep as existing dependency; do not add new dependency without checkpoint. |
| pytest | PyPI | Existing dev dependency; latest published 2026-04-07 [VERIFIED: package-legitimacy seam] | Unknown to seam [VERIFIED: package-legitimacy seam] | `https://github.com/pytest-dev/pytest` [VERIFIED: package-legitimacy seam] | SUS, reason `unknown-downloads` [VERIFIED: package-legitimacy seam] | Keep as existing dev dependency; do not upgrade during Phase 5 unless planned. |

**Packages removed due to [SLOP] verdict:** none. [VERIFIED: package-legitimacy seam]  
**Packages flagged as suspicious [SUS]:** PyYAML and pytest were flagged by the seam only because downloads were unknown, not because the packages were missing or deprecated. [VERIFIED: package-legitimacy seam]

## Architecture Patterns

### System Architecture Diagram

```text
Completed daily bars + SymbolData + indicators + RegimeResult
        |
        v
Relative Strength Leader evaluator
        | rejects unready/stale data, weak SPY RS, bad structure, RISK_OFF, risk/liquidity failures
        v
SetupResult("relative_strength_leader") with NumericEvidence
        |
        +------------------------------+
                                       v
Trend Pullback SetupResult ----> MarketPilot scoring mapper ----+
Volume Breakout SetupResult ----> shared score components ------+--> RankedCandidate
RSL confirmation evidence ------> confidence and classification -+
                                       |
                                       v
                         one primary setup per symbol
                         supporting setups retained as evidence
                                       |
                                       v
                    Combined Swing readiness gate = disabled
```

### Recommended Project Structure

```text
marketpilot/
|-- setups/
|   |-- base.py                 # extend rejection vocabulary for RSL only if needed
|   `-- relative_strength.py    # new independent RSL setup evaluator
|-- scoring.py                  # new MarketPilot Score components, classification, confidence
`-- ranking.py                  # new one-candidate-per-symbol ranking and Combined Swing gate
config/
|-- relative_strength.yaml      # new RSL thresholds and disabled behavior guardrails
`-- scoring.yaml                # new weights, classification, confidence, unavailable-gate policy
docs/
|-- relative_strength.md        # new setup documentation
`-- scoring.md                  # new scoring/ranking/classification documentation
tests/
|-- test_relative_strength_contract.py
|-- test_relative_strength_detection.py
|-- test_relative_strength_rejections.py
|-- test_relative_strength_explanations.py
|-- test_relative_strength_safety.py
|-- test_scoring.py
`-- test_ranking.py
```

All listed files are likely created or modified by Phase 5; existing docs `docs/testing.md` and `docs/safety.md` should also be updated. [VERIFIED: existing phase patterns]

### Pattern 1: Independent RSL Setup Evaluator

**What:** RSL should mirror `evaluate_trend_pullback()` and `evaluate_volume_breakout()`: accept a typed input, validate readiness/regime/indicators, append `NumericEvidence`, return `SetupResult`. [VERIFIED: codebase grep]  
**When to use:** Use for SET-05 before any unified scoring or ranking work. [VERIFIED: Phase 05 CONTEXT.md]  
**Example:**

```python
# Source: existing setup evaluator pattern in marketpilot/setups/trend_pullback.py and volume_breakout.py
if not setup_input.symbol_data.future_signal_ready(REQUIRED_INDICATORS, stale=setup_input.symbol_data_stale):
    reasons.append(SetupRejectionReason.DATA_NOT_READY)
if setup_input.regime.regime is MarketRegime.RISK_OFF or not setup_input.regime.future_entries_allowed:
    reasons.append(SetupRejectionReason.RISK_OFF)
evidence.append(NumericEvidence("spy_rs20", spy_rs20, 0.0, spy_rs20 > 0.0))
```

### Pattern 2: Evidence Mapper, Not Setup Mutation

**What:** MarketPilot scoring should consume `SetupResult.evidence` and produce component scores separately. [VERIFIED: `SetupResult` contract]  
**When to use:** Use for SCO-01/SCO-02 so Trend Pullback and Volume Breakout stay setup-only and reusable. [VERIFIED: Phase 03/04 docs]  
**Example:**

```python
# Source: recommended Phase 5 consumer pattern based on marketpilot/setups/base.py
evidence = {item.name: item for item in setup_result.evidence}
relative_strength_component = component_from_required_evidence(
    evidence,
    required_names=("spy_rs20", "spy_rs60"),
    weight=20,
)
```

### Pattern 3: Hard-Rejection Override

**What:** Any `SetupResult.rejection_reasons` must force classification `REJECTED`, even if component scores can still be calculated for audit. [VERIFIED: Phase 05 CONTEXT.md]  
**When to use:** Use for all setup results before assigning `BUY_CANDIDATE`, `WATCH`, or `AVOID`. [VERIFIED: Phase 05 CONTEXT.md]

### Pattern 4: Unavailable Later-Phase Gates

**What:** Portfolio constraints and activation gates should be explicit `not_evaluated` or `unavailable` evidence in Phase 5. [VERIFIED: Phase 05 CONTEXT.md]  
**When to use:** Use when an otherwise strong candidate cannot honestly satisfy Phase 6/7 gates. [VERIFIED: Phase 05 CONTEXT.md]

### Recommended Plan Breakdown

1. `05-01`: Add RSL config/module/tests/docs and extend rejection vocabulary only for RSL-specific hard gates. [VERIFIED: ROADMAP.md]
2. `05-02`: Add scoring config/models/component mappers/classification/confidence tests/docs. [VERIFIED: ROADMAP.md]
3. `05-03`: Add candidate ranking, one-candidate-per-symbol selection, supporting setup retention, tie-breakers, Combined Swing disabled readiness gate, and safety docs/tests. [VERIFIED: ROADMAP.md]

### Anti-Patterns to Avoid

- **Scoring inside setup evaluators:** This would break the existing Phase 3/4 boundary where setup modules emit evidence only. [VERIFIED: docs/trend_pullback.md, docs/volume_breakout.md]
- **Weak QQQ as hard rejection:** Phase 5 locked QQQ as measured context/bonus/warning, not a standalone rejection. [VERIFIED: Phase 05 CONTEXT.md]
- **Treating missing score data as neutral:** Missing/invalid/stale required scoring data must fail closed. [VERIFIED: Phase 05 CONTEXT.md]
- **Fake portfolio/activation gates:** Unavailable Phase 6/7 gates must be explicit and must not be fabricated as passed. [VERIFIED: Phase 05 CONTEXT.md]
- **Entry/stop/target/order fields in `RankedCandidate`:** Phase 5 context forbids entry, stop, target, quantity, order intent, broker/Paper behavior. [VERIFIED: Phase 05 CONTEXT.md]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Indicator readiness | New ad hoc `None`/NaN checks in scoring | `SymbolData.future_signal_ready()` and `IndicatorResult` [VERIFIED: codebase grep] | Existing readiness already handles missing, unready, invalid, stale, data-quality rejected, and cleaned-up states. [VERIFIED: `marketpilot/symbol_data.py`] |
| Setup result vocabulary | Dicts with loose status/reason strings | `SetupResult`, `NumericEvidence`, `SetupRejectionReason` [VERIFIED: `marketpilot/setups/base.py`] | Existing tests assert the contract and absence of trade fields. [VERIFIED: tests] |
| Market regime gate | New SPY/QQQ logic inside RSL/scoring | `RegimeResult.future_entries_allowed` [VERIFIED: `marketpilot/regime.py`] | Regime is already entry-gate-only and does not override exits. [VERIFIED: docs/market_regime.md] |
| YAML parsing | Custom parser or unsafe loader | `yaml.safe_load` via existing loader pattern [VERIFIED: codebase grep] | Existing config loaders fail closed on unsafe paper/timing settings. [VERIFIED: setup modules] |
| Combined Swing | A partially active combined strategy | Explicit readiness gate object/config flag [VERIFIED: Phase 05 CONTEXT.md] | Combined Swing requires independent setup backtests and OOS results, which are deferred. [VERIFIED: Phase 05 CONTEXT.md] |

**Key insight:** the custom domain logic is the scoring formula, but the contracts, readiness checks, config loading, and safety boundaries already exist; reuse them instead of creating parallel validation paths. [VERIFIED: codebase grep]

## Common Pitfalls

### Pitfall 1: Scoring Rejected Candidates As Tradable
**What goes wrong:** A high numeric score hides a hard rejection. [VERIFIED: Phase 05 CONTEXT.md]  
**Why it happens:** Component score calculation runs after a rejected setup and classification ignores `rejection_reasons`. [ASSUMED]  
**How to avoid:** Classification must check hard rejection first and return `REJECTED`. [VERIFIED: Phase 05 CONTEXT.md]  
**Warning signs:** Tests show a rejected setup with `BUY_CANDIDATE`, `WATCH`, or no hard reason. [ASSUMED]

### Pitfall 2: Turning QQQ Into An Unapproved Gate
**What goes wrong:** Non-growth/non-tech names are rejected only because QQQ RS is weak. [VERIFIED: Phase 05 CONTEXT.md]  
**Why it happens:** SPY and QQQ evidence are implemented symmetrically. [ASSUMED]  
**How to avoid:** Require positive SPY RS20/RS60, measure QQQ as evidence/bonus/warning only. [VERIFIED: Phase 05 CONTEXT.md]  
**Warning signs:** RSL rejection reasons include weak QQQ as the sole hard rejection. [ASSUMED]

### Pitfall 3: Faking Later Gates
**What goes wrong:** `BUY_CANDIDATE` appears to have passed portfolio constraints or activation gates before Phase 6/7 exists. [VERIFIED: Phase 05 CONTEXT.md]  
**Why it happens:** The master spec lists future gates in classification, but this phase cannot evaluate them honestly. [VERIFIED: master spec, Phase 05 CONTEXT.md]  
**How to avoid:** Add explicit `portfolio_gate_status="not_evaluated"` and `activation_gate_status="not_evaluated"` evidence and downgrade to `WATCH` when those are required. [VERIFIED: Phase 05 CONTEXT.md]  
**Warning signs:** Candidate output contains `portfolio_constraints_passed=True` without Phase 6 implementation. [ASSUMED]

### Pitfall 4: Leaking Order Intent Through Scoring Output
**What goes wrong:** Ranked candidates include planned entry, stop, targets, quantity, or broker/Paper fields. [VERIFIED: Phase 05 CONTEXT.md]  
**Why it happens:** The broad master spec includes future signal fields, but Phase 5 context narrows output. [VERIFIED: master spec, Phase 05 CONTEXT.md]  
**How to avoid:** Tests should assert `RankedCandidate` has no `entry`, `stop`, `target`, `quantity`, `order`, `broker`, `paper_order`, or Telegram message attributes. [ASSUMED]

### Pitfall 5: Over-Generalizing Setup Frameworks
**What goes wrong:** Existing Trend Pullback and Volume Breakout modules are refactored while adding RSL. [ASSUMED]  
**Why it happens:** Unified scoring tempts broad framework changes. [ASSUMED]  
**How to avoid:** Add RSL parallel to existing modules and add scoring as a consumer layer. [VERIFIED: existing Phase 4 decision pattern]

## Code Examples

### Score Component Contract

```python
# Source: recommended Phase 5 shape based on marketpilot/setups/base.py
@dataclass(frozen=True)
class ScoreComponent:
    name: str
    raw_score: float
    weight: float
    weighted_score: float
    evidence: tuple[NumericEvidence, ...]
    passed: bool
```

### Classification Override

```python
# Source: Phase 05 CONTEXT.md D-07/D-09/D-10
if setup_result.rejection_reasons:
    classification = CandidateClassification.REJECTED
elif unavailable_required_later_gate:
    classification = CandidateClassification.WATCH
elif total_score >= 75 and confidence >= 75:
    classification = CandidateClassification.BUY_CANDIDATE
elif total_score >= 60:
    classification = CandidateClassification.WATCH
else:
    classification = CandidateClassification.AVOID
```

### Ranking Tie-Breaker

```python
# Source: Phase 05 CONTEXT.md D-13/D-14
ranked = sorted(
    candidates,
    key=lambda item: (
        item.total_score,
        item.confidence,
        item.component_scores["risk_quality"].weighted_score,
        item.component_scores["relative_strength"].weighted_score,
    ),
    reverse=True,
)
```

## State Of The Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Trend Pullback/Volume Breakout emit setup evidence only | Phase 5 may add scoring as a separate consumer layer | Phase 5 scope [VERIFIED: ROADMAP.md] | Existing setup modules should remain setup-only. [VERIFIED: docs] |
| No classifications in setup modules | `RankedCandidate` may include `BUY_CANDIDATE`, `WATCH`, `AVOID`, `REJECTED` as audit labels | Phase 5 context [VERIFIED: Phase 05 CONTEXT.md] | Classification belongs to scoring/ranking, not setup detection. [VERIFIED: Phase 05 CONTEXT.md] |
| Combined Swing out of scope | Explicit disabled readiness gate | Phase 5 context [VERIFIED: Phase 05 CONTEXT.md] | Planner should create a gate, not a combined strategy. [VERIFIED: Phase 05 CONTEXT.md] |

**Deprecated/outdated:**

- Treating Phase 3/4 setup safety tests as permanently forbidding all classifications everywhere is outdated for Phase 5; the prohibition should remain for setup modules, while scoring/ranking modules may define classification. [VERIFIED: Phase 05 CONTEXT.md]
- Treating `AVOID` as a hard rejection is superseded by Phase 5 D-10, where `AVOID` covers score below 60 without hard rejection and `REJECTED` covers hard rejection. [VERIFIED: Phase 05 CONTEXT.md]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Do not add Pydantic/pandas/numpy for this phase. | Standard Stack | If the planner needs batch analytics later, a dependency decision may be required. |
| A2 | RSL default `max_52_week_high_distance_pct` can be set conservatively during planning because the existing config does not define an exact threshold. | Architecture Patterns | If user expects a specific threshold, tests may encode the wrong default. |
| A3 | Tests should assert no `entry`, `stop`, `target`, `quantity`, or order fields in `RankedCandidate`. | Common Pitfalls | If later phases require report placeholders, the test should permit explicit `not_evaluated` evidence but still forbid order intent. |
| A4 | Add `marketpilot/ranking.py` separate from `marketpilot/scoring.py`. | Recommended Project Structure | If the planner prefers one small module, behavior is unaffected but file layout differs. |

## Open Questions

1. **What exact default should RSL use for 52-week-high proximity?**
   - What we know: RSL must enforce 52-week-high proximity and `distance_from_high()` exists. [VERIFIED: `.planning/REQUIREMENTS.md`, `marketpilot/indicators.py`]
   - What's unclear: the master spec says "reasonably close" but does not define a numeric threshold. [VERIFIED: master spec]
   - Recommendation: planner should choose a conservative configurable default and cover it in tests; mark the threshold as a tunable research assumption. [ASSUMED]

2. **Should Phase 5 upgrade the local Python environment?**
   - What we know: `pyproject.toml` requires Python >=3.11, but only Python 3.10 is installed locally. [VERIFIED: shell]
   - What's unclear: whether the executor will have Python 3.11 available in another environment. [VERIFIED: shell]
   - Recommendation: planner should add an environment checkpoint before implementation or explicitly run with the project-approved interpreter. [ASSUMED]

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| Python | All implementation/tests | Wrong version as default | 3.10.10 [VERIFIED: shell] | Install/use Python 3.11+ before strict project execution. |
| Python 3.11 via `py -3.11` | Project metadata | No | - [VERIFIED: shell] | Use a different Python 3.11 installation path if present, otherwise install. |
| pytest | Validation | Yes | 7.3.1 [VERIFIED: shell] | Existing `python -m pytest` works in current shell. |
| PyYAML | Config loading | Yes | 6.0.3 [VERIFIED: shell] | Existing dependency already installed. |
| QuantConnect/LEAN CLI | Not required by Phase 5 offline setup/scoring tests | Not checked for this phase | - | Keep external LEAN verification deferred unless new QC APIs are used. [VERIFIED: Phase 05 scope] |

**Missing dependencies with no fallback:**

- Python 3.11+ is missing from the Windows `py` launcher, which conflicts with project metadata. [VERIFIED: shell]

**Missing dependencies with fallback:**

- No Phase 5 external service dependency is required for deterministic offline tests. [VERIFIED: docs/testing.md]

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 7.3.1 installed locally; project allows pytest >=8.0 in optional dev metadata, so local pytest is older than project metadata but current full suite passes. [VERIFIED: shell, `pyproject.toml`] |
| Config file | `pyproject.toml` [VERIFIED: codebase grep] |
| Quick run command | `python -m pytest tests/test_relative_strength_contract.py tests/test_scoring.py tests/test_ranking.py -q` [ASSUMED until files exist] |
| Full suite command | `python -m pytest -q` [VERIFIED: shell] |

### Phase Requirements To Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SET-05 | RSL detects SPY RS20/RS60 positive, measures QQQ, enforces structure/liquidity/ATR/high-proximity/extension. [VERIFIED: requirements/context] | unit | `python -m pytest tests/test_relative_strength_detection.py tests/test_relative_strength_rejections.py -q` | No - Wave 0 |
| SET-06 | All three setups stay independently valid and Combined Swing remains disabled. [VERIFIED: requirements/context] | unit/safety | `python -m pytest tests/test_relative_strength_safety.py tests/test_ranking.py -q` | No - Wave 0 |
| SCO-01 | Shared score categories map setup evidence into trend, RS, momentum, setup quality, volume, and risk quality. [VERIFIED: context] | unit | `python -m pytest tests/test_scoring.py -q` | No - Wave 0 |
| SCO-02 | Ranked candidate output includes evidence, component scores, total score, classification, confidence, and hard rejection reasons. [VERIFIED: requirements/context] | unit | `python -m pytest tests/test_scoring.py tests/test_ranking.py -q` | No - Wave 0 |
| SCO-03 | Classification and confidence boundaries are configurable, documented, and tested. [VERIFIED: requirements/context] | unit/docs | `python -m pytest tests/test_scoring.py -q` | No - Wave 0 |

### Sampling Rate

- **Per task commit:** `python -m pytest tests/test_relative_strength_contract.py tests/test_relative_strength_detection.py tests/test_relative_strength_rejections.py tests/test_relative_strength_explanations.py tests/test_relative_strength_safety.py tests/test_scoring.py tests/test_ranking.py -q` [ASSUMED until files exist]
- **Per wave merge:** `python -m pytest -q` [VERIFIED: shell]
- **Phase gate:** full suite green plus static safety scan for no orders, no sizing, no portfolio mutation, no Telegram delivery, no Paper/Live deployment, no fake performance, and no entry/stop/target/order intent in Phase 5 modules. [VERIFIED: project constraints; ASSUMED for exact scan list]

### Wave 0 Gaps

- [ ] `tests/test_relative_strength_contract.py` - covers config defaults, RSL contract, rejection vocabulary, disabled behaviors. [ASSUMED]
- [ ] `tests/test_relative_strength_detection.py` - covers valid RSL detection and QQQ evidence-only behavior. [ASSUMED]
- [ ] `tests/test_relative_strength_rejections.py` - covers weak SPY RS20/RS60, RISK_OFF, stale/unready data, bad structure, ATR, liquidity, overextension, 52-week distance. [ASSUMED]
- [ ] `tests/test_relative_strength_explanations.py` - covers numeric evidence and readable rejection explanations. [ASSUMED]
- [ ] `tests/test_relative_strength_safety.py` - covers forbidden behavior absence and setup-only output. [ASSUMED]
- [ ] `tests/test_scoring.py` - covers weights total 100, component scores, hard rejection override, classification boundaries, confidence. [ASSUMED]
- [ ] `tests/test_ranking.py` - covers one candidate per symbol, supporting setups, tie-breakers, Combined Swing disabled readiness gate. [ASSUMED]

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | no | No auth surface in this backend scoring phase. [VERIFIED: Phase 05 scope] |
| V3 Session Management | no | No session surface in this backend scoring phase. [VERIFIED: Phase 05 scope] |
| V4 Access Control | yes | Preserve paper-only/read-only boundaries; do not add order/deployment authority. [VERIFIED: AGENTS.md] |
| V5 Input Validation | yes | Fail closed on YAML config, indicator readiness, missing/invalid/stale data, and hard rejection reasons. [VERIFIED: codebase grep] |
| V6 Cryptography | no | No cryptography or secret handling should be added. [VERIFIED: Phase 05 scope] |

### Known Threat Patterns For This Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Unsafe config silently enables forbidden behavior | Tampering | Config loaders must require `paper_trading_only: true` and disabled order/deployment flags. [VERIFIED: existing setup config loaders] |
| Fake performance or portfolio state sneaks into ranking output | Spoofing/Tampering | Tests must assert no fake backtest, portfolio values, Paper deployment, or profitability claims. [VERIFIED: AGENTS.md, docs/safety.md] |
| Secret-like fields in docs/tests | Information Disclosure | Do not add credentials, tokens, passwords, API keys, or account identifiers. [VERIFIED: AGENTS.md] |
| Order intent through audit objects | Elevation of Privilege | `RankedCandidate` must not include entry, stop, target, quantity, order, broker, Paper, or live deployment fields. [VERIFIED: Phase 05 CONTEXT.md] |

## Sources

### Primary (HIGH confidence)

- `.planning/phases/05-relative-strength-and-unified-scoring/05-CONTEXT.md` - locked Phase 5 decisions and boundaries. [VERIFIED: codebase grep]
- `.planning/REQUIREMENTS.md` - SET-05, SET-06, SCO-01, SCO-02, SCO-03. [VERIFIED: codebase grep]
- `.planning/ROADMAP.md` - Phase 5 goal, success criteria, and plan breakdown. [VERIFIED: codebase grep]
- `marketpilot/setups/base.py` - `SetupResult`, `SetupTiming`, `NumericEvidence`, `SetupRejectionReason`. [VERIFIED: codebase grep]
- `marketpilot/setups/trend_pullback.py` and `marketpilot/setups/volume_breakout.py` - existing setup evaluator pattern. [VERIFIED: codebase grep]
- `marketpilot/indicators.py` - `relative_strength()`, `distance_from_high()`, readiness helpers. [VERIFIED: codebase grep]
- `marketpilot/symbol_data.py` - readiness and stale-data handling. [VERIFIED: codebase grep]
- `marketpilot/regime.py` and `docs/market_regime.md` - entry-gate-only market regime behavior. [VERIFIED: codebase grep]
- `docs/testing.md`, `docs/safety.md`, `docs/trend_pullback.md`, `docs/volume_breakout.md` - testing and safety patterns. [VERIFIED: codebase grep]

### Secondary (MEDIUM confidence)

- `pip index versions PyYAML` and `pip index versions pytest` - registry version visibility for existing dependencies. [VERIFIED: pip index]
- `gsd-tools package-legitimacy check --ecosystem pypi PyYAML pytest` - seam verdicts for existing dependencies. [VERIFIED: package-legitimacy seam]

### Tertiary (LOW confidence)

- Research-plan websearch returned irrelevant generic results for internal project questions; no external web result was used for implementation decisions. [VERIFIED: websearch]

## Metadata

**Confidence breakdown:**

- Standard stack: MEDIUM - existing dependencies and versions were verified, but package-legitimacy seam returned SUS for unknown downloads and local Python is below project metadata. [VERIFIED: shell]
- Architecture: HIGH - based on current codebase contracts and locked Phase 5 context. [VERIFIED: codebase grep]
- Pitfalls: HIGH for boundary risks from project constraints, MEDIUM for implementation warning signs. [VERIFIED: AGENTS.md; ASSUMED for some warning signs]

**Research date:** 2026-06-13  
**Valid until:** 2026-07-13 for internal architecture; re-check package/runtime versions before dependency or environment changes. [ASSUMED]
