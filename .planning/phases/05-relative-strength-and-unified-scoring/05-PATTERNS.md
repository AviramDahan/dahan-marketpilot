# Phase 05: Relative Strength and Unified Scoring - Pattern Map

**Mapped:** 2026-06-13
**Files analyzed:** 18
**Analogs found:** 18 / 18

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `marketpilot/setups/base.py` | model | request-response | `marketpilot/setups/base.py` | exact-modification |
| `marketpilot/setups/__init__.py` | config | transform | `marketpilot/setups/__init__.py` | exact-modification |
| `marketpilot/setups/relative_strength.py` | service | request-response | `marketpilot/setups/volume_breakout.py` | exact |
| `marketpilot/scoring.py` | service/model | transform | `marketpilot/setups/base.py` | role-match |
| `marketpilot/ranking.py` | service/model | transform | `marketpilot/setups/volume_breakout.py` | partial |
| `config/relative_strength.yaml` | config | transform | `config/volume_breakout.yaml` | exact |
| `config/scoring.yaml` | config | transform | `config/volume_breakout.yaml` | role-match |
| `docs/relative_strength.md` | documentation | transform | `docs/volume_breakout.md` | exact |
| `docs/scoring.md` | documentation | transform | `docs/volume_breakout.md` | role-match |
| `docs/testing.md` | documentation | transform | `docs/testing.md` | exact-modification |
| `docs/safety.md` | documentation | transform | `docs/safety.md` | exact-modification |
| `tests/test_relative_strength_contract.py` | test | request-response | `tests/test_volume_breakout_contract.py` | exact |
| `tests/test_relative_strength_detection.py` | test | request-response | `tests/test_volume_breakout_detection.py` | exact |
| `tests/test_relative_strength_rejections.py` | test | request-response | `tests/test_trend_pullback_rejections.py` | exact |
| `tests/test_relative_strength_explanations.py` | test | request-response | `tests/test_volume_breakout_detection.py` | role-match |
| `tests/test_relative_strength_safety.py` | test | transform | `tests/test_volume_breakout_safety.py` | exact |
| `tests/test_scoring.py` | test | transform | `tests/test_volume_breakout_contract.py` | role-match |
| `tests/test_ranking.py` | test | transform | `tests/test_volume_breakout_detection.py` | partial |

## Pattern Assignments

### `marketpilot/setups/relative_strength.py` (service, request-response)

**Analog:** `marketpilot/setups/volume_breakout.py`

**Imports pattern** (lines 3-18):
```python
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import isfinite
from pathlib import Path
from typing import Mapping

import yaml

from marketpilot.indicators import IndicatorResult
from marketpilot.indicators import ReadinessStatus
from marketpilot.regime import MarketRegime
from marketpilot.regime import RegimeResult
from marketpilot.setups.base import NumericEvidence, SetupRejectionReason, SetupResult, SetupStatus, SetupTiming
from marketpilot.symbol_data import SymbolData
```

**Config loader pattern** (lines 55-68):
```python
def load_volume_breakout_config(path: str | Path = DEFAULT_CONFIG_PATH) -> dict:
    with Path(path).open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    config = loaded.get("volume_breakout", loaded)
    if not isinstance(config, dict):
        raise ValueError("volume_breakout config must be a mapping.")
    if config.get("paper_trading_only") is not True:
        raise ValueError("volume_breakout config requires paper_trading_only: true.")
    if config.get("timing_mode") != "completed_daily_bar":
        raise ValueError("Volume Breakout must use completed_daily_bar timing.")
    disabled = config.get("disabled_behaviors", {})
    if disabled.get("intrabar_validity") is not False:
        raise ValueError("Volume Breakout must use completed daily bars only.")
    return config
```

