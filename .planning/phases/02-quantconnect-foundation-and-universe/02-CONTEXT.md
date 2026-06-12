# Phase 2: QuantConnect Foundation and Universe - Context

**Gathered:** 2026-06-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 2 builds the verified QuantConnect/LEAN foundation for data, dynamic universe selection, data quality, SymbolData lifecycle, required indicator readiness, and SPY/QQQ market regime.

This phase must verify current official QuantConnect and LEAN APIs before dependent implementation code uses them. It may introduce universe, data-quality, indicator, SymbolData, and regime foundations, but it must not implement strategy setup signals, BUY/WATCH/AVOID classifications, scoring, portfolio sizing, order submission, Paper Trading deployment, Telegram delivery, Render dashboard data integration, cloud backtest execution, or fake performance artifacts.

</domain>

<decisions>
## Implementation Decisions

### QuantConnect And LEAN Verification

- **D-01:** Use a documented verification gate as the first Phase 2 work item. Official QuantConnect/LEAN documentation, current API names, project structure, and compile path must be verified before later Phase 2 implementation depends on them.
- **D-02:** Keep automated verification offline-first where possible. Unit/static tests must remain deterministic and must not require QuantConnect credentials, Telegram, Render, broker credentials, internet, or real market data.
- **D-03:** Treat real LEAN compile and any QuantConnect Cloud workflow as external/manual gates when local setup is available. Missing LEAN CLI/Docker/login is not a reason to fabricate success.
- **D-04:** Phase 2 may verify and document QuantConnect Cloud API and LEAN CLI workflows, but must not require credentials and must not run cloud backtests or Paper Trading deployments.

### Dynamic Universe Scope

- **D-05:** Build the full Phase 2 universe and data-quality foundation without strategy signals or scoring. The foundation should cover dynamic universe contracts, filters, exclusions, data-quality status, counts, additions/removals, sector distribution where available, and update timestamps.
- **D-06:** Universe data-quality rules should be strict. Required criteria such as US common equity scope, minimum price, history availability, volume/dollar-volume, configurable minimum market capitalization, tradability, stale data, and critical missing data should reject symbols when not satisfied.
- **D-07:** Do not silently reduce the universe to a tiny or hand-written list. Any fallback, truncation, unavailable field, or unsupported filter must be explicit, documented, and tested.

### SymbolData And Indicator Readiness

- **D-08:** Use a readiness-first SymbolData boundary. SymbolData should own per-symbol indicators, data-quality state, readiness checks, and cleanup when securities leave the universe.
- **D-09:** Indicator readiness must be explicit. Missing, invalid, infinite, stale, or NaN values must reject future signal eligibility and must never become a default positive score.
- **D-10:** Build the full Phase 2 indicator foundation needed by requirements: trend, momentum, volume, risk/volatility, relative strength, and benchmark/regime indicators. The foundation must not emit strategy classifications or trade recommendations.

### Market Regime Boundary

- **D-11:** Implement SPY/QQQ market regime as a future entry gate only. `RISK_OFF` may block future new long entries, and `NEUTRAL` may later tighten thresholds or sizing, but Phase 2 must not create liquidation behavior and must not override exit rules.
- **D-12:** Market regime states and thresholds must be configurable, documented, and unit-tested. The phase should include RISK_ON, NEUTRAL, RISK_OFF, transition behavior, and unchanged-state suppression where applicable.
- **D-13:** Do not add Telegram regime alerts in Phase 2. Alert delivery belongs to later notification phases; Phase 2 can define regime events or state needed later only if it does not send messages.

### Documentation And Handoff

- **D-14:** Documentation must be updated in the same phase for every new contract: LEAN/QuantConnect verification, universe selection, data quality, SymbolData, indicator readiness, market regime, setup prerequisites, and deferred boundaries.
- **D-15:** Keep future AI collaborators synchronized. Phase 2 plans and docs must clearly state what was verified, what was not run, what requires user setup, and which official sources were used.

### the agent's Discretion

The user selected the recommended option for each discussed area. No Phase 2 gray area was delegated to open-ended agent discretion beyond routine implementation details.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Scope And Safety

- `docs/Dahan-MarketPilot-Master-Spec.md` - Master product specification, including Phase 2 universe, indicator, regime, source-of-truth, and official-source requirements.
- `.planning/PROJECT.md` - Core value, constraints, key decisions, unresolved QuantConnect decisions, and external actions required later.
- `.planning/REQUIREMENTS.md` - Phase 2 requirement IDs: `QC-02`, `QC-03`, `QC-04`, `UNI-01` through `UNI-05`, `REG-01` through `REG-03`, and `IND-01` through `IND-05`.
- `.planning/ROADMAP.md` - Phase 2 goal, success criteria, and planned plan breakdown.
- `.planning/STATE.md` - Current project state, blockers, and Phase 2 focus.

