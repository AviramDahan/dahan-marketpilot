# Phase 10.1 Context - Runtime Orchestrator Gap Closure

## Phase Goal

Close the milestone audit runtime integration gap by planning and implementing a safe strategy-to-paper orchestrator that connects QuantConnect-authoritative data, setup evidence, scoring/ranking, risk/order lifecycle, Paper Trading reconciliation, Telegram notification-domain events, and dashboard export evidence without adding any real-money path.

## Source Of Request

Phase 10.1 was inserted after `.planning/v1.0-MILESTONE-AUDIT.md` reported `gaps_found`. The formal Phase 9 and Phase 10 verification gaps are closed, but the milestone cannot be archived because the running system still lacks end-to-end runtime wiring.

## Audit Findings To Close

- `INT-01`: Strategy-to-paper E2E flow is not wired. Individual modules exist, but no production orchestrator connects QuantConnect data, setup evaluation, scoring/ranking, risk, order lifecycle, paper reconciliation, Telegram, and dashboard.
- `INT-02`: QuantConnect strategy runtime does not consume universe, regime, indicator, setup, MTF, scoring, risk, paper, or Telegram modules.
- `INT-03`: QuantConnect authority to dashboard runtime source has no producer/fetcher.
- `INT-04`: Backtest validation to paper mode is contract-wired but operationally `not_run`.
- `INT-05`: Telegram alert transport is implemented, but runtime signal/order event emission is absent until the orchestrator exists.

## Requirements In Scope

`QC-03`, `UNI-01..UNI-05`, `REG-01..REG-03`, `IND-01..IND-05`, `SET-01`, `SET-02`, `SET-05`, `SET-07`, `MODE-01..MODE-03`, `TF-01..TF-07`, `SCO-01..SCO-04`, `RISK-01..RISK-07`, `BT-01`, `TEL-01..TEL-03`, `DASH-04`.

## Decisions

<decisions>

- D-10.1-01 | architecture | Add a pure `marketpilot.runtime_orchestrator` service and keep QuantConnect/LEAN API access at adapter boundaries.
- D-10.1-02 | safety | Any order path remains QuantConnect Paper only, gated by validation, paper mode, reconciliation, risk, idempotency, and paper-only safety checks.
- D-10.1-03 | authority | QuantConnect remains authoritative for portfolio, cash, holdings, orders, fills, deployment status, algorithm status, Paper performance, and backtest results.
- D-10.1-04 | dashboard | Dashboard export may mirror QuantConnect-authoritative state but cannot become the authority or expose order controls.
- D-10.1-05 | notifications | Runtime may emit `NotificationDomainEvent`s, but Telegram delivery success/failure cannot affect trading, exits, reconciliation, recovery, or safety.
- D-10.1-06 | timing | Runtime signals use completed bars only and must preserve existing StrategyMode/MTF timing contracts.
- D-10.1-07 | external evidence | QuantConnect Cloud sync/live/Object Store/API checks remain `not_run` unless real external execution occurs with credentials stored outside repository files and planning artifacts.
- D-10.1-08 | scope | This phase closes integration gaps; it does not add new strategies, new scoring weights, real-money support, or performance claims.

</decisions>

## Must Haves

- Orchestrator wires existing pure modules without duplicating strategy logic in `lean/main.py`.
- LEAN bridge is thin, safety-scanned, and explicit about allowed QuantConnect API calls.
- Reconciliation mismatch blocks new entries and preserves exit/protective obligations.
- Dashboard Object Store/API export/fetch path is read-only from Render and uses approved keys/endpoints only.
- Notification emission is observable and non-authoritative.
- Tests prove the deterministic E2E path and failure modes.
- Documentation and planning artifacts distinguish passed local checks from external `not_run` checks.

## Out Of Scope

- Real-money trading or real broker adapters.
- Hidden live-money toggles.
- Leverage, margin, shorting, options, futures, crypto, Forex.
- Dashboard order controls.
- Fake portfolio, fake backtest, fake Paper state, or profitability claims.
- New setup families, arbitrary MTF weights, or scoring redesign.

## Proposed Execution Shape

Use several narrow plans rather than one huge change:

- Plan 10.1-01: Runtime contract, setup registry, and deterministic pure orchestrator skeleton.
- Plan 10.1-02: Strategy pipeline wiring from setup results through scoring/ranking/risk/order intents.
- Plan 10.1-03: LEAN bridge and static safety policy update.
- Plan 10.1-04: QuantConnect-authoritative dashboard export/source.
- Plan 10.1-05: Runtime notification events, reconciliation/paper gates, docs, verification, and audit handoff.

## Verification Expectations

- Targeted runtime orchestration tests pass.
- LEAN static safety tests pass with deliberate allowlist updates.
- Dashboard source/export tests pass.
- Notification isolation tests pass.
- Full offline pytest suite passes.
- Secret scan finds no known secret values.
