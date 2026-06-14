---
phase: 08-quantconnect-paper-trading-and-telegram
plan: "01"
subsystem: paper-trading
tags: [quantconnect, paper-trading, activation-gates, risk, safety, tdd]
requires:
  - phase: 07-backtesting-and-validation
    provides: "ActivationApprovalState and ValidationGateDecision contracts"
  - phase: 06-portfolio-risk-and-order-lifecycle
    provides: "Phase 6 risk limits and order-safety boundaries"
provides:
  - "Paper mode gating for inactive, shadow, limited_paper, and full_paper"
  - "Limited Paper caps stricter than Phase 6 defaults"
  - "Auditable Paper mode transition records with sanitized payloads"
  - "QuantConnect Paper Trading prerequisite and operator-command contracts"
affects: [phase-08, phase-09-dashboard, phase-10-cicd-security]
tech-stack:
  added: []
  patterns:
    - "Pure domain evaluators for Paper Trading gates"
    - "Operator-run command rendering without CLI execution"
key-files:
  created:
    - marketpilot/paper_modes.py
    - marketpilot/quantconnect_paper.py
    - config/paper_trading.yaml
    - tests/test_paper_modes.py
    - tests/test_quantconnect_paper_contract.py
    - tests/test_paper_trading_safety.py
    - docs/paper_trading.md
  modified:
    - docs/activation_gates.md
    - docs/configuration.md
    - docs/safety.md
key-decisions:
  - "validation_passed remains inactive for Paper Trading; explicit approved_for_limited_paper or approved_for_full_paper is required for Paper-order eligibility."
  - "approved_for_shadow permits previews only and cannot submit Paper orders."
  - "QuantConnect deployment is operator-run metadata only; missing prerequisites return not_configured or not_run and never fake deployment state."
patterns-established:
  - "Paper mode gates consume ValidationGateDecision directly instead of duplicating activation-gate logic."
  - "Limited Paper reuses Phase 6 risk fields with stricter caps and preserves Phase 6 checks."
requirements-completed: [TEL-01]
requirements-advanced: [TEL-02]
test-results:
  targeted: "python -m pytest tests/test_paper_modes.py tests/test_quantconnect_paper_contract.py tests/test_paper_trading_safety.py -q -> 21 passed"
  broad: "python -m pytest -q -> passed"
  static-scan: "rg real_broker/live_money/lean cloud live deploy/TELEGRAM_BOT_TOKEN/QUANTCONNECT_API_TOKEN -> only safe false flags, env-var names, tests, and documented operator-run command references"
metrics:
  duration: "10 min"
  completed: 2026-06-14
---

# Phase 08 Plan 01: Paper Trading Modes and QuantConnect Deployment Gates Summary

**Explicit Paper Trading activation modes with Limited Paper caps, transition audit records, and QuantConnect Paper deployment prerequisite contracts.**

## Performance

- **Duration:** 10 min
- **Started:** 2026-06-14T11:26:44Z
- **Completed:** 2026-06-14T11:36:47Z
- **Tasks:** 3
- **Files modified:** 10

## Accomplishments

- Added `marketpilot.paper_modes` with fail-closed mapping from Phase 7 activation states to inactive, shadow, limited Paper, and full Paper modes.
- Added Limited Paper caps: 0.5% per-trade risk, 3 max open Paper positions, and 1 max new Paper entry per day while preserving Phase 6 allocation, sector, reward/risk, stop, and target checks.
- Added immutable `PaperModeTransition` records with prior/requested/resulting modes, reason, timestamp, correlation ID, gate evidence, and secret-like payload redaction.
- Added `marketpilot.quantconnect_paper` prerequisite/status contracts for QuantConnect Paper Trading only, with `not_configured`, `not_run`, and operator-action-required states.
- Documented Paper Trading mode gates, QuantConnect prerequisites, no-secret handling, and no real-money brokerage boundary.

## Task Commits

1. **Task 1 RED:** `da1e033` test(08-01): add failing paper mode gate tests
2. **Task 1 GREEN:** `3d7aa5c` feat(08-01): implement paper mode gates
3. **Task 2 RED:** `b05e157` test(08-01): add failing paper mode transition tests
4. **Task 2 GREEN:** `a3422bc` feat(08-01): add paper mode transition records
5. **Task 3 RED:** `dba57e2` test(08-01): add failing quantconnect paper contract tests
6. **Task 3 GREEN:** `7e3c627` feat(08-01): add quantconnect paper deployment contracts

## Files Created/Modified

