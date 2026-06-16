# Phase 15 Patterns: Paper Trading & Order Flow

## Boundary Rules

- `marketpilot/qc_api.py` is the only local QuantConnect REST boundary. Other modules receive a `QCApiClient` instance and must not construct QuantConnect URLs.
- `lean/main.py` is the only LEAN paper-order placement boundary. Local Python modules produce `OrderIntent` and command payloads; they do not call broker/order endpoints directly.
- QuantConnect is authoritative for paper orders, fills, portfolio state, deployment state, and algorithm state. JSONL files are audit/display mirrors only.
- Render/dashboard code stays read-only and must not import Phase 15 command submission modules.

## Data Contracts

- Every command carries `command_type="marketpilot_signal"`, `correlation_id`, `signal_id`, `idempotency_key`, `symbol`, `quantity`, `signal_time_utc`, `expires_at_utc`, `strategy_mode`, `primary_setup`, and paper-only authority fields.
- Every LEAN order generated from a command uses a compact tag format that can recover `signal_id` and `idempotency_key`.
- Every audit record in the order flow includes `source_authority="quantconnect"` when derived from QC order polling and `local_authority=false`.
- UTC timestamps are stored internally. ET conversion is display-only and not part of Phase 15 command or audit storage.

## Safety Gates

- Enforce `PAPER_TRADING_ONLY is True` at API wrapper, command builder, deployment orchestration, and LEAN receiver boundaries.
- Reject stale signals before calling `/live/commands/create`.
- Reject stale signals again inside `on_command`.
- Reject duplicate deploy and duplicate signal keys before calling QuantConnect.
- Reject duplicate signal keys again inside LEAN before placing a paper order.
- Reject unsupported command types, unsupported asset classes, zero/negative quantities, non-integer quantities, missing timestamps, malformed timestamps, and unknown order action fields.

## Test Patterns

- Use pytest with deterministic fixtures and `unittest.mock`.
- Patch `QCApiClient` methods; never contact QuantConnect in automated tests.
- Use `tmp_path` for JSONL ledgers and audit journals; never write to repo `data/` in tests.
- Extend static LEAN safety tests when controlled `market_order(..., tag=...)` is introduced, preserving bans on brokerage setup, liquidation, credentials, unsupported assets, leverage, margin, and uncontrolled order calls.
- External QuantConnect checks remain `not_run` unless a credentialed run is actually performed.

## Documentation Patterns

- Documentation may name required environment variables, but must not show or ask for secret values.
- Documentation must explicitly state simulated Paper Trading only, QuantConnect authority, local audit mirror status, and no profitability claims.
- UAT/verification artifacts must distinguish offline deterministic tests from real QuantConnect execution.
