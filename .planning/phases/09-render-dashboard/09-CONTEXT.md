# Phase 9: Render Dashboard - Context

**Gathered:** 2026-06-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 9 delivers a password-protected, mobile-friendly, read-only Streamlit
dashboard hosted on Render. The dashboard displays QuantConnect-sourced Paper
Trading state, strategy evidence, reports, notifications, activity, risk, and
system health with safe caching, stale-data warnings, USD/NIS display, secret
masking, and explicit paper-only disclaimers.

This phase does not add order submission, order modification, cancellation,
manual trade controls, real-money broker integrations, fake portfolio state, or
independent Render portfolio authority.

</domain>

<decisions>
## Implementation Decisions

### Data Authority and Access
- **D-01:** QuantConnect remains the source of truth for dashboard data. Render may read only verified QuantConnect API/export/Object Store paths and may keep short-lived cache copies for display resilience.
- **D-02:** Render must not maintain an independent simulated portfolio, hidden trading state, fake holdings, fake backtest results, fake Paper state, or manually editable trading records.
- **D-03:** Dashboard data contracts must explicitly label source, source timestamp, cache timestamp, freshness status, and authority. Deterministic tests may use explicit fixtures, but production UI must not claim fixture data as live state.
- **D-04:** Phase 9 planning must verify the current official QuantConnect Cloud API/Object Store/export paths before implementing data access. If exact endpoints or Object Store behavior are unclear, implementation must use typed `not_configured`, `not_available`, or `stale` states rather than fabricated data.

### Dashboard Structure and Mobile Layout
- **D-05:** The default mobile-first navigation is a compact Overview first, followed by tabs or equivalent segmented navigation for Positions, Trades, Signals, Backtests, Strategies, Risk, Notifications, Activity, and System.
- **D-06:** The dashboard should feel like an operational monitoring tool: dense, scan-friendly, restrained, and readable on mobile. Avoid marketing/landing-page composition.
- **D-07:** Overview should summarize the most important safety and operating state: paper-only warning, QuantConnect connection/source state, Paper mode, portfolio summary if available, stale status, open positions count, recent signals/actions, and system warnings.

### Refresh, Cache, and Stale-Data Policy
- **D-08:** Use manual refresh plus gentle polling where appropriate. Default cache should be short-lived and transparent to the user.
- **D-09:** Show a visible stale warning after approximately 10 minutes without fresh source data and a stronger stale/error state after approximately 30 minutes.
- **D-10:** Refresh, cache, and stale state must be read-only observability. Refresh must not submit orders, mutate Paper Trading state, trigger Telegram delivery, or change QuantConnect state.

### Render Authentication and Secrets
- **D-11:** Use a single strong dashboard password stored as a Render environment variable for v1. Do not implement full user management, roles, database-backed accounts, or social login in this phase.
- **D-12:** Authentication may use a simple session cookie or Streamlit session state, but failures must be safe: no data leak before login, no secrets in errors, and no logged raw password.
- **D-13:** Render environment variables may name or hold operational secrets; repository files, docs examples, test fixtures, logs, dashboard UI, and planning artifacts must never contain real secret values.

### Missing Data and Error Presentation
- **D-14:** Use a fail-visible approach. If QuantConnect, cache, FX, Telegram status, or Render configuration is unavailable, the dashboard should still render a safe read-only shell with banners, timestamps, and typed error/stale states.
- **D-15:** Do not silently hide missing critical sections in a way that makes the system look healthy. Missing or stale source data must be obvious and actionable.
- **D-16:** Error messages must be safe for operators: include typed status, affected subsystem, timestamp, and suggested operator action, but redact tokens, chat IDs, API keys, passwords, account credentials, and secret-like values.

### USD/NIS and FX Display
- **D-17:** USD remains the accounting/source currency. NIS is display-only and must not rewrite historical USD accounting or QuantConnect authority.
- **D-18:** Dashboard displays should include FX rate, FX source, FX timestamp, and FX staleness warning where NIS values appear.
- **D-19:** If FX data is missing or stale, show USD values normally and mark NIS display as unavailable/stale rather than inventing a conversion.

### Read-Only Enforcement
- **D-20:** The dashboard is read-only in v1. Allowed actions are limited to viewing, login/logout, and refresh.
- **D-21:** No order buttons, buy/sell/cancel/modify forms, manual trade entry, alert send buttons, Paper mode switching, recovery approval, or QuantConnect mutation controls are allowed in Phase 9.
- **D-22:** CSV/export, acknowledge/mark-read workflows, and operator actions are deferred unless a future phase explicitly scopes them with safety review.

### the agent's Discretion
- The agent may choose the exact Streamlit component structure, module names, and fixture format that best matches the current codebase.
- The agent may choose whether tabs, segmented controls, or a mobile-friendly sidebar best implement the selected navigation, as long as the resulting UI is compact, mobile-friendly, and read-only.
- The agent may choose conservative default cache durations and stale thresholds near the selected 10-minute and 30-minute policy if tests and documentation keep the thresholds explicit and configurable.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Planning and Product Scope
- `.planning/ROADMAP.md` - Phase 9 goal, requirements, success criteria, and planned four-plan structure.
- `.planning/REQUIREMENTS.md` - Dashboard requirements DASH-01 through DASH-07 plus safety requirements SAF-02, SAF-03, SAF-05, and QuantConnect requirement QC-05.
- `.planning/PROJECT.md` - Project-wide constraints: QuantConnect authority, Render read-only boundary, no secrets in repository files, paper-only scope, and mobile dashboard expectation.
- `.planning/STATE.md` - Current project state and Phase 9 focus.