**Evaluator skeleton and fail-closed readiness pattern** (lines 88-119):
```python
def evaluate_volume_breakout(
    setup_input: VolumeBreakoutInput,
    config: dict | None = None,
) -> SetupResult:
    active_config = config or load_volume_breakout_config()
    bars = setup_input.bars
    signal_time = bars[-1].time if bars else datetime.min
    evidence: list[NumericEvidence] = []
    reasons: list[SetupRejectionReason] = []

    if len(bars) < lookback_bars + 1 or any(not bar.complete for bar in bars) or any(not _valid_bar_values(bar) for bar in bars):
        reasons.append(SetupRejectionReason.INCOMPLETE_COMPLETED_BAR_DATA)
    symbol_data_ready = setup_input.symbol_data.future_signal_ready(REQUIRED_INDICATORS, stale=setup_input.symbol_data_stale)
    evidence.append(NumericEvidence("symbol_data_stale", setup_input.symbol_data_stale, False, not setup_input.symbol_data_stale))
    if not symbol_data_ready:
        reasons.append(SetupRejectionReason.DATA_NOT_READY)
    if setup_input.regime.regime is MarketRegime.RISK_OFF or not setup_input.regime.future_entries_allowed:
        reasons.append(SetupRejectionReason.RISK_OFF)
    reasons.extend(_validate_indicators(setup_input.indicators))
```

**Evidence and hard-rejection pattern** (lines 152-196):
```python
volume_ratio = latest.volume / float(setup_input.average_volume) if _positive(setup_input.average_volume) else 0.0
volume_threshold = float(volume_config["min_volume_ratio"])
evidence.append(NumericEvidence("volume_ratio", round(volume_ratio, 4), volume_threshold, volume_ratio >= volume_threshold))
if volume_ratio < volume_threshold:
    reasons.append(SetupRejectionReason.VOLUME_CONFIRMATION_WEAK)

if not isfinite(ema20_extension_pct) or ema20_extension_pct > max_ema20_extension_pct:
    reasons.append(SetupRejectionReason.EMA20_EXTENSION_EXCESSIVE)

if not average_dollar_volume_ok:
    reasons.append(SetupRejectionReason.INSUFFICIENT_DOLLAR_VOLUME)
```

**Result builder pattern** (lines 262-284):
```python
def _build_result(
    setup_input: VolumeBreakoutInput,
    signal_time: datetime,
    evidence: list[NumericEvidence],
    reasons: list[SetupRejectionReason],
) -> SetupResult:
    unique_reasons = tuple(dict.fromkeys(reasons))
    status = SetupStatus.REJECTED if unique_reasons else SetupStatus.VALID
    return SetupResult(
        setup_name=SETUP_NAME,
        symbol=setup_input.symbol_data.symbol.strip().upper(),
        status=status,
        timing=SetupTiming(signal_time=signal_time),
        evidence=tuple(evidence),
        rejection_reasons=unique_reasons,
        explanation=_explain(status, unique_reasons),
    )
```

**Indicator helpers to reuse** from `marketpilot/indicators.py` (lines 113-131):
```python
def relative_strength(symbol_returns: Sequence[float], benchmark_returns: Sequence[float], period: int) -> IndicatorResult:
    symbol = _validate_series(symbol_returns, period)
    benchmark = _validate_series(benchmark_returns, period)
    name = f"RS{period}"
    if isinstance(symbol, IndicatorResult) or isinstance(benchmark, IndicatorResult):
        return IndicatorResult(name, ReadinessStatus.NOT_READY, required_points=period, available_points=min(len(symbol_returns), len(benchmark_returns)))
    value = fmean(symbol[-period:]) - fmean(benchmark[-period:])
    return IndicatorResult(name, ReadinessStatus.READY, value, period, min(len(symbol), len(benchmark)))

def distance_from_high(values: Sequence[float], period: int = 252) -> IndicatorResult:
    checked = _validate_series(values, period)
    if isinstance(checked, IndicatorResult):
        return _rename(checked, "52W_HIGH_DISTANCE")
```

### `marketpilot/scoring.py` (service/model, transform)

**Analog:** `marketpilot/setups/base.py` plus setup evidence consumers.

**Frozen dataclass result contract** from `marketpilot/setups/base.py` (lines 38-66):
```python
@dataclass(frozen=True)
class NumericEvidence:
    name: str
    value: float | int | str | bool | None
    threshold: float | int | str | bool | None = None
    passed: bool | None = None

@dataclass(frozen=True)
class SetupResult:
    setup_name: str
    symbol: str
    status: SetupStatus
    timing: SetupTiming
    evidence: tuple[NumericEvidence, ...] = field(default_factory=tuple)
    rejection_reasons: tuple[SetupRejectionReason, ...] = field(default_factory=tuple)
    explanation: tuple[str, ...] = field(default_factory=tuple)
```

