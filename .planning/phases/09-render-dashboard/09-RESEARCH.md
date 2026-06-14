# Phase 09: Render Dashboard - Research

**Researched:** 2026-06-15
**Domain:** QuantConnect Cloud/API data access, Streamlit dashboard architecture, Render Python web service deployment
**Confidence:** MEDIUM

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
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

### Deferred Ideas (OUT OF SCOPE)
- CSV/export from dashboard displayed data is deferred.
- Alert acknowledge/mark-read workflows are deferred.
- Multi-user accounts, roles, social login, and full user management are deferred.
- Any dashboard action that mutates Paper Trading, QuantConnect, Telegram, or recovery state is deferred and out of scope for Phase 9.
</user_constraints>

## Project Constraints (from AGENTS.md)

- Project files, code, tests, identifiers, configuration, technical docs, and GSD artifacts must be English; user-facing chat must be Hebrew. [VERIFIED: AGENTS.md]
- QuantConnect remains authoritative for simulated cash, portfolio equity, holdings, open positions, orders, fills, Paper Trading state, algorithm status, and QuantConnect Backtest results. [VERIFIED: AGENTS.md]
- Render must stay read-only and must never add dashboard order-entry controls. [VERIFIED: AGENTS.md]
- Tests must not require real QuantConnect, Telegram, Render, broker credentials, internet, or real market access. [VERIFIED: AGENTS.md]
- Current official QuantConnect APIs must be verified before use; do not invent QuantConnect APIs, LEAN classes, Cloud API endpoints, package behavior, or tutorial details. [VERIFIED: AGENTS.md]
- No credentials or secrets may appear in source files, logs, tests, reports, planning artifacts, docs examples, or chat. [VERIFIED: AGENTS.md]
- Do not commit unless explicitly asked; the user explicitly requested no commit for this research turn. [VERIFIED: AGENTS.md + user request]

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| QC-05 | QuantConnect Object Store or Cloud API export mechanisms are designed only after official documentation verification. | Official QuantConnect Cloud API and Object Store docs checked; recommendation uses read endpoints plus algorithm-exported Object Store DTOs only. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference] [CITED: https://www.quantconnect.com/docs/v2/writing-algorithms/object-store] |
| DASH-01 | Render hosts a password-protected Streamlit dashboard. | Render web service/env-var docs and Streamlit auth/session docs checked; recommendation uses single env-var password and Streamlit session state. [CITED: https://render.com/docs/web-services] [CITED: https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state] |
| DASH-02 | Dashboard is read-only and contains no order submission, modification, cancellation, or manual trade controls. | QuantConnect mutation endpoints are explicitly excluded; only viewing, login/logout, and refresh are permitted. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference] |
| DASH-03 | Dashboard views include Overview, Positions, Trades, Signals, Backtests, Strategies, Risk, Notifications, Activity, and System Status. | Streamlit tabs/navigation are suitable for compact grouped views; existing shell can evolve into page modules. [CITED: https://docs.streamlit.io/develop/api-reference/layout/st.tabs] [VERIFIED: dashboard/app.py] |
| DASH-04 | Dashboard data is sourced from QuantConnect-approved API/export paths and displays stale-data warnings. | QuantConnect portfolio/orders/insights snapshots update about every 10 minutes; stale policy should align to 10/30 minute thresholds. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/read-live-algorithm/portfolio-state] |
| DASH-05 | Dashboard displays portfolio values in USD and NIS and shows FX timestamp/source/staleness warnings. | Existing FX seed model validates USD trading and NIS display metadata; dashboard must keep NIS display-only. [VERIFIED: marketpilot/fx.py] |
| DASH-06 | Dashboard masks secrets and presents API/cache/authentication errors safely. | Existing Telegram config/result redaction patterns should be reused for dashboard error DTOs. [VERIFIED: marketpilot/telegram.py] |
| DASH-07 | Dashboard tests cover API parsing, caching, stale data, authentication, read-only behavior, error presentation, and secret masking. | Streamlit AppTest supports headless app execution with pytest; pure helpers remain preferred for deterministic offline tests. [CITED: https://docs.streamlit.io/develop/api-reference/app-testing] [VERIFIED: tests/test_dashboard.py] |
</phase_requirements>

## Executive Recommendation

Build Phase 9 as a read-only Streamlit monitoring app with a thin UI layer, pure typed dashboard DTOs, and injected data clients. [VERIFIED: codebase read] Use QuantConnect Cloud API read endpoints for authoritative live Paper portfolio, orders, insights, logs, and live deployment status, and require the QuantConnect algorithm to export dashboard-specific JSON snapshots to Object Store for data that the live read endpoints do not directly expose, such as strategy evidence, risk summaries, notification summaries, and dashboard health DTOs. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/read-live-algorithm] [CITED: https://www.quantconnect.com/docs/v2/writing-algorithms/object-store]

Use Streamlit `st.cache_data` with short TTLs only for read results, and keep every DTO labeled with `source`, `source_timestamp`, `cache_timestamp`, `freshness_status`, and `authority`. [CITED: https://docs.streamlit.io/develop/api-reference/caching-and-state/st.cache_data] Default to fresh under 10 minutes, stale warning at 10 minutes, and error/strong stale state at 30 minutes, matching Phase 9 D-09 and QuantConnect's documented live snapshot cadence for portfolio/orders/insights. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/read-live-algorithm/portfolio-state] [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/read-live-algorithm/orders]

Deploy on Render as a Python web service with `streamlit run dashboard/app.py --server.address=0.0.0.0 --server.port=$PORT`, store all operational secrets as Render environment variables, and avoid Render disk/database state for portfolio authority. [CITED: https://render.com/docs/web-services] [CITED: https://render.com/docs/configure-environment-variables] [CITED: https://render.com/docs/free]

## Official Sources Checked With URLs And Dates

| Source | Checked | Findings |
|--------|---------|----------|
| QuantConnect API Reference | 2026-06-15 | API v2 includes authentication, live read endpoints, backtest read endpoints, Object Store management, and mutation endpoints that must be excluded from the dashboard adapter. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference] |
| QuantConnect Authentication | 2026-06-15 | API requests use User Id, API Token, timestamped hashed token, and base URL `https://www.quantconnect.com/api/v2`; credentials must come from environment/secret stores only. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/authentication] |
| QuantConnect Live Portfolio State | 2026-06-15 | `/live/portfolio/read` reads portfolio state for a project and its snapshot updates about every 10 minutes. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/read-live-algorithm/portfolio-state] |
| QuantConnect Live Orders | 2026-06-15 | `/live/orders/read` reads live algorithm orders by project/deploy id and range; snapshot updates about every 10 minutes. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/read-live-algorithm/orders] |
| QuantConnect Live Insights | 2026-06-15 | `/live/insights/read` reads live algorithm insights by project/deploy id and range; snapshot updates about every 10 minutes. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/read-live-algorithm/insights] |
| QuantConnect Live Logs | 2026-06-15 | `/live/logs/read` reads live logs by project/deploy id and line range; snapshot updates about every 5 minutes. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/read-live-algorithm/logs] |
| QuantConnect List Live Algorithms | 2026-06-15 | `/live/list` lists past/current live deployments and can filter by project id and status. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/list-live-algorithms] |
| QuantConnect Object Store API | 2026-06-15 | `/object/get` returns a job id and download URL for requested object keys; `/object/list` and `/object/properties` support discovery/metadata. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/object-store-management/get-object-store-file] |
| QuantConnect Writing Algorithms Object Store | 2026-06-15 | Algorithms can save/read strings, JSON, XML, and bytes in an organization-specific Object Store; keys should be prefixed with project id to avoid collisions. [CITED: https://www.quantconnect.com/docs/v2/writing-algorithms/object-store] |
| QuantConnect Organization Object Store | 2026-06-15 | Free Object Store capacity is 50 MB/1,000 files; live access is slower than research/backtesting and individual objects should stay under 50 MB. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/organizations/object-store] |
| Streamlit `st.cache_data` | 2026-06-15 | Data-returning functions can be cached with TTL and cleared manually; cached data is shared globally by default and returned as copies. [CITED: https://docs.streamlit.io/develop/api-reference/caching-and-state/st.cache_data] |
| Streamlit `st.session_state` | 2026-06-15 | Session state persists values across reruns and pages within a user session. [CITED: https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state] |
| Streamlit `st.tabs` | 2026-06-15 | Tabs group related content; by default, all tab content is computed and sent unless lazy behavior is used. [CITED: https://docs.streamlit.io/develop/api-reference/layout/st.tabs] |
| Streamlit secrets management | 2026-06-15 | Streamlit recommends keeping secrets outside the repository, including uncommitted secrets files or environment variables. [CITED: https://docs.streamlit.io/develop/concepts/connections/secrets-management] |
| Streamlit auth APIs | 2026-06-15 | `st.login` is OIDC-oriented and requires `streamlit[auth]`; this exceeds the Phase 9 v1 decision for a single password. [CITED: https://docs.streamlit.io/develop/api-reference/user/st.login] |
| Streamlit remote start guidance | 2026-06-15 | Remote deployments need the correct exposed port via `--server.port`; stable cookie secrets matter across replicas. [CITED: https://docs.streamlit.io/knowledge-base/deploy/remote-start] |
| Streamlit AppTest | 2026-06-15 | `st.testing.v1.AppTest` supports headless app tests with pytest and injected secrets/session state. [CITED: https://docs.streamlit.io/develop/api-reference/app-testing] |
| Render Web Services | 2026-06-15 | Web services have build/start commands and must bind HTTP on `0.0.0.0`, preferably using the `PORT` environment variable. [CITED: https://render.com/docs/web-services] |
| Render Environment Variables and Secrets | 2026-06-15 | Render env vars configure runtime behavior and protect against committing secrets; secret files are available at runtime. [CITED: https://render.com/docs/configure-environment-variables] |
| Render Health Checks | 2026-06-15 | Web services can define HTTP health check paths; 2xx/3xx responses are healthy. [CITED: https://render.com/docs/health-checks] |
| Render Python Version | 2026-06-15 | Render supports setting `PYTHON_VERSION` or `.python-version`; services created now default to Python 3.14.3 unless configured. [CITED: https://render.com/docs/python-version] |
| Render Free Plan | 2026-06-15 | Free web services spin down after 15 idle minutes and use ephemeral filesystem behavior. [CITED: https://render.com/docs/free] |

## QuantConnect Data Access/Export Recommendation

Use two read-only data paths. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference]

| Dashboard Need | Recommended Source | Why |
|----------------|--------------------|-----|
| Deployment/algorithm status | `/live/list` plus existing `QuantConnectPaperStatus` DTO | Lists current/past live deployments and status; aligns with Phase 8 status contracts. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/list-live-algorithms] [VERIFIED: marketpilot/quantconnect_paper.py] |
| Cash, holdings, portfolio state | `/live/portfolio/read` | QuantConnect-documented live portfolio read endpoint; snapshot cadence is about 10 minutes. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/read-live-algorithm/portfolio-state] |
| Orders and fills/activity | `/live/orders/read` plus algorithm-exported fill summaries if endpoint payload does not include every fill detail needed by current DTOs | Live orders endpoint is documented; Phase 8 fill DTOs need authoritative QuantConnect order IDs. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/read-live-algorithm/orders] [VERIFIED: marketpilot/quantconnect_paper.py] |
| Signals/insights | `/live/insights/read` and/or Object Store exported signal evidence | Insights endpoint is documented; custom MarketPilot evidence is project-specific and should be exported by the algorithm as JSON. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/read-live-algorithm/insights] [CITED: https://www.quantconnect.com/docs/v2/writing-algorithms/object-store] |
| Strategy/risk/backtest/report summaries | Algorithm-created Object Store JSON files under project-prefixed keys | Object Store supports JSON/string/bytes and is organization-specific; project-id prefixes avoid collisions. [CITED: https://www.quantconnect.com/docs/v2/writing-algorithms/object-store] |
| Logs/system activity | `/live/logs/read` for live log tails, plus sanitized algorithm-exported health DTOs for dashboard display | Logs endpoint exists and updates about every 5 minutes; dashboard should not expose raw secrets from logs. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/read-live-algorithm/logs] [VERIFIED: AGENTS.md] |

Do not call QuantConnect mutation endpoints from Render, including live algorithm creation/update, liquidate, stop, live commands, Object Store upload/delete, project/file update, or backtest creation/update/delete. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference] Render refresh is display-only and must not submit orders, trigger Telegram, change Paper mode, change Object Store data, or mutate QuantConnect state. [VERIFIED: 09-CONTEXT.md]

Recommended Object Store keys should be project-prefixed and versioned, for example `"{project_id}/dashboard/latest.json"`, `"{project_id}/dashboard/signals/latest.json"`, and `"{project_id}/dashboard/health/latest.json"`. [CITED: https://www.quantconnect.com/docs/v2/writing-algorithms/object-store] These are recommendations, not verified existing keys; implementation must treat missing keys as `not_available` or `not_configured`. [ASSUMED]

## Streamlit/Render Deployment Recommendation

Add `streamlit` as a runtime dependency only after a planner checkpoint because the package-legitimacy seam returned `SUS` for unknown-download/too-new signals despite PyPI and official docs confirming the package. [VERIFIED: package-legitimacy check] [VERIFIED: pip index versions streamlit] [CITED: https://docs.streamlit.io/]

Use this Render configuration shape. [CITED: https://render.com/docs/web-services] [CITED: https://render.com/docs/blueprint-spec]

```yaml
services:
  - type: web
    runtime: python
    name: dahan-marketpilot-dashboard
    buildCommand: pip install -r requirements.txt
    startCommand: streamlit run dashboard/app.py --server.address=0.0.0.0 --server.port=$PORT
    healthCheckPath: /
    envVars:
      - key: PYTHON_VERSION
        value: 3.13.5
      - key: DASHBOARD_PASSWORD
        sync: false
      - key: DASHBOARD_SESSION_SECRET
        sync: false
      - key: QUANTCONNECT_USER_ID
        sync: false
      - key: QUANTCONNECT_API_TOKEN
        sync: false
      - key: QUANTCONNECT_PROJECT_ID
        sync: false
      - key: QUANTCONNECT_ORGANIZATION_ID
        sync: false
```

Use `PYTHON_VERSION` or `.python-version` because the project requires Python `>=3.11` while the current local shell is Python 3.10.10. [VERIFIED: pyproject.toml] [VERIFIED: environment probe] [CITED: https://render.com/docs/python-version]

Free Render web services are acceptable for early non-production monitoring but are operationally risky for a dashboard because idle spin-down can delay access and the filesystem is ephemeral. [CITED: https://render.com/docs/free] Do not rely on Render local disk for cache authority or portfolio state. [CITED: https://render.com/docs/free] [VERIFIED: AGENTS.md]

## Auth/Session Recommendation

Use one strong `DASHBOARD_PASSWORD` env var, compare with `hmac.compare_digest`, store only `dashboard_authenticated=True` in `st.session_state`, and call `st.stop()` before rendering any QuantConnect data when unauthenticated. [CITED: https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state] [ASSUMED]

Do not use `st.login`/OIDC in Phase 9 because Streamlit's native login flow is OIDC-provider based and requires `streamlit[auth]`, while D-11 explicitly selects a single-password v1 dashboard without full user management. [CITED: https://docs.streamlit.io/develop/api-reference/user/st.login] [VERIFIED: 09-CONTEXT.md]

Do not put the password or session secret in `config/dashboard.yaml`, `.streamlit/secrets.toml`, docs examples, tests, or planning artifacts. [VERIFIED: AGENTS.md] Use fake env mappings in tests only, such as `{"DASHBOARD_PASSWORD": "test-password"}`, and never mark them as production credentials. [ASSUMED]

## Cache/Stale/Error Recommendation

Use a dashboard cache wrapper around `st.cache_data(ttl=...)` for external reads, with manual refresh clearing only dashboard read caches. [CITED: https://docs.streamlit.io/develop/api-reference/caching-and-state/st.cache_data] Manual refresh must not call QuantConnect mutation endpoints, Telegram delivery, or local recovery approval code. [VERIFIED: 09-CONTEXT.md]

Recommended defaults:

| Value | Recommendation | Rationale |
|-------|----------------|-----------|
| Cache TTL | 120 seconds for API/Object Store reads | Short enough for operator display while respecting QuantConnect snapshot cadence. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/read-live-algorithm/portfolio-state] [ASSUMED] |
| Stale warning | Source data age >= 10 minutes | Matches Phase 9 D-09 and QuantConnect live portfolio/orders/insights snapshot cadence. [VERIFIED: 09-CONTEXT.md] [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/read-live-algorithm/orders] |
| Strong stale/error | Source data age >= 30 minutes or latest read failed with no usable cached snapshot | Matches Phase 9 D-09 and fail-visible policy. [VERIFIED: 09-CONTEXT.md] |
| Last-good cache | Allowed in memory for display only | Render cache is not authority; display must label cache timestamp and source timestamp. [VERIFIED: 09-CONTEXT.md] |

Every section should render one of: `fresh`, `stale`, `error`, `not_configured`, `not_available`, or `auth_required`. [ASSUMED] Do not silently omit a section when data is missing. [VERIFIED: 09-CONTEXT.md]

## USD/NIS/FX Recommendation

Keep USD as source/accounting currency and calculate NIS display values from an explicit FX snapshot containing rate, source, timestamp, and staleness. [VERIFIED: marketpilot/fx.py] If FX is missing or stale, render USD normally and mark NIS as unavailable/stale; never infer or invent a fallback rate. [VERIFIED: 09-CONTEXT.md]

Phase 9 should extend `marketpilot/fx.py` with display conversion/staleness helpers or add dashboard-specific formatting helpers that consume `FxSeed`-like metadata. [VERIFIED: marketpilot/fx.py] Current `FxSeed` validates the seed rate and USD/NIS currencies but does not yet provide runtime stale-rate display helpers. [VERIFIED: marketpilot/fx.py]

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|--------------|----------------|-----------|
| QuantConnect state authority | QuantConnect Cloud | Dashboard adapter | QuantConnect owns cash, equity, holdings, orders, fills, live status, and backtest results; dashboard reads only. [VERIFIED: AGENTS.md] |
| Dashboard-specific exported evidence | QuantConnect algorithm/Object Store | Render dashboard | Strategy/risk/notification summaries should be exported by the algorithm under project-prefixed keys; Render displays typed snapshots. [CITED: https://www.quantconnect.com/docs/v2/writing-algorithms/object-store] |
| Authentication | Render/Streamlit app | Browser session | Single password is checked server-side; browser/session state only stores authenticated status. [VERIFIED: 09-CONTEXT.md] [CITED: https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state] |
| Caching and stale states | Render/Streamlit app | QuantConnect source timestamps | Cache is presentation resilience only; source timestamps decide freshness. [VERIFIED: 09-CONTEXT.md] |
| Mobile UI | Browser/Streamlit frontend | Pure render helpers | Streamlit renders compact tabs/pages; pure helpers keep tests deterministic. [CITED: https://docs.streamlit.io/develop/api-reference/layout/st.tabs] [VERIFIED: tests/test_dashboard.py] |
| Secrets | Render environment | Local test env fakes | Render stores real env values; repo stores env var names only. [CITED: https://render.com/docs/configure-environment-variables] [VERIFIED: AGENTS.md] |

## Recommended Project Structure

```text
dashboard/
  app.py                 # Thin Streamlit entry point and navigation
  auth.py                # Password/session helpers; no secrets logged
  cache.py               # st.cache_data wrappers and stale classification
  config.py              # Dashboard config loader/validation
  data_client.py         # Read-only QuantConnect/Object Store client interface
  models.py              # Dashboard DTOs and section status models
  formatters.py          # USD/NIS, timestamps, status labels
  pages/
    overview.py
    positions.py
    trades.py
    signals.py
    backtests.py
    strategies.py
    risk.py
    notifications.py
    activity.py
    system_status.py
```

This structure follows the existing thin Streamlit shell plus pure helper pattern and avoids placing business logic directly in `dashboard/app.py`. [VERIFIED: dashboard/app.py] [VERIFIED: dashboard/safety_view.py]

## Do Not Hand-Roll

| Problem | Do Not Build | Use Instead | Why |
|---------|--------------|-------------|-----|
| Authoritative portfolio store | Render JSON/SQLite/local files as portfolio state | QuantConnect live read endpoints and exported Object Store DTOs | QuantConnect is the project authority; Render filesystem can be ephemeral. [VERIFIED: AGENTS.md] [CITED: https://render.com/docs/free] |
| Password hashing/user management | Users table, roles, social login, OIDC | Single env-var password with constant-time comparison | D-11 chooses v1 single password and excludes full user management. [VERIFIED: 09-CONTEXT.md] |
| API mutation control panel | Order/recovery/Paper-mode buttons | Read-only refresh and status display | D-20/D-21 allow viewing/login/logout/refresh only. [VERIFIED: 09-CONTEXT.md] |
| Cache database | Persistent Render disk/cache database | `st.cache_data` plus source/cache timestamps | Cache is display-only; Streamlit already supports data cache TTL/clear. [CITED: https://docs.streamlit.io/develop/api-reference/caching-and-state/st.cache_data] |
| Secret masking | Ad hoc string printing | Central redaction helper patterned after Telegram safe dict/result | Existing Telegram code already redacts token/chat-like values. [VERIFIED: marketpilot/telegram.py] |

## Test Strategy

Use deterministic offline tests only. [VERIFIED: AGENTS.md] Keep API clients injected/fakeable and test parsing with explicit fixtures labeled as deterministic test fixtures, not live state. [VERIFIED: marketpilot/quantconnect_paper.py]

Recommended tests:

| Area | Test |
|------|------|
| API parsing | Parse fixture payloads for live portfolio, live orders, live insights, live logs, and Object Store dashboard JSON into typed DTOs. [CITED: QuantConnect API docs listed above] |
| Cache/stale | Unit-test freshness states at <10m, >=10m, >=30m, failed read with last-good cache, and failed read without cache. [VERIFIED: 09-CONTEXT.md] |
| Auth | Test no dashboard data renders before successful password; wrong password is safe; logout clears session; raw passwords never appear in diagnostics. [CITED: https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state] |
| Read-only enforcement | Static tests reject forbidden words/actions: submit order, buy/sell/cancel/modify, paper mode switch, Telegram send, recovery approval, QuantConnect mutation endpoints. [VERIFIED: tests/test_dashboard.py] |
| Error presentation | Test typed subsystem errors redact secret-like keys and show operator-safe messages. [VERIFIED: marketpilot/telegram.py] |
| USD/NIS/FX | Test USD remains present when FX missing/stale; NIS display requires rate/source/timestamp and staleness labels. [VERIFIED: marketpilot/fx.py] |
| Streamlit UI | Use `st.testing.v1.AppTest` for login shell, tabs/pages, warning banners, and no-data states where practical. [CITED: https://docs.streamlit.io/develop/api-reference/app-testing] |
| Render config | Static-test `render.yaml`/docs start command contains `--server.address=0.0.0.0` and `--server.port=$PORT`, and secret env vars use `sync: false` when in Blueprint. [CITED: https://render.com/docs/web-services] [CITED: https://render.com/docs/blueprint-spec] |

Quick command: `python -m pytest tests/test_dashboard.py -q`. [VERIFIED: pyproject.toml]

Full suite command: `python -m pytest -q`. [VERIFIED: pyproject.toml]

Current environment gap: local Python is 3.10.10 but project metadata requires Python >=3.11; Render must set `PYTHON_VERSION` and release verification should run on Python >=3.11. [VERIFIED: environment probe] [VERIFIED: pyproject.toml]

## Package Legitimacy Audit

| Package | Registry | Latest Version | Installed | Verdict | Disposition |
|---------|----------|----------------|-----------|---------|-------------|
| `streamlit` | PyPI | 1.58.0 | 1.58.0 | SUS: too-new/unknown-downloads from seam | Keep, but planner must add `checkpoint:human-verify` before adding/pinning. [VERIFIED: package-legitimacy check] [VERIFIED: pip index versions streamlit] |
| `PyYAML` | PyPI | 6.0.3 | 6.0.3 | SUS: unknown-downloads from seam | Already present; keep with checkpoint before dependency changes. [VERIFIED: package-legitimacy check] [VERIFIED: pip index versions PyYAML] |
| `pytest` | PyPI | 9.1.0 | 7.3.1 | SUS: too-new/unknown-downloads from seam | Already dev dependency; do not upgrade in Phase 9 unless planner adds checkpoint. [VERIFIED: package-legitimacy check] [VERIFIED: pip index versions pytest] |

**Packages removed due to SLOP verdict:** none. [VERIFIED: package-legitimacy check]
**Packages flagged as suspicious SUS:** `streamlit`, `PyYAML`, `pytest`. [VERIFIED: package-legitimacy check]

Do not add `streamlit[auth]` or `Authlib` for Phase 9 because D-11 selects single-password auth and Streamlit OIDC exceeds scope. [CITED: https://docs.streamlit.io/develop/api-reference/user/st.login] [VERIFIED: 09-CONTEXT.md]

## Security Domain

| ASVS Category | Applies | Standard Control |
|---------------|---------|------------------|
| V2 Authentication | yes | Single env-var password, constant-time comparison, no data before auth. [ASSUMED] |
| V3 Session Management | yes | Streamlit session state stores authenticated flag only; optional session secret via env for stable cookies. [CITED: https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state] [CITED: https://docs.streamlit.io/knowledge-base/deploy/remote-start] |
| V4 Access Control | yes | Dashboard has one role: read-only viewer; no mutation endpoints or controls. [VERIFIED: 09-CONTEXT.md] |
| V5 Input Validation | yes | Validate env vars/config, parse external JSON into typed DTOs, reject malformed payloads into typed error states. [ASSUMED] |
| V6 Cryptography | yes | Use Python standard `hmac.compare_digest`; never implement custom crypto. [ASSUMED] |
| V7 Error Handling | yes | Redact secret-like values; show typed subsystem/timestamp/action only. [VERIFIED: marketpilot/telegram.py] |
| V9 Communications | yes | Render terminates HTTPS for public web services and redirects HTTP to HTTPS. [CITED: https://render.com/docs/web-services] |

Threat patterns:

| Pattern | STRIDE | Mitigation |
|---------|--------|------------|
| Dashboard password leak | Information Disclosure | Store only in Render env var, never render/log raw value, no repo examples with real values. [CITED: https://render.com/docs/configure-environment-variables] [VERIFIED: AGENTS.md] |
| Unauthenticated data exposure | Information Disclosure | Auth gate must run before any data fetch or page render; tests assert no data before login. [ASSUMED] |
| Accidental QuantConnect mutation | Tampering/Elevation | Read-only client allowlist for `/live/list`, `/live/portfolio/read`, `/live/orders/read`, `/live/insights/read`, `/live/logs/read`, `/object/get`, `/object/properties`, `/object/list`; reject all mutation endpoint constants in dashboard code. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference] |
| Stale Paper state mistaken as current | Spoofing/Information Integrity | Display source timestamp, cache timestamp, freshness status, and authority on every section. [VERIFIED: 09-CONTEXT.md] |
| Secret exposure in errors | Information Disclosure | Central redaction helper using existing Telegram redaction patterns. [VERIFIED: marketpilot/telegram.py] |

## Risks And Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| QuantConnect live read snapshots update about every 10 minutes, so manual refresh may not show immediate changes. | Operator may think refresh failed. | Show source timestamp and "QuantConnect snapshot cadence" messaging; cache timestamp must be separate from source timestamp. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/read-live-algorithm/portfolio-state] |
| Object Store dashboard DTO keys do not exist yet. | Dashboard sections could look empty. | Implement typed `not_available`/`not_configured` states and require algorithm export task before claiming live data. [VERIFIED: 09-CONTEXT.md] |
| Object Store free capacity and live access constraints. | Large JSON snapshots could exceed practical limits. | Keep latest DTOs compact, project-prefixed, and under individual-object guidance; do not store history-heavy dashboard data in Object Store for v1. [CITED: https://www.quantconnect.com/docs/v2/cloud-platform/organizations/object-store] |
| Render free tier spin-down. | Mobile dashboard cold start delay and stale first view. | Prefer paid instance for operational use; if free is used, disclose cold-start limitation and rely on stale banners. [CITED: https://render.com/docs/free] |
| Streamlit tabs compute all content by default. | Expensive API calls can happen for non-visible tabs. | Fetch once into a cached dashboard snapshot before rendering tabs, or use lazy tab behavior when available. [CITED: https://docs.streamlit.io/develop/api-reference/layout/st.tabs] |
| Local dev Python does not satisfy project metadata. | Tests may pass locally but fail in release/runtime. | Run release checks on Python >=3.11 and set Render `PYTHON_VERSION`. [VERIFIED: environment probe] [CITED: https://render.com/docs/python-version] |

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| Python | Tests/local dev | Wrong version | 3.10.10 local; project requires >=3.11 | Use Python >=3.11 for release/Render. [VERIFIED: environment probe] |
| pytest | Dashboard tests | yes | 7.3.1 installed; latest PyPI 9.1.0 | Keep existing unless planner decides upgrade with checkpoint. [VERIFIED: environment probe] [VERIFIED: pip index versions pytest] |
| Streamlit | Dashboard runtime/AppTest | yes | 1.58.0 | Add/pin runtime dependency with checkpoint. [VERIFIED: environment probe] |
| Render CLI | Optional deployment automation | no | - | Use Render Dashboard/Blueprint docs; not blocking research. [VERIFIED: environment probe] |
| LEAN CLI | QuantConnect operator context | yes | 1.0.225 | Operator-run only; tests must not deploy. [VERIFIED: environment probe] |
| Graph context | Semantic planning context | no | `.planning/graphs/graph.json` absent | Continue with code/docs reads. [VERIFIED: graph check] |

**Missing dependencies with no fallback:** none for research/planning. [VERIFIED: environment probe]
**Missing dependencies with fallback:** Render CLI is absent; use Render Dashboard/Blueprint docs. [VERIFIED: environment probe]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Recommended Object Store dashboard keys use a project-prefixed `dashboard/latest.json` style. | QuantConnect Data Access/Export Recommendation | Planner may need to adjust key names to match algorithm implementation. |
| A2 | Single-password auth should use `hmac.compare_digest` and store only an authenticated boolean in Streamlit session state. | Auth/Session Recommendation | Implementation may need a different cookie/session approach if Streamlit session state is insufficient on Render. |
| A3 | Cache TTL default of 120 seconds is appropriate. | Cache/Stale/Error Recommendation | Too short may add unnecessary QuantConnect API calls; too long may delay operator display. |
| A4 | Status enum should include `fresh`, `stale`, `error`, `not_configured`, `not_available`, and `auth_required`. | Cache/Stale/Error Recommendation | Planner may need to align enum names with existing model conventions. |
| A5 | Dashboard auth tests may use fake env mappings like `test-password`. | Auth/Session Recommendation | If project adopts a stricter no-password-fixture policy, tests need hashed/sentinel fixture values instead. |
| A6 | V5/V6 controls use typed parsing and Python standard `hmac.compare_digest`. | Security Domain | Security tasks may need stronger controls if dashboard exposure expands beyond single-user v1. |

## Open Questions

None blocking. [VERIFIED: 09-CONTEXT.md]

Recommended defaults are sufficient for planning: QuantConnect Cloud API live reads plus Object Store dashboard exports, Render env-var password, Streamlit session state, 120-second display cache, stale warning at 10 minutes, strong stale/error at 30 minutes, and no mutation controls. [CITED: official sources listed above] [VERIFIED: 09-CONTEXT.md]

## Sources

### Primary
- QuantConnect API Reference: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference
- QuantConnect Authentication: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/authentication
- QuantConnect Read Live Algorithm: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/read-live-algorithm
- QuantConnect Live Portfolio State: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/read-live-algorithm/portfolio-state
- QuantConnect Live Orders: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/read-live-algorithm/orders
- QuantConnect Live Insights: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/read-live-algorithm/insights
- QuantConnect Live Logs: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/read-live-algorithm/logs
- QuantConnect List Live Algorithms: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/list-live-algorithms
- QuantConnect Object Store API Get: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/object-store-management/get-object-store-file
- QuantConnect Writing Algorithms Object Store: https://www.quantconnect.com/docs/v2/writing-algorithms/object-store
- QuantConnect Organization Object Store: https://www.quantconnect.com/docs/v2/cloud-platform/organizations/object-store
- Streamlit cache data: https://docs.streamlit.io/develop/api-reference/caching-and-state/st.cache_data
- Streamlit session state: https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state
- Streamlit tabs: https://docs.streamlit.io/develop/api-reference/layout/st.tabs
- Streamlit secrets management: https://docs.streamlit.io/develop/concepts/connections/secrets-management
- Streamlit authentication: https://docs.streamlit.io/develop/api-reference/user/st.login
- Streamlit AppTest: https://docs.streamlit.io/develop/api-reference/app-testing
- Render web services: https://render.com/docs/web-services
- Render env vars/secrets: https://render.com/docs/configure-environment-variables
- Render health checks: https://render.com/docs/health-checks
- Render Python version: https://render.com/docs/python-version
- Render free plan: https://render.com/docs/free

### Codebase Sources
- `AGENTS.md`
- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `.planning/PROJECT.md`
- `.planning/STATE.md`
- `.planning/phases/09-render-dashboard/09-CONTEXT.md`
- `.planning/phases/08-quantconnect-paper-trading-and-telegram/08-VERIFICATION.md`
- `dashboard/app.py`
- `dashboard/models.py`
- `dashboard/safety_view.py`
- `tests/test_dashboard.py`
- `config/dashboard.yaml`
- `marketpilot/quantconnect_paper.py`
- `marketpilot/reconciliation.py`
- `marketpilot/telegram.py`
- `marketpilot/notification_events.py`
- `marketpilot/fx.py`
- `docs/paper_trading.md`
- `docs/telegram.md`
- `docs/safety.md`
- `docs/configuration.md`

## Metadata

**Confidence breakdown:**
- QuantConnect data path: MEDIUM - official endpoints verified, but exact dashboard Object Store export schema is not implemented yet.
- Streamlit/Render deployment: MEDIUM - official docs verified and local Streamlit is installed, but Render deployment was not executed.
- Auth/cache/stale design: MEDIUM - aligned with official Streamlit APIs and Phase 9 decisions, but implementation still needs tests.
- Package audit: MEDIUM - PyPI confirms package versions, but GSD legitimacy seam flags packages as `SUS`; planner must add checkpoints before dependency changes.

**Research date:** 2026-06-15
**Valid until:** 2026-07-15 for architecture; re-check official QuantConnect/Render/Streamlit docs immediately before implementation-sensitive endpoint or deployment changes.
