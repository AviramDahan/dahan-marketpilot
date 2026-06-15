# Operations

SIMULATED PAPER TRADING ONLY - NOT FINANCIAL ADVICE

This runbook covers local validation, GitHub Actions workflows, guarded
QuantConnect checks, weekly validation, dashboard health, and release evidence
status handling.

## Evidence Statuses

Use these statuses for every operational check:

- `passed` - The check executed and met acceptance criteria.
- `failed` - The check executed and found a blocking issue.
- `skipped` - The check was intentionally not selected for the current run.
- `not_run` - The check could not run because prerequisites, credentials,
  operator confirmation, service access, or an approved package checkpoint were
  unavailable.

Unexecuted external checks are not passed checks.

## Local Offline Tests

Run deterministic tests locally before pushing release changes:

```powershell
python -m pytest -q
```

Default tests must not require QuantConnect, Telegram, Render, broker
credentials, internet access, or real market data.

## GitHub Actions Workflows

| Workflow | Trigger | Purpose | External access |
|----------|---------|---------|-----------------|
| `tests.yml` | push, pull request | Deterministic offline pytest | None |
| `quantconnect.yml` | manual `workflow_dispatch` | Guarded QuantConnect sync/backtest evidence | `not_run` until approved |
| `weekly-validation.yml` | weekly schedule, manual | Offline weekly pytest plus external status summary | None by default |
| `dashboard-health.yml` | daily schedule, manual | Read-only dashboard health GET when configured | Render dashboard URL only |

All workflows use `permissions: contents: read` and pinned official GitHub
Actions SHAs.

## GitHub Actions Secrets

Store values only in GitHub Actions Secrets or another approved external secret
store. Repository files may name these variables but must never include values:

- `QUANTCONNECT_USER_ID`
- `QUANTCONNECT_API_TOKEN`
- `QUANTCONNECT_PROJECT_ID`
- `DASHBOARD_HEALTH_URL`
- `DASHBOARD_PASSWORD`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

## QuantConnect Workflow

`quantconnect.yml` is manually dispatched and currently records QuantConnect
sync and cloud backtest as `not_run`. The Lean package install is intentionally
disabled until a release operator approves a pinned CLI package and external
execution procedure.

Required operator confirmation for the current not-run evidence path:

```text
NOT_RUN_APPROVED
```

Do not add Paper deployment, live deployment, real broker, or order-submission
commands to this workflow.

## Weekly Validation

`weekly-validation.yml` runs the same deterministic offline tests on a Monday
schedule and by manual dispatch. It records QuantConnect and dashboard external
checks as `not_run` because weekly validation is offline by default.

## Dashboard Health

`dashboard-health.yml` runs a read-only GET against `DASHBOARD_HEALTH_URL` only
when that secret is configured. Missing URL records `not_run`. The workflow must
not print the URL, POST to Render, call a deploy hook, or mutate dashboard,
QuantConnect, Telegram, or broker state.

## Release Checklist

- Local `python -m pytest -q` has `passed`.
- GitHub `tests.yml` has `passed`.
- Security release gates have `passed`.
- QuantConnect external workflow is either real approved evidence or `not_run`.
- Dashboard health is `passed`, `skipped`, or `not_run` with reason.
- `SECURITY_REVIEW.md` and phase summaries are synchronized with the actual
  workflow behavior.