**Classification must be separate from setup modules.** Use Phase 5 labels only in scoring/ranking, not in setup evaluators. Existing setup safety tests assert setup outputs have no classification or score fields; see `tests/test_volume_breakout_safety.py` lines 38-50.

**Fail-closed input validation pattern** from `marketpilot/setups/volume_breakout.py` (lines 250-259):
```python
def _validate_indicators(indicators: Mapping[str, IndicatorResult]) -> list[SetupRejectionReason]:
    reasons: list[SetupRejectionReason] = []
    for name in REQUIRED_INDICATORS:
        result = indicators.get(name)
        if result is None or result.status is not ReadinessStatus.READY or result.value is None:
            reasons.append(SetupRejectionReason.DATA_NOT_READY)
            continue
        if isinstance(result.value, (int, float)) and not isfinite(float(result.value)):
            reasons.append(SetupRejectionReason.DATA_NOT_READY)
    return reasons
```

### `marketpilot/ranking.py` (service/model, transform)

**Analog:** `marketpilot/setups/volume_breakout.py` for immutable audit output and `tests/test_volume_breakout_detection.py` for one-result assertions.

**Use immutable audit objects and no trade fields.** Model shape should follow frozen dataclasses from `marketpilot/setups/base.py` lines 38-62. Ranking should consume `SetupResult`, keep one primary setup per symbol, retain supporting setup evidence, and never add entry, stop, target, quantity, order intent, broker, Paper deployment, or Telegram delivery fields.

**Tie-breaker inputs:** use weighted total score, confidence, risk quality score, then relative strength score per Phase 5 context. Since no ranking analog exists, implement directly from research and cover with `tests/test_ranking.py`.

### `marketpilot/setups/base.py` (model, request-response)

**Analog:** same file.

**Rejection vocabulary pattern** (lines 15-35):
```python
class SetupRejectionReason(str, Enum):
    RISK_OFF = "risk_off"
    DATA_NOT_READY = "data_not_ready"
    EMA50_BREAK = "ema50_break"
    EXCESSIVE_ATR = "excessive_atr"
    WEAK_REWARD_RISK = "weak_reward_risk"
    INCOMPLETE_COMPLETED_BAR_DATA = "incomplete_completed_bar_data"
    ...
    INSUFFICIENT_DOLLAR_VOLUME = "insufficient_dollar_volume"
    EARNINGS_RISK_CONFLICT = "earnings_risk_conflict"
    PORTFOLIO_CONFLICT = "portfolio_conflict"
```

Add only RSL-specific hard-rejection reasons that tests require, such as weak SPY RS and excessive 52-week-high distance. Do not add score/classification concepts to `SetupResult`.

### `marketpilot/setups/__init__.py` (config/export, transform)

**Analog:** same file.

**Export pattern** (lines 3-17):
```python
from marketpilot.setups.base import (
    NumericEvidence,
    SetupRejectionReason,
    SetupResult,
    SetupStatus,
    SetupTiming,
)

__all__ = [
    "NumericEvidence",
    "SetupRejectionReason",
    "SetupResult",
    "SetupStatus",
    "SetupTiming",
]
```

If exporting RSL evaluator symbols, keep imports explicit and update `__all__` with public names only.

### `config/relative_strength.yaml` and `config/scoring.yaml` (config, transform)

**Analog:** `config/volume_breakout.yaml`

**Safety-bounded config pattern** (lines 1-28):
```yaml
volume_breakout:
  paper_trading_only: true
  timing_mode: completed_daily_bar
  volume:
    average_volume_period: 20
    min_volume_ratio: 1.5
    min_dollar_volume: 20000000
  risk:
    max_atr_pct: 8.0
    max_ema20_extension_pct: 10.0
    min_reward_risk_proxy: 1.5
  deferred_gates:
    earnings_risk_source_verified: false
    portfolio_conflict_check_available: false
  disabled_behaviors:
    intrabar_validity: false
    create_orders: false
    portfolio_sizing: false
    backtest_result_creation: false
    telegram_delivery: false
    paper_deployment: false
    live_deployment: false
```