### Prior Phase Foundation

- `.planning/phases/01-foundation-and-safety/01-CONTEXT.md` - Locked Phase 1 decisions about paper-only safety, shared package layout, minimal LEAN shell, static dashboard shell, and documentation synchronization.
- `.planning/phases/01-foundation-and-safety/01-VERIFICATION.md` - Phase 1 verification result and known external LEAN compile limitation.
- `.planning/phases/01-foundation-and-safety/01-04-USER-SETUP.md` - External LEAN CLI/Docker/login setup requirements.

### Existing Code And Docs

- `AGENTS.md` - Repository instructions, safety constraints, language rules, and GSD workflow enforcement.
- `docs/AI-COLLABORATION.md` - Documentation synchronization contract, commit policy, resume rules, and secret-handling rules.
- `docs/setup.md` - Existing local setup and LEAN prerequisite notes.
- `docs/testing.md` - Existing offline test policy and optional LEAN compile boundary.
- `docs/safety.md` - Paper-only safety, QuantConnect source-of-truth, Render read-only, and Telegram non-authoritative rules.
- `lean/main.py` - Current minimal benchmark-only LEAN shell.
- `marketpilot/constants.py` - Central paper-only guard and disclaimer.
- `marketpilot/safety.py` - Existing fail-closed safety validation pattern.
- `marketpilot/configuration.py` - Existing safe YAML loading pattern.
- `marketpilot/models.py` - Existing Phase 1-safe foundational model primitives.
- `tests/test_lean_static_safety.py` - Current static LEAN no-order safety checks.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets

- `lean/main.py` provides a minimal `QCAlgorithm` shell with SPY/QQQ benchmark subscriptions and no order calls.
- `marketpilot/constants.py` provides `PAPER_TRADING_ONLY` and the required disclaimer.
- `marketpilot/safety.py` provides a sanitized fail-closed validation style that Phase 2 config/data-quality validation should preserve.
- `marketpilot/configuration.py` provides the safe YAML loading pattern through `yaml.safe_load`.
- `marketpilot/models.py` provides safe primitives such as `Money`, `FxSeed`, `SafetyStatus`, `ReadOnlyStatus`, and `ValidationIssue`.
- `tests/test_lean_static_safety.py` and `tests/test_project_files.py` show the static guardrail testing pattern to extend.

### Established Patterns

- Project files, code, tests, docs, GSD artifacts, and commit messages are English; user chat is Hebrew.
- Focused commits are approved for completed, verified units.
- Documentation must be synchronized with implementation in the same change.
- Tests should be deterministic and offline unless an external setup gate is explicitly documented.
- QuantConnect is authoritative for future paper/backtest state; Render and local files must not become hidden portfolio state.

### Integration Points

- New Phase 2 shared code should live under `marketpilot/` and keep `lean/` as a thin consumer where practical.
- New tests should extend the existing `tests/` pytest suite.
- Setup/testing docs should record official-source verification and any commands that were not run.
- Phase 2 must update planning artifacts and project docs before commit.

</code_context>

<specifics>
## Specific Ideas

- User chose a documented LEAN/API verification gate first.
- User chose a full universe/data-quality foundation rather than a minimal slice.
- User chose strict data-quality rejection for critical missing/stale/invalid fields.
- User chose readiness-first `SymbolData`.
- User chose a full indicator foundation without strategy classifications.
- User chose market regime as a gate for future entries only, not liquidation or exit override behavior.
- User chose offline-first automated tests with optional external LEAN verification when setup exists.
- User chose synchronized documentation for all new Phase 2 contracts.
- User chose QuantConnect Cloud API verification/documentation only in Phase 2, with no credentials, cloud backtest, or Paper deployment.
- User requested future text-mode choice blocks in Hebrew use a stable code-block format with `[A]`, `[B]`, `[C]` labels because RTL numbering/letters were visually unstable.

</specifics>

<deferred>
## Deferred Ideas

- QuantConnect Cloud backtest execution is deferred to later validation/backtesting phases.
- QuantConnect Paper Trading deployment and Live Node work are deferred to Paper Trading phases.
- Telegram regime alerts are deferred to notification phases.
- Render dashboard data integration is deferred to dashboard phases.
- Strategy setup signals, scoring, classifications, portfolio sizing, orders, fills, stops, targets, and exits are deferred to their respective later phases.

</deferred>

---

*Phase: 2-QuantConnect Foundation and Universe*
*Context gathered: 2026-06-13*
