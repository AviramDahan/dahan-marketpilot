# Release Handoff

SIMULATED PAPER TRADING ONLY - NOT FINANCIAL ADVICE

This release handoff records the Phase 10 release gate for Dahan MarketPilot.
It is an evidence artifact, not an approval to use real-money trading.

## Status Vocabulary

- `passed` - The check executed and met acceptance criteria.
- `failed` - The check executed and found a blocking issue.
- `skipped` - The check was intentionally not selected for the current run.
- `not_run` - The check could not run because prerequisites, credentials,
  operator confirmation, service access, or an approved package checkpoint were
  unavailable.

Unexecuted external checks are not passed checks.

## Release Prerequisites

- `SECURITY_REVIEW.md` is complete and current.
- `docs/operations.md`, `docs/troubleshooting.md`, `docs/recovery.md`,
  `docs/setup.md`, `docs/testing.md`, `docs/safety.md`, and
  `docs/render_dashboard.md` are synchronized with workflow behavior.
- `LICENSE`, `NOTICE`, `THIRD_PARTY_NOTICES.md`, and `DISCLAIMER.md` are present.
- QuantConnect and Render external checks are recorded honestly as `passed`,
  `skipped`, or `not_run` according to actual execution.

## Requirement Traceability

| Requirement | Release evidence | Status |
|-------------|------------------|--------|
| CI-01 | `.github/workflows/tests.yml` and `tests/test_ci_workflows.py` verify deterministic offline CI without external secrets/services. | `passed` |
| CI-02 | `tests.yml`, `quantconnect.yml`, `weekly-validation.yml`, and `dashboard-health.yml` exist with guarded external behavior. | `passed` |
| CI-03 | `docs/operations.md`, `docs/troubleshooting.md`, `docs/setup.md`, `docs/recovery.md`, `docs/render_dashboard.md`, `docs/safety.md`, `docs/testing.md`, `docs/licensing.md`, and this handoff cover release operations. | `passed` |
| CI-04 | `SECURITY_REVIEW.md` and `tests/test_security_release_gates.py` verify secrets, read-only dashboard, no real-money path, and action supply chain. | `passed` |
| CI-05 | `tests/test_release_audit.py`, licensing guidance, disclaimer, attribution files, and artifact-safety tests verify release readiness boundaries. | `passed` |
| CI-06 | This evidence table and workflow summaries distinguish executed checks from `skipped` and `not_run` checks and include git status capture. | `passed` |

## Release Evidence

| Evidence | Command or source | Status | Notes |
|----------|-------------------|--------|-------|
| Targeted CI workflow tests | `python -m pytest tests/test_ci_workflows.py tests/test_dashboard_render_config.py -q` | `passed` | 11 checks passed during Plan 10-01. |
| Security release gates | `python -m pytest tests/test_security_release_gates.py tests/test_safety.py tests/test_dashboard_read_only.py tests/test_paper_trading_safety.py tests/test_backtest_artifact_safety.py -q` | `passed` | 28 checks passed during Plan 10-02. |
| Operations documentation checks | Inline docs assertions and `python -m pytest tests/test_project_files.py tests/test_quantconnect_verification_docs.py tests/test_dashboard_render_config.py -q` | `passed` | 13 checks passed during Plan 10-03. |
| Final release audit tests | `python -m pytest tests/test_release_audit.py tests/test_project_files.py tests/test_backtest_artifact_safety.py tests/test_security_release_gates.py tests/test_ci_workflows.py -q` | `passed` | Executed before full-suite release gate. |
| Full deterministic offline suite | `python -m pytest -q` | `passed` | 365 checks passed during Plan 10-04. |
| Git status capture | `git status --short --branch` | `passed` | Captured before the 10-04 commit: branch `master` tracking `origin/master`, with only Phase 10 release audit and planning metadata changes pending. |
| QuantConnect cloud sync/backtest | `.github/workflows/quantconnect.yml` | `not_run` | Lean package install is intentionally disabled until a release operator approves pinned external execution. |
| Dashboard health external check | `.github/workflows/dashboard-health.yml` | `skipped` | Requires externally configured `DASHBOARD_HEALTH_URL`; no dashboard health result is claimed here. |

## GitHub Workflows

- `tests.yml` - default offline pytest for push and pull request.
- `quantconnect.yml` - manual guarded QuantConnect evidence workflow; records
  sync/backtest as `not_run` until external execution is approved.
- `weekly-validation.yml` - weekly/manual deterministic offline validation.
- `dashboard-health.yml` - read-only GET check when `DASHBOARD_HEALTH_URL` is
  configured.

## Documentation Checklist

- Product purpose and safety: `README.md`, `DISCLAIMER.md`, `docs/safety.md`.
- QuantConnect responsibilities: `docs/quantconnect_verification.md`,
  `docs/operations.md`, `docs/recovery.md`.
- GitHub responsibilities: `.github/workflows/*.yml`, `docs/operations.md`,
  `docs/setup.md`, `docs/testing.md`.
- Render responsibilities: `docs/render_dashboard.md`.
- Telegram responsibilities: `docs/safety.md`, `docs/testing.md`.
- Strategy rules, scoring, risk, order lifecycle, execution assumptions,
  backtesting methodology, bias risks, and activation gates: phase docs and
  `docs/testing.md`.
- Recovery and troubleshooting: `docs/recovery.md`,
  `docs/troubleshooting.md`.
- Licensing and disclaimer: `LICENSE`, `NOTICE`, `THIRD_PARTY_NOTICES.md`,
  `docs/licensing.md`, `DISCLAIMER.md`.

## Attribution And Licensing

The project source is MIT unless a file states otherwise. Before release, review
`LICENSE`, `NOTICE`, `THIRD_PARTY_NOTICES.md`, and `docs/licensing.md`.

No direct-copy third-party source is currently recorded. Any direct-copy or
substantially adapted third-party source must update `NOTICE` and
`THIRD_PARTY_NOTICES.md` before shipping.

## Fake Performance And Profitability Audit

Release artifacts must reject fake performance, fake Backtest results, fake
Paper Trading results, fake portfolio values, and unverified profitability
claims. Backtest artifacts must be labeled as real QuantConnect output, fixture,
schema, example, or `not_run`.

This release handoff does not claim QuantConnect cloud backtest performance,
Paper Trading performance, dashboard health performance, portfolio values, or
profitability evidence beyond executed local tests.

## Limitations

- QuantConnect sync/backtest remains `not_run` until external setup and Lean CLI
  execution are explicitly approved.
- Dashboard health remains `skipped` or `not_run` unless
  `DASHBOARD_HEALTH_URL` is configured and the workflow actually runs.
- GitHub Actions Secrets values must be configured outside the repository.
- Render dashboard and Telegram delivery remain non-authoritative.
- QuantConnect remains authoritative for simulated Paper Trading state.

## User Setup Still Required

Configure optional external values only in approved secret stores:

- `QUANTCONNECT_USER_ID`
- `QUANTCONNECT_API_TOKEN`
- `QUANTCONNECT_PROJECT_ID`
- `DASHBOARD_HEALTH_URL`
- `DASHBOARD_PASSWORD`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

## Final Handoff Instructions

Before tagging or handing the project to another operator, run:

```powershell
python -m pytest -q
git status --short --branch
```

Record the actual output summary in this file or the Phase 10 summary. Failed
commands remain `failed`; missing external checks remain `skipped` or `not_run`.
