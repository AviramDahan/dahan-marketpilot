# Phase 1: Foundation and Safety - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md - this log preserves the alternatives considered.

**Date:** 2026-06-12
**Phase:** 1-Foundation and Safety
**Areas discussed:** License / attribution, Project skeleton, Safety config, Test boundary, Non-trading QC shell, Dashboard shell, Documentation sync

---

## License / Attribution

| Option | Description | Selected |
|--------|-------------|----------|
| MIT | Simple, short, suitable for private/commercial use, with separate attribution for third-party code. | Yes |
| Apache-2.0 | Stronger patent grant and naturally aligned with QuantConnect LEAN if Apache-2.0 code is copied directly. | |
| Defer choice | Create placeholders and leave final release-ready licensing blocked pending user decision. | |

**User's choice:** `MIT`
**Notes:** User selected option 1.

| Option | Description | Selected |
|--------|-------------|----------|
| Strict from day one | Create `NOTICE`, `THIRD_PARTY_NOTICES.md`, and require source/license recording before copying external logic. | Yes |
| Document policy only | Create files and policy but leave them mostly empty until third-party code is actually reused. | |
| Minimal now | Create only `LICENSE` and `DISCLAIMER.md` now; defer attribution structure. | |

**User's choice:** User said they did not know and asked the agent to choose.
**Notes:** The agent selected strict attribution from day one because the project may interact with Apache-2.0 QuantConnect code and should establish attribution discipline early.

---

## Project Skeleton

| Option | Description | Selected |
|--------|-------------|----------|
| Planning-first skeleton | Create only files needed for Phase 1 safety/config/tests/docs/minimal shells; avoid meaningless placeholders. | Yes |
| Full directory scaffold | Create most directories from the master spec with `.gitkeep` or placeholder files where needed. | |
| Lean minimal | Create only what is absolutely required for tests and minimal non-trading compile. | |

**User's choice:** `Planning-first skeleton`
**Notes:** User selected option 1.

| Option | Description | Selected |
|--------|-------------|----------|
| Shared package first | Create shared package for tests/config/models, then let `lean/` and `dashboard/` consume it gradually. | Yes |
| LEAN-first | Put most foundation under `lean/marketpilot/`; dashboard models come later. | |
| Separate apps | Keep `lean/` and `dashboard/` fully separate from the beginning. | |

**User's choice:** `Shared package first`
**Notes:** User selected option 1.

---

## Safety Config

| Option | Description | Selected |
|--------|-------------|----------|
| Hardcoded constant plus validation | Central `PAPER_TRADING_ONLY = True` plus configuration validation that rejects false or live-money features. | Yes |
| Config-only guard | Store the guard only in configuration and load it at runtime. | |
| Constant-only guard | Use only a code constant and do not expose a parallel config key. | |

**User's choice:** `Hardcoded constant plus validation`
**Notes:** User selected option 1.

| Option | Description | Selected |
|--------|-------------|----------|
| Fail closed | Unsafe or suspicious safety/trading keys cause explicit validation failure. | Yes |
| Warn only | Show warnings but do not fail validation. | |
| Ignore unknown | Ignore unknown keys as long as known central values are safe. | |

**User's choice:** `Fail closed`
**Notes:** User selected option 1.

---

## Test Boundary

| Option | Description | Selected |
|--------|-------------|----------|
| Safety and config gates | Unit tests for paper-only guard, unsafe config rejection, FX seed calculation, domain model basics, and dashboard read-only flags. | Yes |
| Broad placeholder suite | Create skeletons for all future tests, even if mostly skipped or placeholder. | |
| Minimal smoke tests | Only import/basic validation tests. | |

**User's choice:** `Safety and config gates`
**Notes:** User selected option 1.

| Option | Description | Selected |
|--------|-------------|----------|
| No QC runtime in unit tests | Offline unit tests only; minimal algorithm exists but does not require QuantConnect credentials or cloud. | |
| Local LEAN smoke optional | Offline unit tests plus optional smoke test when LEAN CLI is installed. | |
| Require LEAN compile | Phase 1 does not pass without a real compile check for the minimal non-trading algorithm. | Yes |

**User's choice:** `Require LEAN compile`
**Notes:** User selected option 3. The compile check must not require stored credentials or any trading action.

---

## Non-trading QC Shell

| Option | Description | Selected |
|--------|-------------|----------|
| Initialize only | Set basic cash/config/logging only, without subscriptions, indicators, or universe. | |
| Benchmarks only | Add SPY/QQQ subscriptions only, without signals or orders. | Yes |
| Skeleton hooks | Include empty hooks such as `OnData`, but no real logic. | |
| You choose | Agent chooses the best balance for the project. | Yes |

**User's choice:** `You choose`
**Notes:** The agent selected `Benchmarks only` to make the compile check meaningful while avoiding strategy, universe, indicator, or order logic.

---

## Dashboard Shell

| Option | Description | Selected |
|--------|-------------|----------|
| Static safety shell | Show product title, disclaimer, paper-only banner, read-only status, and "No live data connected". | Yes |
| Config-driven shell | Read basic config and show selected environment/status. | |
| Mock data shell | Show mock portfolio/cards for layout, clearly marked as demo. | |
| You choose | Agent chooses the best balance for the project. | Yes |

**User's choice:** `You choose`
**Notes:** The agent selected `Static safety shell` to avoid fake portfolio or fake performance data in Phase 1.

---

## Documentation Sync

| Option | Description | Selected |
|--------|-------------|----------|
| Safety docs only | Only `README`, `DISCLAIMER`, and basic safety docs. | |
| Full foundation docs | `README`, `DISCLAIMER`, licensing/attribution docs, setup notes, config docs, testing notes, and AI collaboration updates. | Yes |
| GSD artifacts only | Rely on `.planning/` and `AGENTS.md`; defer public docs. | |
| You choose | Agent chooses the best balance for the project. | |

**User's choice:** `Full foundation docs`
**Notes:** User selected option 2.

---

## the agent's Discretion

- Attribution handling: user delegated; agent chose strict attribution from day one.
- Minimal QuantConnect shell: user delegated; agent chose SPY/QQQ benchmark subscriptions only.
- Minimal dashboard shell: user delegated; agent chose static safety shell with no mock portfolio data.
- Future questions should include a `You choose` option when a technical tradeoff is better delegated to the agent.

## Deferred Ideas

None.
