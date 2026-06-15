# Troubleshooting

SIMULATED PAPER TRADING ONLY - NOT FINANCIAL ADVICE

Use this runbook to map symptoms to safe actions. When in doubt, record the
check as `failed`, `skipped`, or `not_run`; do not invent pass evidence.

| Symptom | Likely cause | Safe action | Prohibited action |
|---------|--------------|-------------|-------------------|
| `tests.yml` fails on dependency install | Requirements file or Python version mismatch | Re-run locally, inspect `requirements-dev.txt`, keep Python 3.11.9 in CI | Add broad internet-dependent setup or secrets to default CI |
| Workflow SHA/action check fails | Mutable action tag or unapproved action was added | Replace with approved full SHA or record a supply-chain checkpoint | Use `@vN` mutable tags |
| QuantConnect secrets are missing | GitHub Actions Secrets not configured | Record QuantConnect workflow as `not_run` | Commit credentials or paste values into logs |
| Lean package checkpoint is rejected | CLI package or version is not approved for CI | Keep QuantConnect sync/backtest as `not_run` | Install an unapproved package in Actions |
| QuantConnect sync/backtest is `not_run` | External execution prerequisites are absent | Keep offline gates active and document missing prerequisites | Claim QuantConnect validation passed |
| Dashboard health is `not_run` | `DASHBOARD_HEALTH_URL` is missing or withheld | Configure the secret externally or keep `not_run` evidence | Print the URL or call a deploy hook |
| Render dashboard is stale or unavailable | Source data unavailable, cache stale, or service cold start | Inspect read-only dashboard status and recovery docs | Use dashboard cache as authority |
| Dashboard auth fails | Password missing, wrong, or unavailable in Render | Verify `DASHBOARD_PASSWORD` in Render only | Log or commit the raw password |
| Paper state requires recovery | QuantConnect snapshot unavailable or mismatched | QuantConnect remains authoritative; block new entries and follow recovery | Promote local audit files to portfolio authority |
| Secret exposure is suspected | Token, password, URL, or credential may have leaked | Revoke/rotate externally, remove from repo history if committed, document `failed` | Reuse the exposed value |
| Fake performance artifact is suspected | Fixture/example was mistaken for real QuantConnect output | Relabel as fixture, schema, example, or `not_run` | Present invented profitability as real |

## Safe Escalation

QuantConnect remains authoritative for simulated Paper cash, equity, holdings,
orders, fills, deployment status, algorithm status, and real QuantConnect
backtest artifacts. Render and Telegram are non-authoritative. GitHub Actions
summaries are evidence records, not trading state.

If a check did not execute, use `skipped` or `not_run`.
