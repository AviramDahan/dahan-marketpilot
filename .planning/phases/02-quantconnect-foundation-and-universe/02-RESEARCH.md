# Phase 2 Research: QuantConnect Foundation and Universe

**Researched:** 2026-06-13
**Status:** Complete

## Scope

Phase 2 plans the verified QuantConnect/LEAN foundation for:

- current API verification and local/cloud workflow documentation;
- dynamic US equity universe and data-quality contracts;
- SymbolData lifecycle and indicator readiness;
- SPY/QQQ market regime states and tests.

No strategy signals, scoring, orders, Paper Trading deployment, Telegram delivery,
Render data integration, cloud backtests, fake results, or credentials belong in
this phase.

## Official Sources Checked

- QuantConnect LEAN CLI API Reference: `https://www.quantconnect.com/docs/v2/lean-cli/api-reference`
- QuantConnect LEAN CLI Project Management: `https://www.quantconnect.com/docs/v2/lean-cli/projects/project-management`
- QuantConnect LEAN CLI `lean cloud push`: `https://www.quantconnect.com/docs/v2/lean-cli/api-reference/lean-cloud-push`
- QuantConnect Cloud API Reference: `https://www.quantconnect.com/docs/v2/cloud-platform/api-reference`
- QuantConnect Cloud API Authentication: `https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/authentication`
- QuantConnect Cloud API Compile Create: `https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/compiling-code/create-compilation-job`
- QuantConnect Cloud API Live Create: `https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/create-live-algorithm`
- QuantConnect US Equity Requesting Data: `https://www.quantconnect.com/docs/v2/writing-algorithms/securities/asset-classes/us-equity/requesting-data`
- QuantConnect Fundamental Universes: `https://www.quantconnect.com/docs/v2/writing-algorithms/universes/equity/fundamental-universes`
- QuantConnect Historical Data History Responses: `https://www.quantconnect.com/docs/v2/writing-algorithms/historical-data/history-responses`
- QuantConnect Historical Data Common Errors: `https://www.quantconnect.com/docs/v2/writing-algorithms/historical-data/common-errors`
- QuantConnect Indicators Key Concepts: `https://www.quantconnect.com/docs/v2/writing-algorithms/indicators/key-concepts`
- QuantConnect Supported Indicators: `https://www.quantconnect.com/docs/v2/writing-algorithms/indicators/supported-indicators`
- QuantConnect Updating Indicators: `https://www.quantconnect.com/docs/v2/writing-algorithms/consolidating-data/updating-indicators`

## Findings

### LEAN And Cloud Workflow

- LEAN CLI exposes local and cloud commands including `lean build`, `lean backtest`,
  `lean cloud push`, `lean cloud backtest`, and live-management commands.
- LEAN CLI project creation can scaffold Python projects, but it requires being
  in an organization workspace and, per docs, an organization on a paid tier.
- Cloud API v2 uses `https://www.quantconnect.com/api/v2`, authenticated by user
  ID plus timestamped SHA-256 API-token hashing. Phase 2 must not store or ask
  for credentials.
- Cloud compile uses `/compile/create` with a project ID and returns a compile
  job state such as `InQueue`, `BuildSuccess`, or `BuildError`.
- Live deployment APIs require brokerage/data-provider configuration. This is
  explicitly outside Phase 2 because it would touch live/Paper deployment
  mechanics and secret-bearing broker settings.

### US Equity Data And Universe Selection

- US Equity `add_equity` creates a single subscription; dynamic equity universes
  require an equity universe or universe selection model.
- Fundamental universes use `add_universe` with a filter function receiving
  `Fundamental` objects and returning `Symbol` objects. The docs explicitly say
  not to call `add_equity` inside the filter function.
- The current fundamental universe docs say the dataset includes roughly 8,100
  tickers, including delisted companies and excluding ETFs, ADRs, and OTC.
- The legacy coarse/fine universe APIs are documented as deprecated; planners
  should prefer current fundamental universe APIs unless research during
  execution finds a safer current alternative.

### Historical Data And Readiness

- History responses can be DataFrames, Slices, or typed lists. DataFrame history
  is common in Python, but typed objects avoid unnecessary conversion when the
  goal is to warm up indicators.
- History responses are returned oldest to newest, which matters for indicator
  warm-up.
- History requests can return fewer data points than requested, especially for
  illiquid securities or unavailable pre-IPO periods.
- Indicator readiness is a documented failure mode: indicators cannot produce a
  valid value until they have enough historical data. If insufficient data is
  available, warm-up/history may not make them ready.

### Indicators And Dynamic Universe Lifecycle

- LEAN provides more than 100 built-in indicators and supports EMA, ATR, MACD,
  RSI, ROC, and other required indicator families.
- For static universes, automatic indicators are easy to create with helper
  methods. For dynamic universes, the docs recommend manual indicators plus
  consolidators, and keeping consolidator references so they can be removed when
  a security leaves the universe.
- Phase 2 should plan explicit SymbolData cleanup for removed securities and
  explicit readiness/data-quality gates before any later signal uses indicators.

## Planning Implications

- Plan 02-01 should be a documentation and verification gate. It should create
  docs that pin the official-source findings, allowed commands, and forbidden
  credential/deployment boundaries.
- Plan 02-02 should implement universe and data-quality contracts using offline
  models/tests first, plus a thin LEAN integration surface where current API
  names are documented.
- Plan 02-03 should implement SymbolData and indicator readiness using pure
  Python indicator primitives or wrappers that can be tested offline. It should
  not rely on QuantConnect runtime imports for local tests.
- Plan 02-04 should implement market-regime logic over benchmark indicator
  snapshots and keep it as a future entry gate only.

## Known Constraints

- The local environment did not have LEAN CLI available during Phase 1, so
  `lean build` may remain an external gate until the user installs and logs in.
- No credentials may be stored in repo, docs examples, tests, logs, reports, or
  planning artifacts.
- Any command not actually run must be reported as not run. No fake compile,
  cloud backtest, Paper Trading state, holdings, or performance artifacts.

## Research Execution Note

GSD plan-phase normally separates researcher, planner, and checker roles into
subagents. In this Codex session, automatic subagent spawning was not explicitly
requested by the user, so this research and planning pass was performed inline
while preserving the same artifact, source-grounding, and verification gates.
