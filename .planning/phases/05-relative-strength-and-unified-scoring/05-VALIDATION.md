---
phase: 05
slug: relative-strength-and-unified-scoring
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-13
---

# Phase 05 - Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `python -m pytest tests/test_relative_strength_contract.py tests/test_relative_strength_detection.py tests/test_relative_strength_rejections.py tests/test_relative_strength_explanations.py tests/test_relative_strength_safety.py tests/test_scoring.py tests/test_ranking.py -q` |
| **Full suite command** | `python -m pytest -q` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run the relevant targeted pytest command for the touched module.
- **After every plan wave:** Run `python -m pytest -q`.
- **Before `$gsd-verify-work`:** Full suite must be green.
- **Max feedback latency:** 10 seconds for targeted checks, 30 seconds for full suite.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | SET-05 | T-05-01 / T-05-02 | Relative Strength Leader config and contract stay paper-only, completed-bar, and setup-only. | unit/static | `python -m pytest tests/test_relative_strength_contract.py -q` | no - W0 | pending |
| 05-01-02 | 01 | 1 | SET-05 | T-05-03 / T-05-04 | RSL requires positive SPY RS20/RS60, measures QQQ as evidence only, and rejects bad structure, liquidity, ATR, high-distance, overextension, stale/unready data, and RISK_OFF. | unit | `python -m pytest tests/test_relative_strength_detection.py tests/test_relative_strength_rejections.py -q` | no - W0 | pending |
| 05-01-03 | 01 | 1 | SET-05, SET-06 | T-05-05 | RSL explanations and safety scans preserve setup-only boundaries with no orders, sizing, Paper/Live, Telegram, fake performance, or classifications inside setup modules. | unit/static/docs | `python -m pytest tests/test_relative_strength_explanations.py tests/test_relative_strength_safety.py -q` | no - W0 | pending |
| 05-02-01 | 02 | 2 | SCO-01, SCO-02, SCO-03 | T-05-06 / T-05-07 | Scoring weights total 100, shared components map setup evidence consistently, hard rejection overrides score, and required missing/invalid/stale data fails closed. | unit | `python -m pytest tests/test_scoring.py -q` | no - W0 | pending |
| 05-02-02 | 02 | 2 | SCO-02, SCO-03 | T-05-08 | Classification and confidence boundaries are configurable, tested, and do not fake unavailable portfolio or activation gates. | unit/docs | `python -m pytest tests/test_scoring.py -q` | no - W0 | pending |
| 05-03-01 | 03 | 3 | SET-06, SCO-01, SCO-02 | T-05-09 / T-05-10 | Ranking emits one audit candidate per symbol, retains supporting setups, applies tie-breakers, and never emits entry, stop, target, quantity, or order intent. | unit/static | `python -m pytest tests/test_ranking.py -q` | no - W0 | pending |
| 05-03-02 | 03 | 3 | SET-06 | T-05-11 | Combined Swing remains disabled behind readiness prerequisites and cannot become an active strategy in Phase 5. | unit/static/docs | `python -m pytest tests/test_ranking.py tests/test_relative_strength_safety.py -q` | no - W0 | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_relative_strength_contract.py` - RSL config defaults, contract shape, rejection vocabulary, and disabled behaviors.
- [ ] `tests/test_relative_strength_detection.py` - valid RSL detection, SPY hard gate, and QQQ evidence-only behavior.
- [ ] `tests/test_relative_strength_rejections.py` - weak SPY RS20/RS60, RISK_OFF, stale/unready data, bad structure, ATR, liquidity, overextension, and 52-week-distance rejection.
- [ ] `tests/test_relative_strength_explanations.py` - RSL numeric evidence and readable explanations.
- [ ] `tests/test_relative_strength_safety.py` - forbidden behavior scan and setup-only output assertions.
- [ ] `tests/test_scoring.py` - weights, component scores, hard rejection override, missing-data fail-closed behavior, classification boundaries, confidence, and unavailable gate placeholders.
- [ ] `tests/test_ranking.py` - one candidate per symbol, supporting setups, tie-breakers, Combined Swing disabled readiness gate, and no order-intent fields.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Python version alignment | Project metadata | Local default Python is 3.10.10 while `pyproject.toml` requires Python >=3.11. | Before strict release validation, run tests with Python 3.11+ or document the local execution caveat. |

All phase product behaviors are expected to have automated offline verification.

---

## Validation Sign-Off

- [ ] All tasks have automated verification or Wave 0 dependencies.
- [ ] Sampling continuity: no 3 consecutive tasks without automated verification.
- [ ] Wave 0 covers all missing test references.
- [ ] No watch-mode flags.
- [ ] Feedback latency < 30s.
- [ ] `nyquist_compliant: true` set in frontmatter after plan verification confirms coverage.

**Approval:** pending
