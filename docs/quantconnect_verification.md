# QuantConnect Verification

Phase 2 uses official QuantConnect and LEAN documentation as the source contract
for future integration work. Local automated checks remain offline-first and
deterministic. External LEAN or QuantConnect checks are allowed only as explicit
verification gates and must be reported as not run when prerequisites are
missing.

## Official Sources Checked

- LEAN CLI API Reference: https://www.quantconnect.com/docs/v2/lean-cli/api-reference
- LEAN CLI Project Management: https://www.quantconnect.com/docs/v2/lean-cli/projects/project-management
- LEAN Cloud Push: https://www.quantconnect.com/docs/v2/lean-cli/api-reference/lean-cloud-push
- Cloud API Reference: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference
- Cloud API Authentication: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/authentication
- Cloud API Compile Create: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/compiling-code/create-compilation-job
- Cloud API Live Create: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/create-live-algorithm
- US Equity Requesting Data: https://www.quantconnect.com/docs/v2/writing-algorithms/securities/asset-classes/us-equity/requesting-data
- Fundamental Universes: https://www.quantconnect.com/docs/v2/writing-algorithms/universes/equity/fundamental-universes
- History Responses: https://www.quantconnect.com/docs/v2/writing-algorithms/historical-data/history-responses
- History Common Errors: https://www.quantconnect.com/docs/v2/writing-algorithms/historical-data/common-errors
- Indicator Key Concepts: https://www.quantconnect.com/docs/v2/writing-algorithms/indicators/key-concepts
- Supported Indicators: https://www.quantconnect.com/docs/v2/writing-algorithms/indicators/supported-indicators
- Updating Indicators With Consolidators: https://www.quantconnect.com/docs/v2/writing-algorithms/consolidating-data/updating-indicators
- Consolidating Data: https://www.quantconnect.com/docs/v2/writing-algorithms/consolidating-data/getting-started
- Time Period Consolidators: https://www.quantconnect.com/docs/v2/writing-algorithms/consolidating-data/consolidator-types/time-period-consolidators
- Calendar Consolidators: https://www.quantconnect.com/docs/v2/writing-algorithms/consolidating-data/consolidator-types/calendar-consolidators
- US Equity Market Hours: https://www.quantconnect.com/docs/v2/writing-algorithms/securities/asset-classes/us-equity/market-hours
- Time Modeling Periods: https://www.quantconnect.com/docs/v2/writing-algorithms/key-concepts/time-modeling/periods
- Scheduled Events: https://www.quantconnect.com/docs/v2/writing-algorithms/scheduled-events
- Warm-Up Periods: https://www.quantconnect.com/docs/v2/writing-algorithms/historical-data/warm-up-periods
- Manual Indicators: https://www.quantconnect.com/docs/v2/writing-algorithms/indicators/manual-indicators
- Research Dataset Key Concepts: https://www.quantconnect.com/docs/v2/research-environment/datasets/key-concepts

## Allowed Phase 2 API Surface

The following names are allowed as documented integration contracts for later
LEAN work:

- `add_universe` for current fundamental universe selection.
- `Fundamental` records supplied to universe filters.
- `add_equity` for explicit benchmark subscriptions such as `SPY` and `QQQ`.
- `history` for readiness and warm-up checks, with missing data treated as a
  rejection condition.
- Indicator readiness checks before any value is considered usable.
- Manual indicator and consolidator cleanup for symbols removed from dynamic
  universes.
- `lean build` as an optional external compile gate when LEAN prerequisites are
  available.
- Cloud API authentication and compile endpoints as documented references only.

## Forbidden Phase 2 Surface

Phase 2 does not require or authorize:

- Repository-stored credentials, API tokens, user IDs, brokerage settings, or
  secret examples.
- Cloud backtest execution.
- Paper Trading deployment.
- Live deployment.
- Brokerage configuration.
- Fake LEAN compile success, fake cloud backtest results, fake Paper Trading
  results, fake portfolio values, or unverified performance claims.

If LEAN CLI, Docker, `lean login`, `lean init`, or organization access is
missing, the external check is recorded as not run. It is not converted into a
pass.

## External Verification Commands

Optional local compile verification:

```powershell
lean build
```

This command may require Docker, LEAN CLI installation, `lean login`,
`lean init`, and QuantConnect organization access. Do not paste credentials into
chat, documentation, tests, logs, or repository files.

Cloud API compile verification remains documentation-only in Phase 2. The API
uses QuantConnect account credentials and timestamped request signing, so any
future automation must use approved secret stores outside the repository.

## Phase 2 Documentation Rule

Every Phase 2 artifact that mentions QuantConnect behavior must distinguish:

- Verified official source contracts.
- Local offline tests that were actually run.
- External checks that were not run.
- User-managed setup requirements.

## Phase 4.1 Multi-Timeframe Verification Rule

Before implementation uses QuantConnect multi-resolution behavior, verify the
exact current API names and semantics for source subscription resolution,
`TradeBar` consolidators, calendar/custom anchoring, `America/New_York`
exchange time, DST, regular-hours filtering, extended-hours exclusion, holidays,
early closes, warm-up, indicator readiness, and dynamic-universe consolidator
registration and cleanup.

The recommended initial 4H alignment is market-open anchored and RTH-only. A
regular US equity session is 6.5 hours, so a remaining partial-session bar must
be marked partial and must not generate signals by default. A 2H alternative may
be evaluated only if 4H is technically unsafe or too sparse; it must not replace
4H silently.
