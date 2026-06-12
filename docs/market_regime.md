# Market Regime

Phase 2 adds an offline SPY/QQQ market-regime foundation. It is an entry gate
for future new entries only. It is not a strategy signal, not an exit rule, and
not an order mechanism.

## Inputs

`config/regime.yaml` defines:

- Benchmark symbols: SPY and QQQ.
- Required EMA20, EMA50, and EMA200 values.
- Slope windows for 20-day and 60-day trend checks.
- 20-day and 60-day return inputs.
- RISK_ON, NEUTRAL, and RISK_OFF thresholds.
- `entry_gate_only: true`.
- `override_exits: false`.

## Behavior

- RISK_ON permits future new entries when both benchmarks are supportive.
- NEUTRAL is the mixed/default state and still permits future new entries.
- RISK_OFF blocks future new entries only.
- Missing or unready benchmark data blocks future new entries until readiness is
  restored.
- Unchanged regime states are suppressed so later notification phases can avoid
  duplicate messages.

There is no liquidation behavior, no forced exit behavior, no exit override, no
order behavior, and no Telegram delivery in Phase 2.

## Verification Boundary

QuantConnect remains authoritative for future paper and backtest state. Phase 2
uses offline fixtures only. Strategy consumption, notification delivery, Paper
deployment, and live deployment remain deferred to later phases.
