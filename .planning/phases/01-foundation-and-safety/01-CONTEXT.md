# Phase 1: Foundation and Safety - Context

**Gathered:** 2026-06-12
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 1 establishes the repository and safety foundation without implementing production trading logic, strategy entries, Paper orders, real broker paths, or fake performance artifacts.

This phase may create the project skeleton, shared package foundation, typed configuration, safety validation, deterministic unit tests, licensing/attribution files, full foundation documentation, a minimal non-trading QuantConnect algorithm that compiles, and a minimal read-only Streamlit dashboard shell. It must stop before dynamic universe selection, indicators, setups, scoring, order lifecycle, real Paper Trading deployment, Telegram delivery, or QuantConnect Cloud workflows.

</domain>

<decisions>
## Implementation Decisions

### Licensing And Attribution

- **D-01:** Use the MIT License for Dahan MarketPilot source code.
- **D-02:** Apply strict attribution discipline from day one. Phase 1 should create `NOTICE` and `THIRD_PARTY_NOTICES.md`, and document a rule that external logic may not be copied until its source, license, reuse scope, and attribution requirements are recorded.
- **D-03:** Treat QuantConnect LEAN and official QuantConnect examples as third-party Apache-2.0 sources. If substantial code is directly copied later, attribution and NOTICE handling must be updated before the commit that introduces the copied logic.

### Project Skeleton

- **D-04:** Use a planning-first skeleton. Create only files and directories that Phase 1 needs for real safety/config/tests/docs/minimal shells. Do not create a broad tree of meaningless placeholders.
- **D-05:** Use a shared package first. Put safety, configuration, FX seed logic, and domain model foundations in a shared Python package such as `marketpilot/`. Keep `lean/` and `dashboard/` as thin consumers where practical.
- **D-06:** Avoid empty production strategy modules in Phase 1. Strategy directories and modules belong in later phases when their rules are being implemented.

### Safety Configuration

- **D-07:** Use a hardcoded central constant plus validation: define `PAPER_TRADING_ONLY = True` in a central constants/safety module, and validate configuration so attempts to set paper-only behavior false fail.
- **D-08:** Fail closed for unsafe or suspicious configuration. Real broker settings, real-money credentials, live-money order support, leverage, margin, shorting, options, futures, crypto, Forex, manual dashboard order controls, or unknown safety/trading keys that imply live trading must fail validation.
- **D-09:** Unsafe configuration failures should be explicit, testable, and safe to show without leaking secrets.

### Tests

- **D-10:** Phase 1 tests should be real safety and configuration gates, not a broad placeholder suite. Cover paper-only guard, unsafe config rejection, FX seed calculation, basic domain model validation, and dashboard read-only/safety status.
- **D-11:** Phase 1 requires an actual compile check for the minimal non-trading QuantConnect algorithm. This must not require real broker credentials, Paper Trading credentials, or order submission.
- **D-12:** If LEAN compile requires external setup, Phase 1 planning should distinguish local/offline unit tests from external/manual QuantConnect or LEAN CLI verification. Credentials must not be stored in the repository or chat.

### Minimal QuantConnect Shell

- **D-13:** The minimal `QCAlgorithm` may subscribe to SPY and QQQ benchmark symbols to prove basic data/subscription compatibility and compile behavior.
- **D-14:** The minimal algorithm must not implement dynamic universe selection, production indicators, strategy signals, position sizing, orders, Paper orders, real broker setup, or live trading behavior.
- **D-15:** Empty hooks are acceptable only when they help compile or clarify lifecycle; they must not contain placeholder trading logic.

### Minimal Dashboard Shell

- **D-16:** Phase 1 dashboard is a static safety shell. It should show product name, simulated-paper-only disclaimer, read-only status, and a clear "No live data connected" or equivalent state.
- **D-17:** Do not display mock portfolio values, fake P&L, fake holdings, fake Backtest metrics, or demo trading cards in Phase 1.
- **D-18:** The dashboard shell may establish safe page structure and styling only if it reinforces read-only and paper-only behavior.

### Documentation

- **D-19:** Phase 1 must include full foundation documentation, not only code. Expected docs include `README.md`, `DISCLAIMER.md`, licensing/attribution docs, setup notes, configuration docs, testing notes, and AI collaboration/update rules.
- **D-20:** Documentation must stay synchronized with implementation. Any safety, config, QuantConnect, dashboard, testing, licensing, or setup behavior introduced in Phase 1 must be documented in the same phase.
- **D-21:** The master specification at `docs/Dahan-MarketPilot-Master-Spec.md` should change only if the user explicitly changes the product definition.

### the agent's Discretion

The user delegated attribution detail handling, minimal QuantConnect shell scope, and minimal dashboard shell scope to the agent. The locked choices are:

- Strict attribution from day one.
- Benchmark-only minimal QuantConnect shell with SPY/QQQ subscriptions and no trading logic.
- Static safety dashboard shell with no mock portfolio or fake trading data.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Scope And Safety

- `docs/Dahan-MarketPilot-Master-Spec.md` - Master product specification, safety requirements, project structure guidance, testing scope, documentation requirements, and full v1 definition of done.
- `.planning/PROJECT.md` - Core value, constraints, key decisions, unresolved decisions, and external actions required later.
- `.planning/REQUIREMENTS.md` - Phase 1 requirements: `SAF-01` through `SAF-06`, `CFG-01` through `CFG-05`, and `QC-01`.
- `.planning/ROADMAP.md` - Phase 1 goal, success criteria, and plan breakdown.
- `.planning/STATE.md` - Current project state and known blockers.

### AI And Workflow Continuity

- `AGENTS.md` - Repository instructions for agents, safety constraints, language rules, and GSD workflow enforcement.
- `docs/AI-COLLABORATION.md` - Required reading, documentation synchronization contract, commit policy, resume rules, and secret-handling rules for AI collaborators.

### Research Sources Recorded During Initialization

- `.planning/research/STACK.md` - Official source anchors and stack decisions.
- `.planning/research/ARCHITECTURE.md` - Source-of-truth architecture and component responsibilities.
- `.planning/research/PITFALLS.md` - Safety, QuantConnect, backtesting, dashboard, licensing, and operational pitfalls.
- `.planning/research/SUMMARY.md` - High-level research summary and source list.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets

- No application source code exists yet.
- Existing reusable assets are planning and documentation artifacts only: `.planning/`, `AGENTS.md`, `docs/AI-COLLABORATION.md`, and `docs/Dahan-MarketPilot-Master-Spec.md`.

### Established Patterns

- Planning artifacts are English; user communication is Hebrew.
- GSD is the source of planning workflow state.
- Commits are now approved for focused, verified units.
- Documentation synchronization is mandatory before committing.

### Integration Points

- New shared package should connect to future `lean/` and `dashboard/` shells without creating strategy or order logic.
- `AGENTS.md` and `docs/AI-COLLABORATION.md` should remain the entry points for future AI collaborators.
- `.planning/STATE.md` should be updated through `gsd-tools` when workflow state changes.

</code_context>

<specifics>
## Specific Ideas

- User chose MIT licensing.
- User chose a planning-first skeleton and shared package-first layout.
- User explicitly requested an "You choose" option in future discussion questions because some technical choices are better delegated to the agent.
- User selected a real LEAN compile requirement for the minimal non-trading `QCAlgorithm`.
- User selected full foundation documentation for Phase 1.

</specifics>

<deferred>
## Deferred Ideas

None - discussion stayed within Phase 1 scope.

</deferred>

---

*Phase: 1-Foundation and Safety*
*Context gathered: 2026-06-12*
