# Security Review

SIMULATED PAPER TRADING ONLY - NOT FINANCIAL ADVICE

Phase 10 release security review for CI/CD, guarded external checks, Render
dashboard safety, QuantConnect authority, and release evidence handling.

## Status Taxonomy

Every release check must use one of these statuses:

- `passed` - The check executed and met its acceptance criteria.
- `failed` - The check executed and found a blocking issue.
- `skipped` - The check was intentionally not selected for the current run.
- `not_run` - The check could not run because prerequisites, credentials,
  operator confirmation, service access, or an approved package checkpoint were
  unavailable.

Unexecuted external checks are not passed checks.

## Scope

| Check | Status | Evidence |
|-------|--------|----------|
| Offline pytest workflow | `passed` | `.github/workflows/tests.yml` and `tests/test_ci_workflows.py` |
| GitHub Actions SHA pinning | `passed` | Full SHA refs in all workflow `uses` statements |
| QuantConnect cloud sync/backtest workflow | `not_run` | `quantconnect.yml` records not-run evidence only |
| Dashboard health workflow | `skipped` | Runs only when `DASHBOARD_HEALTH_URL` is configured |
| Real broker and real-money path review | `passed` | Static safety tests and this review |

## Secret Handling

Repository files may name required secrets, but must never contain secret
values. Approved storage locations are GitHub Actions Secrets for workflow
values and Render environment variables for dashboard runtime values.

Secret names referenced by release docs and workflows:

- `QUANTCONNECT_USER_ID`
- `QUANTCONNECT_API_TOKEN`
- `QUANTCONNECT_PROJECT_ID`
- `DASHBOARD_HEALTH_URL`
- `DASHBOARD_PASSWORD`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

Workflow steps mask non-empty QuantConnect and dashboard values before any
external status handling. Workflows must not run `printenv`, dump environment
state, echo dashboard URLs, echo tokens, or write secret values to summaries.

## Read-only Dashboard

The Render dashboard remains password-protected and read-only. The allowed
surface is view, refresh, login, and logout. Dashboard pages must not submit,
cancel, replace, recover, approve, or modify orders. Dashboard cache and USD/NIS
display are presentation-only and cannot become accounting authority.

The dashboard health workflow uses a read-only GET request only when
`DASHBOARD_HEALTH_URL` is configured. Missing dashboard health configuration is
recorded as `not_run`, not converted into a pass.

## Real-money Trading

The repository remains simulated Paper Trading only. There is no real-money
trading path, no real broker adapter, no hidden live switch, no live-money
credential path, and no dashboard order-control path.

Forbidden release behavior includes real brokerage adapters, real-money
credentials, leverage, margin, short selling, options, futures, cryptocurrency,
Forex, manual dashboard orders, and live deployment commands.

## QuantConnect Authority

QuantConnect remains authoritative for simulated Paper cash, equity, holdings,
orders, fills, deployment status, algorithm status, and real QuantConnect
backtest artifacts. Local audit files, dashboard cache, GitHub Actions
summaries, and Telegram messages are context only.

When QuantConnect state is unavailable or mismatched, new entries remain
blocked until explicit operator recovery is completed.

## Action Supply Chain

GitHub Actions are pinned to full 40-character commit SHAs from official
GitHub-owned repositories:

- `actions/checkout`: `df4cb1c069e1874edd31b4311f1884172cec0e10`
- `actions/setup-python`: `a309ff8b426b58ec0e2a45f0f869d46889d02405`

Mutable action tags and third-party workflow actions are not allowed in Phase
10 workflows.

The local `lean` package metadata identifies the installed package as
QuantConnect LEAN CLI, but Lean package install is intentionally disabled in
GitHub Actions until a release operator approves a pinned CLI package and
external execution procedure.

## External not_run Handling

QuantConnect sync/backtest and dashboard health are guarded external checks.
They can be `passed` only after they actually run against approved external
configuration. Missing secrets, missing operator confirmation, rejected package
checkpoint, absent dashboard URL, or unavailable service access must be
recorded as `skipped` or `not_run`.

## Fake Performance And Profitability

Release artifacts must not invent performance, portfolio, or profitability
evidence. Backtest outputs must be labeled as real QuantConnect output, fixture,
schema, example, or `not_run`. Only documented real QuantConnect artifacts may
carry performance metrics.

## Release Gate Result

Current status: `passed` for offline CI/CD security gates, `not_run` for
QuantConnect external cloud sync/backtest, and conditionally `skipped` or
`not_run` for dashboard health until `DASHBOARD_HEALTH_URL` is configured.
