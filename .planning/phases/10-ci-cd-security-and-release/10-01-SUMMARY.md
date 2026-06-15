---
phase: 10-ci-cd-security-and-release
plan: "01"
subsystem: ci
tags: [github-actions, pytest, security, quantconnect, render]
requires:
  - phase: 09-render-dashboard
    provides: "Render dashboard runtime configuration and dashboard health expectations"
provides:
  - "Pinned GitHub Actions workflows for offline tests, weekly validation, QuantConnect not_run evidence, and dashboard health"
  - "Static workflow tests for SHA pinning, least-privilege permissions, secret-free default CI, and guarded external checks"
  - "Supply-chain checkpoint record for GitHub actions and Lean CI install decision"
affects: [phase-10, ci, release, security, operations]
tech-stack:
  added: []
  patterns:
    - "GitHub Actions references use full 40-character SHA pins instead of mutable tags."
    - "External workflows record not_run evidence when prerequisites or operator approvals are absent."
key-files:
  created:
    - ".github/workflows/tests.yml"
    - ".github/workflows/quantconnect.yml"
    - ".github/workflows/weekly-validation.yml"
    - ".github/workflows/dashboard-health.yml"
    - "tests/test_ci_workflows.py"
  modified: []
key-decisions:
  - "Use full SHA pins for official GitHub-owned actions only."
  - "Do not install Lean CLI in GitHub Actions until a release operator approves pinned package execution; QuantConnect CI records not_run."
  - "Default CI remains deterministic, offline, and secret-free."
patterns-established:
  - "Workflow tests parse YAML and reject mutable action tags, third-party actions, broad permissions, and unsafe external behavior."
  - "Optional external workflows write explicit skipped or not_run evidence instead of implying success."
requirements-completed: [CI-01, CI-02, CI-06]
duration: 12min
completed: 2026-06-15
---

# Phase 10 Plan 01 Summary

**Pinned, secret-free GitHub Actions foundation with guarded external not_run evidence.**

## Performance

- **Duration:** 12 min
- **Started:** 2026-06-15T09:03:00Z
- **Completed:** 2026-06-15T09:15:31Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- Added default offline GitHub Actions pytest workflow using Python 3.11.9 and no external secrets.
- Added guarded QuantConnect workflow that records sync and cloud backtest as `not_run` until Lean package execution is separately approved.
- Added weekly offline validation and read-only dashboard health workflows with explicit `not_run` evidence for unavailable external checks.
- Added static workflow tests proving SHA-pinned official actions, least privilege, secret-free default CI, and no unsafe external commands.

## Supply-Chain Checkpoint

- `actions/checkout`: official GitHub-owned action, pinned to `df4cb1c069e1874edd31b4311f1884172cec0e10` from the `v6.0.3` tag.
- `actions/setup-python`: official GitHub-owned action, pinned to `a309ff8b426b58ec0e2a45f0f869d46889d02405` from the `v6.2.0` tag.
- `lean`: local package metadata identifies the installed package as QuantConnect LEAN CLI, but GitHub Actions install/use is intentionally disabled for this plan. QuantConnect sync/backtest remains `not_run` until a release operator approves pinned external execution.

## Files Created

- `.github/workflows/tests.yml` - Deterministic offline pytest workflow.
- `.github/workflows/quantconnect.yml` - Manual guarded QuantConnect workflow that records `not_run`.
- `.github/workflows/weekly-validation.yml` - Scheduled/manual offline validation workflow.
- `.github/workflows/dashboard-health.yml` - Guarded read-only dashboard health workflow.
- `tests/test_ci_workflows.py` - Static tests for workflow safety, pinning, permissions, and external-check behavior.

## Decisions Made

- Selected the latest verified v6 action tag commits available from the official GitHub action repositories and used full SHAs in workflow files.
- Preserved CI-02 without adding a mutable or unapproved Lean install by making QuantConnect cloud sync/backtest an explicit `not_run` workflow outcome.
- Kept dashboard health read-only with GET-only behavior and without printing the configured URL.

## Deviations from Plan

None - the plan's checkpoint path explicitly allowed preserving CI-02 with `not_run` behavior when Lean execution was not approved for CI.

## Issues Encountered

None.

## Verification

```powershell
python -m pytest tests/test_ci_workflows.py tests/test_dashboard_render_config.py -q
```

Result: 11 passed.

## User Setup Required

Optional GitHub repository secrets are required before external checks can run beyond `not_run` evidence:

- `QUANTCONNECT_USER_ID`
- `QUANTCONNECT_API_TOKEN`
- `QUANTCONNECT_PROJECT_ID`
- `DASHBOARD_HEALTH_URL`

Do not store secret values in repository files or planning artifacts.

## Next Phase Readiness

Plan 10-02 can now build security release gates on top of the pinned workflow foundation. Plan 10-03 can document CI, external `not_run` behavior, and dashboard health operations.

---
*Phase: 10-ci-cd-security-and-release*
*Completed: 2026-06-15*
