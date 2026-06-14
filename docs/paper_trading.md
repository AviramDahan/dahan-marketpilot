# Paper Trading

SIMULATED PAPER TRADING ONLY - NOT FINANCIAL ADVICE

Phase 8 introduces Paper Trading mode contracts and QuantConnect Cloud Paper
Trading deployment prerequisites. It does not deploy algorithms, start Live
Nodes, submit orders, store credentials, create fake Paper Trading state, or
add real-money brokerage support.

## Modes

Paper modes are gated by Phase 7 activation evidence:

- `inactive`: default; no previews and no Paper orders.
- `shadow`: signal and Telegram previews only.
- `limited_paper`: eligible for capped QuantConnect Paper orders after Phase 6
  checks.
- `full_paper`: eligible for configured Phase 6 risk limits after Phase 6
  checks.

`validation_passed` alone is not Paper order approval. Limited and Full Paper
require explicit `approved_for_limited_paper` or `approved_for_full_paper`
approval states.

Limited Paper caps are:

- 0.5% per-trade risk.
- 3 maximum open Paper positions.
- 1 maximum new Paper entry per trading day.

Phase 6 allocation, sector exposure, reward/risk, stop, and target checks still
apply.

## QuantConnect Prerequisites

QuantConnect Cloud Paper Trading is the only allowed deployment target for this
phase. Required external prerequisites are:

- QuantConnect account.
- Organization access with Paper Trading capability.
- Available Paper Trading Live Node.
- QuantConnect project ID.
- QuantConnect API credentials stored outside repository files.
- Live data-provider settings appropriate for the project.

Missing prerequisites are represented as `not_configured`. A configured
operator action that has not been performed is represented as `not_run` or
`configured_operator_action_required`; it is never represented as a fake
deployment.

The repository may render this operator-run command metadata:

```text
lean cloud live deploy "$QUANTCONNECT_PROJECT_ID" --push
```

The command is documentation/operator guidance only. Automated tests must not
invoke it, start a Live Node, require credentials, or contact QuantConnect.

## Secrets

Use approved external secret stores for QuantConnect credentials. Repository
files may name required environment variables, but must never contain secret
values. Do not paste QuantConnect credentials into chat or commit them to the
repository.

## Authority

QuantConnect remains authoritative for simulated cash, portfolio equity,
holdings, open positions, orders, fills, Paper Trading state, algorithm status,
and Paper Trading performance. Local records are audit and recovery context
only.

## Reconciliation

QuantConnect Paper snapshots are the only authoritative input for simulated
cash, portfolio equity, holdings, orders, fills, deployment status, algorithm
status, and Paper performance. Deterministic tests may use fixture snapshots
only when the fixture label is explicit.

Local order intents, lifecycle events, and audit records are mirror context.
They can help identify duplicate intent generation and explain restart history,
but they never overwrite QuantConnect order IDs, fill prices, fill quantities,
portfolio cash, or holdings after submission.

When reconciliation finds a mismatch between QuantConnect and the local mirror,
the decision blocks new entries, preserves exit obligations, emits a high
severity system-domain event with a correlation ID, and requires explicit
operator recovery. Reconciliation does not call QuantConnect, Telegram, Render,
or a broker; it is a pure comparison over already-provided snapshots.