For `scoring.yaml`, include weights that total 100 and explicit unavailable/not-evaluated later-phase gates. Keep disabled behavior guardrails.

### `tests/test_relative_strength_contract.py` (test, request-response)

**Analog:** `tests/test_volume_breakout_contract.py`

**Config safety test pattern** (lines 18-35):
```python
def test_volume_breakout_config_contains_safety_bounded_defaults():
    config = load_volume_breakout_config()

    assert config["paper_trading_only"] is True
    assert config["timing_mode"] == "completed_daily_bar"
    assert config["disabled_behaviors"]["intrabar_validity"] is False
    assert config["disabled_behaviors"]["create_orders"] is False
    assert config["disabled_behaviors"]["backtest_result_creation"] is False
    assert config["disabled_behaviors"]["telegram_delivery"] is False
    assert config["disabled_behaviors"]["paper_deployment"] is False
    assert config["disabled_behaviors"]["live_deployment"] is False
```

**Contract result safety pattern** (lines 96-114):
```python
result = contract_result("msft", signal_time)

assert isinstance(result, SetupResult)
assert result.setup_name == "volume_breakout"
assert result.symbol == "MSFT"
assert result.status is SetupStatus.REJECTED
assert result.timing.timing_mode == "completed_daily_bar"
assert result.timing.uses_completed_daily_bar is True
assert result.timing.intrabar_valid is False
assert not hasattr(result, "order")
assert not hasattr(result, "quantity")
assert not hasattr(result, "portfolio_weight")
assert not hasattr(result, "classification")
assert not hasattr(result, "backtest_result")
assert not hasattr(result, "telegram_message")
```

### `tests/test_relative_strength_detection.py` (test, request-response)

**Analog:** `tests/test_volume_breakout_detection.py`

**Fixture pattern** (lines 11-59):
```python
def ready_indicator(name, value):
    return IndicatorResult(name=name, status=ReadinessStatus.READY, value=value, required_points=20, available_points=260)

def indicators(ema20=100.0, atr14=4.0):
    return {
        "EMA20": ready_indicator("EMA20", ema20),
        "ATR14": ready_indicator("ATR14", atr14),
    }

def valid_input(**overrides):
    active_indicators = overrides.pop("indicator_values", indicators())
    symbol_data = SymbolData("MSFT", "Technology", DataQualityStatus.ACCEPTED, active_indicators)
    setup_input = VolumeBreakoutInput(
        symbol_data=symbol_data,
        regime=RegimeResult(MarketRegime.RISK_ON, True, True, None, ("supportive",)),
        bars=breakout_bars(),
        indicators=active_indicators,
        average_volume=1000000,
        average_dollar_volume=30000000,
        atr_pct=4.0,
        projected_target=110.0,
    )
    return VolumeBreakoutInput(**{**setup_input.__dict__, **overrides})
```

**Valid detection assertions** (lines 66-77):
```python
result = evaluate_volume_breakout(valid_input())

assert result.status is SetupStatus.VALID
assert result.valid is True
assert result.rejection_reasons == ()
assert evidence_value(result, "prior_resistance") == 99.0
assert evidence_value(result, "volume_ratio") == 1.6
assert result.timing.uses_completed_daily_bar is True
assert result.timing.intrabar_valid is False
```

### `tests/test_relative_strength_rejections.py` (test, request-response)

**Analog:** `tests/test_trend_pullback_rejections.py`

**Rejection helper and readiness rejection pattern** (lines 54-88):
```python
def assert_rejected(setup_input, reason):
    result = evaluate_trend_pullback(setup_input)
    assert result.status is SetupStatus.REJECTED
    assert reason in result.rejection_reasons
    return result

def test_rejects_unready_or_rejected_symbol_data_and_missing_indicators():
    setup_input = valid_input()
    rejected_symbol = SymbolData("MSFT", "Technology", DataQualityStatus.REJECTED, setup_input.indicators)
    assert_rejected(TrendPullbackInput(**{**setup_input.__dict__, "symbol_data": rejected_symbol}), SetupRejectionReason.DATA_NOT_READY)

    missing = dict(setup_input.indicators)
    missing.pop("MACD")
    missing_symbol = SymbolData("MSFT", "Technology", DataQualityStatus.ACCEPTED, missing)
    assert_rejected(
        TrendPullbackInput(**{**setup_input.__dict__, "symbol_data": missing_symbol, "indicators": missing}),
        SetupRejectionReason.DATA_NOT_READY,
    )
```