### Prior Phase Evidence
- `.planning/phases/08-quantconnect-paper-trading-and-telegram/08-VERIFICATION.md` - Phase 8 verified Paper Trading and Telegram state, including live QuantConnect Paper status and Telegram smoke evidence.
- `.planning/phases/08-quantconnect-paper-trading-and-telegram/08-UAT.md` - External UAT evidence that QuantConnect Cloud Paper and Telegram smoke delivery passed.
- `.planning/phases/08-quantconnect-paper-trading-and-telegram/08-01-SUMMARY.md` - Paper mode gates and QuantConnect deployment prerequisite contracts.
- `.planning/phases/08-quantconnect-paper-trading-and-telegram/08-02-SUMMARY.md` - QuantConnect reconciliation, restart recovery, and protective recovery.
- `.planning/phases/08-quantconnect-paper-trading-and-telegram/08-03-SUMMARY.md` - Telegram integration, secret handling, and delivery results.
- `.planning/phases/08-quantconnect-paper-trading-and-telegram/08-04-SUMMARY.md` - Telegram alert coverage, regime alerts, daily summaries, and failure isolation.

### Existing Documentation
- `docs/paper_trading.md` - QuantConnect authority, Paper mode assumptions, and operator-run deployment boundary.
- `docs/telegram.md` - Telegram non-authoritative delivery and secret handling.
- `docs/operator_setup_phase08.md` - Operator-owned external setup and secret handling patterns.
- `docs/configuration.md` - Existing configuration expectations.
- `docs/safety.md` - Paper-only safety rules and no-secret/no-real-money boundaries.
- `docs/Dahan-MarketPilot-Master-Spec.md` - Original dashboard, Telegram, QuantConnect, and Render product specification.

### Existing Code and Tests
- `dashboard/app.py` - Current minimal Streamlit shell.
- `dashboard/models.py` - Current dashboard safety model.
- `dashboard/safety_view.py` - Pure rendering helper for safety lines.
- `tests/test_dashboard.py` - Existing dashboard safety tests and forbidden text checks.
- `config/dashboard.yaml` - Existing read-only dashboard config.
- `marketpilot/quantconnect_paper.py` - QuantConnect Paper status and snapshot contracts.
- `marketpilot/reconciliation.py` - QuantConnect-vs-local mirror reconciliation decisions.
- `marketpilot/telegram.py` - Telegram delivery result and secret redaction patterns.
- `marketpilot/notification_events.py` - Alert taxonomy and daily summary event contracts.
- `marketpilot/fx.py` - Existing FX seed/display logic.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `dashboard/app.py`: Provides the current Streamlit entry point and shared disclaimer rendering.
- `dashboard/models.py`: Defines a frozen safety-state model that can evolve into typed dashboard state objects.
- `dashboard/safety_view.py`: Provides pure render helpers that are easy to test without Streamlit.
- `config/dashboard.yaml`: Already enforces `paper_trading_only: true`, `read_only: true`, `manual_order_controls_enabled: false`, `display_currency: NIS`, and `trading_currency: USD`.
- `marketpilot/quantconnect_paper.py`: Contains authoritative Paper Trading snapshot/status contracts that dashboard data contracts should reuse or adapt.
- `marketpilot/reconciliation.py` and `marketpilot/recovery.py`: Provide status language for mismatch, recovery, and fail-closed display.
- `marketpilot/telegram.py` and `marketpilot/notification_events.py`: Provide safe, typed delivery and alert status concepts for the Notifications/System pages.
- `marketpilot/fx.py`: Existing FX model should guide USD/NIS display and staleness handling.

### Established Patterns
- Pure helper functions are preferred for testability; Streamlit rendering should remain thin.
- Safety configuration fails closed and keeps `paper_trading_only: true` central.
- External services use typed status results and fake/injected clients in tests.
- QuantConnect is authoritative; local files/Render/cache are display and audit context only.
- Secrets are referenced by env var names and redacted from safe dictionaries, reprs, logs, docs examples, and tests.
- Tests must remain deterministic offline by default and must not require QuantConnect, Telegram, Render, internet, or real credentials.

### Integration Points
- Render deployment planning should connect to `dashboard/app.py`, `requirements.txt` or deployment-specific dependency files, and Render environment variables.
- Dashboard auth should connect to `config/dashboard.yaml` and Render env vars without committing passwords.
- Dashboard data contracts should connect to QuantConnect export/API/Object Store adapters only after official docs verification.
- Dashboard pages should consume typed DTOs/snapshots rather than raw unvalidated external payloads.
- Health/status pages should display QuantConnect, cache, FX, Telegram, and dashboard auth/config state without exposing secrets.

</code_context>

<specifics>
## Specific Ideas

- The user delegated all Phase 9 discussion answers to the agent's recommended choices.
- Use the recommended dashboard posture: operational, mobile-first, read-only, QuantConnect-authoritative, fail-visible, and safe by default.
- Keep exact source endpoints/export paths open for research because current official QuantConnect and Render/Streamlit documentation must be verified before implementation.

</specifics>

<deferred>
## Deferred Ideas

- CSV/export from dashboard displayed data is deferred.
- Alert acknowledge/mark-read workflows are deferred.
- Multi-user accounts, roles, social login, and full user management are deferred.
- Any dashboard action that mutates Paper Trading, QuantConnect, Telegram, or recovery state is deferred and out of scope for Phase 9.

</deferred>

---

*Phase: 9-Render Dashboard*
*Context gathered: 2026-06-15*