- `marketpilot/paper_modes.py` - Paper mode enum, config loader, eligibility decision, Limited Paper risk caps, and transition records.
- `marketpilot/quantconnect_paper.py` - QuantConnect Paper prerequisite/status types and operator command renderer.
- `config/paper_trading.yaml` - Safe default inactive Paper config with Limited Paper caps and disabled unsafe behaviors.
- `tests/test_paper_modes.py` - TDD coverage for D-01 through D-05 and transition audit behavior.
- `tests/test_quantconnect_paper_contract.py` - QuantConnect Paper deployment contract tests for D-06 through D-10.
- `tests/test_paper_trading_safety.py` - Static safety tests for no real broker, no deployment execution, and no fake deployment state.
- `docs/paper_trading.md` - Paper Trading mode and QuantConnect prerequisite documentation.
- `docs/activation_gates.md` - Paper mode mapping and transition audit documentation.
- `docs/configuration.md` - Paper Trading config documentation.
- `docs/safety.md` - QuantConnect Paper Trading safety documentation.

## Verification

- `python -m pytest tests/test_paper_modes.py -q` -> 13 passed.
- `python -m pytest tests/test_quantconnect_paper_contract.py tests/test_paper_trading_safety.py -q` -> 8 passed.
- `python -m pytest tests/test_paper_modes.py tests/test_quantconnect_paper_contract.py tests/test_paper_trading_safety.py -q` -> 21 passed.
- `python -m pytest -q` -> passed.
- `rg -n "real_broker|live_money|lean cloud live deploy|TELEGRAM_BOT_TOKEN|QUANTCONNECT_API_TOKEN" marketpilot config docs tests` -> findings were safe false flags, env-var names, tests, and documented/operator-rendered `lean cloud live deploy` text; no secret values or CLI execution path found.

## Decisions Made

- `validation_passed` remains non-Paper-eligible. Paper orders require explicit `approved_for_limited_paper` or `approved_for_full_paper`.
- Shadow mode enables previews only.
- Limited Paper uses stricter caps but still requires Phase 6 risk and exit checks.
- QuantConnect Paper deployment is represented as typed local status and operator-run command metadata only.
- TEL-02 remains partially complete: this plan covers deployment prerequisites and command contracts; reconciliation, restart recovery, and protective-order recovery remain for later Phase 8 plans.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Security] Renamed secret-like config key**
- **Found during:** Task 1
- **Issue:** `live_money_credentials: false` was rejected by the existing safety validator because keys containing `credential` are forbidden even when false.
- **Fix:** Replaced the key with `live_money_paths: false`, preserving fail-closed behavior without a secret-like repository key.
- **Files modified:** `config/paper_trading.yaml`, `marketpilot/paper_modes.py`
- **Verification:** `python -m pytest tests/test_paper_modes.py -q` passed.
- **Committed in:** `3d7aa5c`

**Total deviations:** 1 auto-fixed security adjustment.
**Impact on plan:** The adjustment strengthened compatibility with existing no-secret validation and did not expand scope.

## Issues Encountered

- `gsd-tools` was not on `PATH`; the executor used `node C:\Users\User\.codex\gsd-core\bin\gsd-tools.cjs` where SDK updates were possible.
- `state.advance-plan` and `state.add-decision` could not parse the current free-form `STATE.md`, so the required state/roadmap/requirements updates were completed manually.
- Local Python is 3.10.10 while project metadata expects Python >=3.11 for strict release validation. The full local suite still passed in this environment.

## Known Stubs

None.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: deployment_command_rendering | `marketpilot/quantconnect_paper.py` | New operator command text surface for QuantConnect Paper deployment; mitigated by returning metadata only, `executed=False`, no subprocess usage, and static tests. |

## TDD Gate Compliance

- RED commits exist for all three TDD tasks.
- GREEN commits exist after each RED commit.
- No refactor commit was needed.

## User Setup Required

External QuantConnect setup remains operator-managed outside repository files: account, organization access, Paper Trading Live Node, project ID, API credentials in approved secret stores, and data-provider settings.

## Next Phase Readiness

Plan 08-02 can build reconciliation, restart recovery, and protective-order recovery on top of the typed Paper mode decisions and QuantConnect prerequisite/status contracts. QuantConnect remains the source of truth; local state remains audit/recovery context only.

## Self-Check: PASSED

- Verified all created and modified files exist.
- Verified task commits exist: `da1e033`, `3d7aa5c`, `b05e157`, `a3422bc`, `dba57e2`, `7e3c627`.

---
*Phase: 08-quantconnect-paper-trading-and-telegram*
*Completed: 2026-06-14*