**Deferred evidence, not fabricated rejection** (lines 113-117):
```python
result = evaluate_trend_pullback(valid_input())

assert SetupRejectionReason.EARNINGS_SOURCE_UNVERIFIED not in result.rejection_reasons
assert any(item.name == "earnings_source_verified" and item.value is False for item in result.evidence)
```

### `tests/test_relative_strength_safety.py`, `tests/test_scoring.py`, `tests/test_ranking.py` (test, transform)

**Analog:** `tests/test_volume_breakout_safety.py`

**Static forbidden-behavior scan pattern** (lines 9-35):
```python
ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_FILES = [
    ROOT / "marketpilot" / "setups" / "base.py",
    ROOT / "marketpilot" / "setups" / "volume_breakout.py",
]
FORBIDDEN = [
    "MarketOrder",
    "SetHoldings",
    "Liquidate",
    "send_telegram",
    "BacktestResult",
    "Paper deployment",
    "Live deployment",
    "api_key",
    "token",
    "password",
]

def test_volume_breakout_production_files_contain_no_forbidden_behavior():
    text = "\n".join(path.read_text(encoding="utf-8") for path in PRODUCTION_FILES)

    for value in FORBIDDEN:
        assert value not in text
```

For `tests/test_scoring.py`, allow classification labels in `marketpilot/scoring.py` but keep order/deployment/credential/portfolio mutation terms forbidden. For `tests/test_ranking.py`, assert one candidate per symbol, supporting setups retained, tie-break order, and Combined Swing disabled gate.

### `docs/relative_strength.md` and `docs/scoring.md` (documentation, transform)

**Analog:** `docs/volume_breakout.md`

**Documentation structure pattern** (lines 1-13, 25-50, 102-111):
```markdown
# Volume Breakout

Phase 4 implements Volume Breakout as an independently testable setup module.
It identifies completed daily-bar closes that break above prior resistance with
volume confirmation and records auditable evidence and rejection reasons.

## Contract

The setup uses completed daily bars only.

## Result Vocabulary

Volume Breakout returns setup results with:

- `valid` or `rejected` status
- numeric evidence
- rejection reasons
- completed daily timing metadata
- human-readable explanation fields

There is no BUY, WATCH, or AVOID output. There are no orders, no portfolio
sizing, no backtest result creation, no Telegram delivery, and no live or Paper
deployment behavior in Phase 4.
```

For `docs/scoring.md`, invert the classification note: classifications are permitted there, but explicitly state they are audit labels and not trade/order instructions.

### `docs/testing.md` and `docs/safety.md` (documentation, transform)

**Analog:** same files.

**Testing doc addition pattern** from `docs/testing.md` (lines 99-114):
```markdown
Phase 4 Volume Breakout tests are deterministic and offline. They verify
current-bar-excluded prior resistance, completed-close breakout confirmation,
volume confirmation, SET-04 hard gates, stale SymbolData readiness rejection,
evaluator-calculated reward/risk proxy, evidence completeness, readable
explanations, setup-only output, and forbidden behavior absence.

Current Phase 4 suites:

- `tests/test_volume_breakout_contract.py`
- `tests/test_volume_breakout_detection.py`
- `tests/test_volume_breakout_rejections.py`
- `tests/test_volume_breakout_explanations.py`
- `tests/test_volume_breakout_safety.py`
```

**Safety doc addition pattern** from `docs/safety.md` (lines 39-43):
```markdown
Volume Breakout remains setup evidence only in Phase 4. It may emit valid or
rejected setup results, numeric evidence, explanations, and rejection reasons,
but it must not contain orders, sizing, portfolio state, backtest results,
Telegram delivery, live or Paper deployment, credentials, fake performance, or
profitability claims.
```

