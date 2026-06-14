# Phase 6 Patterns: Portfolio Risk and Order Lifecycle

**Date:** 2026-06-14
**Status:** Planning patterns complete

## Existing Patterns To Reuse

### Safe Domain Models

- Use frozen dataclasses and string enums, following `marketpilot/models.py`,
  `marketpilot/scoring.py`, and `marketpilot/ranking.py`.
- Validate numeric inputs explicitly. Reuse `Decimal` for money/risk where exact
  accounting-like values matter.
- Keep public outputs sanitized and deterministic.

### Config Loading

- Follow `load_scoring_config()` and existing YAML loaders:
  `yaml.safe_load`, mapping validation, `paper_trading_only: true`, explicit
  disabled unsafe behavior flags, and fail-closed threshold validation.
- Config files should live under `config/`.

### Evidence And Audit

- Reuse `NumericEvidence` concepts for numeric decisions when practical.
- Preserve component evidence, reasons, explanations, and timestamps.
- Treat Phase 5 `RankedCandidate` as input evidence only, not a trade
  instruction.

### Tests

- Existing tests are deterministic pytest files under `tests/`.
- Contract tests usually verify config safety and output shape first.
- Safety tests scan production code for prohibited behavior.
- Plan execution should run targeted tests first, then `python -m pytest -q`.

### Documentation

- Keep docs in English.
- Update `docs/configuration.md`, `docs/testing.md`, and `docs/safety.md` in the
  same phase as implementation.
- Add domain docs for risk, lifecycle, exits, audit journal, recovery, and
  notification events as needed.

## Phase 6 Naming Guidance

Suggested public names:

- `RiskConfig`, `PortfolioSnapshot`, `PositionSizingDecision`,
  `RiskDecision`, `RiskRejectionReason`
- `OrderIntent`, `OrderLifecycleState`, `OrderLifecycleEvent`,
  `make_order_idempotency_key`
- `ExitPlan`, `StopModel`, `TargetModel`, `PartialExitRule`,
  `TrailingStopPolicy`, `HoldingPeriodPolicy`
- `AuditJournalRecord`, `AppendOnlyJsonlAuditJournal`
- `RecoveryDecision`, `RecoveryMismatch`, `CorporateActionPlaceholder`
- `NotificationDomainEvent`, `FakeNotificationCollector`,
  `NotificationDeduplicator`, `NotificationRateLimiter`

Names may change during execution if the local code shape suggests a clearer
fit, but the plans must preserve the Phase 6 decisions.

