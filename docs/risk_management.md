# Risk Management

Phase 6 risk management is paper-only domain validation. It consumes ranked
audit candidates and explicit stop/target inputs, but classifications are not
order instructions.

Defaults:

- Per-trade risk: 1% of simulated equity.
- Maximum open positions: 10.
- Maximum sector exposure: 30% of simulated equity.
- Maximum new entries per Paper trading day: 3.
- Maximum allocation per position: 15% of simulated equity.
- Minimum reward/risk: 2R.

Position sizing uses `risk_amount / stop_distance`. Missing, zero, negative, or
non-finite stop distance rejects fail-closed. If cash is insufficient, quantity
may be reduced only when minimum reward/risk and minimum quantity remain valid.

Risk decisions do not submit orders, mutate QuantConnect state, send Telegram
messages, or create fake portfolio authority.
