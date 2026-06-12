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