## Shared Patterns

### Completed Daily-Bar Timing

**Source:** `marketpilot/setups/base.py` lines 38-43
**Apply to:** all setup result constructors and tests

```python
@dataclass(frozen=True)
class SetupTiming:
    signal_time: datetime
    timing_mode: str = "completed_daily_bar"
    uses_completed_daily_bar: bool = True
    intrabar_valid: bool = False
```

### Symbol Readiness And Stale Data

**Source:** `marketpilot/symbol_data.py` lines 47-67
**Apply to:** RSL evaluator and scoring required-data checks

```python
def readiness_for(self, required: list[str] | tuple[str, ...], stale: bool = False) -> IndicatorReadiness:
    if self.lifecycle_state is SymbolLifecycleState.REMOVED:
        return IndicatorReadiness.CLEANED_UP
    if self.data_quality_status is not DataQualityStatus.ACCEPTED:
        return IndicatorReadiness.DATA_QUALITY_REJECTED
    if stale:
        return IndicatorReadiness.STALE
    if self.missing_indicators(required):
        return IndicatorReadiness.MISSING
    ...
    return IndicatorReadiness.READY

def future_signal_ready(self, required: list[str] | tuple[str, ...], stale: bool = False) -> bool:
    return self.readiness_for(required, stale=stale) is IndicatorReadiness.READY
```

### Market Regime Gate

**Source:** `marketpilot/regime.py` lines 34-40 and 79-93
**Apply to:** RSL evaluator and scoring/classification gates

```python
@dataclass(frozen=True)
class RegimeResult:
    regime: MarketRegime
    future_entries_allowed: bool
    changed: bool
    previous_regime: MarketRegime | None
    reasons: tuple[str, ...]

if supportive_conditions:
    return _result(MarketRegime.RISK_ON, True, previous_regime, ("benchmarks_supportive",))
if defensive_conditions:
    return _result(MarketRegime.RISK_OFF, False, previous_regime, ("benchmarks_defensive",))
return _result(MarketRegime.NEUTRAL, True, previous_regime, ("mixed_benchmarks",))
```

### Config Safety

**Source:** `marketpilot/setups/volume_breakout.py` lines 55-68 and `config/volume_breakout.yaml` lines 20-28
**Apply to:** all new YAML configs and loaders

```python
if config.get("paper_trading_only") is not True:
    raise ValueError("volume_breakout config requires paper_trading_only: true.")
if config.get("timing_mode") != "completed_daily_bar":
    raise ValueError("Volume Breakout must use completed_daily_bar timing.")
disabled = config.get("disabled_behaviors", {})
if disabled.get("intrabar_validity") is not False:
    raise ValueError("Volume Breakout must use completed daily bars only.")
```

```yaml
disabled_behaviors:
  intrabar_validity: false
  create_orders: false
  portfolio_sizing: false
  backtest_result_creation: false
  telegram_delivery: false
  paper_deployment: false
  live_deployment: false
```

### Explanation Format

**Source:** `marketpilot/setups/volume_breakout.py` lines 281-284
**Apply to:** RSL setup explanations

```python
def _explain(status: SetupStatus, reasons: tuple[SetupRejectionReason, ...]) -> tuple[str, ...]:
    if status is SetupStatus.VALID:
        return ("Volume Breakout is valid on completed daily-bar breakout evidence.",)
    return tuple(f"Rejected: {reason.value}." for reason in reasons)
```

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| `marketpilot/scoring.py` | service/model | transform | No existing unified scoring module; use dataclass/result/evidence patterns plus Phase 5 research. |
| `marketpilot/ranking.py` | service/model | transform | No existing cross-setup ranker; use setup result contracts and direct Phase 5 tie-breaker decisions. |
| `tests/test_scoring.py` | test | transform | No scoring tests exist; adapt config contract and safety test patterns. |
| `tests/test_ranking.py` | test | transform | No ranking tests exist; adapt deterministic fixture style and one-result assertions. |

## Metadata

**Analog search scope:** `marketpilot/`, `config/`, `tests/`, `docs/`
**Files scanned:** 47 repository files
**Pattern extraction date:** 2026-06-13
