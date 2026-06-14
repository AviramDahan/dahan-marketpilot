# Phase 9: Render Dashboard - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md - this log preserves the alternatives considered.

**Date:** 2026-06-15
**Phase:** 9-Render Dashboard
**Areas discussed:** data source, mobile structure, refresh/cache/stale policy, Render authentication, missing data/errors, USD/NIS display, read-only actions

---

## Dashboard Data Source

| Option | Description | Selected |
|--------|-------------|----------|
| A | QuantConnect is source of truth; dashboard reads only approved snapshots/exports with temporary local cache. | yes |
| B | Dashboard calls several QuantConnect endpoints directly on each load with minimal cache. | |
| C | Dashboard primarily reads algorithm-created export/Object Store files rather than direct live API. | |
| Z | The agent chooses. | selected by user delegation |

**User's choice:** User authorized the agent to answer with recommended choices.
**Notes:** Recommended choice A was selected.

---

## Mobile Dashboard Structure

| Option | Description | Selected |
|--------|-------------|----------|
| A | Overview first, then compact tabs for Positions, Trades, Signals, Backtests, Strategies, Risk, Notifications, Activity, and System. | yes |
| B | One long page with sections and no tabs. | |
| C | Only Overview and System first; other pages later. | |
| Z | The agent chooses. | selected by user delegation |

**User's choice:** User authorized the agent to answer with recommended choices.
**Notes:** Recommended choice A was selected.

---

## Refresh, Cache, and Stale Warnings

| Option | Description | Selected |
|--------|-------------|----------|
| A | Manual refresh plus gentle polling, short cache, warning after about 10 minutes, serious stale state after about 30 minutes. | yes |
| B | Manual refresh only, no polling. | |
| C | More frequent polling every 30-60 seconds. | |
| Z | The agent chooses. | selected by user delegation |

**User's choice:** User authorized the agent to answer with recommended choices.
**Notes:** Recommended choice A was selected.

---

## Render Authentication

| Option | Description | Selected |
|--------|-------------|----------|
| A | One strong password through Render env var, simple session cookie/state, no user management. | yes |
| B | Basic Auth through middleware or Render layer if available. | |
| C | Full account and role system. | |
| Z | The agent chooses. | selected by user delegation |

**User's choice:** User authorized the agent to answer with recommended choices.
**Notes:** Recommended choice A was selected.

---

## Missing Data and Error Presentation

| Option | Description | Selected |
|--------|-------------|----------|
| A | Fail visible with read-only dashboard, banners, last-known timestamp, stale/error status, and no invented data. | yes |
| B | Hide sections that lack data. | |
| C | Block dashboard entirely if QuantConnect is unavailable. | |
| Z | The agent chooses. | selected by user delegation |

**User's choice:** User authorized the agent to answer with recommended choices.
**Notes:** Recommended choice A was selected.

---

## USD/NIS and FX

| Option | Description | Selected |
|--------|-------------|----------|
| A | USD remains accounting source; NIS is display-only with FX rate, source, timestamp, and stale warning. | yes |
| B | Display USD only first. | |
| C | Display NIS as primary and USD as secondary. | |
| Z | The agent chooses. | selected by user delegation |

**User's choice:** User authorized the agent to answer with recommended choices.
**Notes:** Recommended choice A was selected.

---

## Allowed Dashboard Actions

| Option | Description | Selected |
|--------|-------------|----------|
| A | Absolute read-only: view, refresh, login, and logout only. No order controls, no export, no mark-read. | yes |
| B | Read-only plus CSV export of displayed data. | |
| C | Read-only plus acknowledge/mark-read for alerts. | |
| Z | The agent chooses. | selected by user delegation |

**User's choice:** User authorized the agent to answer with recommended choices.
**Notes:** Recommended choice A was selected.

---

## the agent's Discretion

- User explicitly authorized the agent to answer all Phase 9 discussion questions with the recommended choices.
- Exact implementation details, module structure, and adapter boundaries are left for research and planning, constrained by CONTEXT.md.

## Deferred Ideas

- CSV/export from displayed dashboard data.
- Alert acknowledge/mark-read workflows.
- Full user management, roles, and social login.
- Any dashboard action that mutates QuantConnect, Paper Trading, Telegram, or recovery state.
