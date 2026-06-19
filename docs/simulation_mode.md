# Simulation Mode

Dahan MarketPilot v1.1 is pivoted toward an autonomous stock scanner with an internal paper simulator.

## Product Modes

- `simulation_only`: the core MVP. It scans a deterministic stock universe, evaluates existing strategy setup rules, scores and ranks candidates, opens internal simulated trades, manages simulated positions, exports dashboard state, and emits Telegram notifications. It does not require QuantConnect.
- `qc_paper_validation`: parked optional validation mode. Existing QuantConnect Paper work is preserved for future external validation, but it is not a blocker for the simulator MVP.
- `qc_native_algorithm`: future-only mode where QuantConnect/LEAN would own selection and execution. It is not implemented in Phase 16.3.

## Safety Boundaries

- Internal simulation only.
- No real-money trading.
- No live brokerage credentials.
- No broker mutation path.
- No QuantConnect dependency in `simulation_only`.
- No dashboard order controls.
- No guaranteed-profit wording.
- Telegram delivery is informational and never controls safety logic.

## What Counts As Evidence

Every simulated trade must be traceable to:

- symbol
- strategy
- score and rank
- setup evidence
- risk decision
- entry price
- stop price
- target price
- quantity
- open time
- close time
- exit reason
- realized or unrealized P&L

The Phase 16.3 evidence gate is `scripts/phase16_3_simulation_evidence_report.py`.
It requires sanitized JSON proving:

- `product_mode=simulation_only`
- `paper_trading_only=true`
- dashboard is read-only
- dashboard mutation is disabled
- no real orders
- no QuantConnect dependency
- no live brokerage path
- no guaranteed-profit claims
- timezone-aware source timestamp
- scanner, dashboard, and Telegram-observation evidence
- no secret-like fields

## Runtime Boundary

`marketpilot.simulation_runner.run_simulation_cycle()` is the scheduler-bound
simulation runner. It reuses the existing scheduler ledger, file lock,
dependency-aware job ordering, heartbeat record, dashboard sink boundary, and
notification sink boundary. It does not use QuantConnect clients, deployment
ids, `/live/orders/read`, broker credentials, or real-order adapters.

The runner expects a scan callable that returns a sanitized simulation payload.
The payload may include scanner candidates, rejected candidates, internal
portfolio state, simulated trade records, dashboard records, and
simulation-labeled notification events.

Render uses the simulation runner for the near-term MVP worker:

```powershell
python -m marketpilot.simulation_runner scheduler
```

Local one-shot verification:

```powershell
python -m marketpilot.simulation_runner --dry-run
python -m marketpilot.simulation_runner once
```

The default simulation app builds one deterministic scan cycle from
`config/simulation_universe.yaml`, evaluates the scanner through a
simulation-only setup registry, opens at most one internal simulated position
from an accepted risk decision, publishes a dashboard payload to shared state
when `REDIS_URL` is configured, and emits simulation-labeled Telegram events
when Telegram config is present.

Worker startup runs one simulation cycle immediately, then continues on the
configured scheduler cadence. This keeps the deployed dashboard populated after
deploy even before the next scheduled market-window trigger.

## Local Verification

Run the focused Phase 16.3 suite:

```powershell
python -m pytest tests/test_product_modes.py tests/test_simulation_mode_safety.py tests/test_universe.py tests/test_universe_sources.py tests/test_scanner.py tests/test_internal_paper_simulator.py tests/test_simulation_storage.py tests/test_simulation_runner.py tests/test_dashboard_simulation_source.py tests/test_simulation_notifications.py tests/test_phase16_3_simulation_evidence_report.py tests/test_risk_contract.py tests/test_position_sizing.py tests/test_ranking.py -q
```

Run the evidence gate with a sanitized evidence JSON file:

```powershell
python scripts/phase16_3_simulation_evidence_report.py --evidence-json <path-to-simulation-evidence.json>
```

Phase 16.2 remains parked as optional QuantConnect Paper validation. Do not
mark Phase 16.2 complete from Phase 16.3 simulation evidence.
