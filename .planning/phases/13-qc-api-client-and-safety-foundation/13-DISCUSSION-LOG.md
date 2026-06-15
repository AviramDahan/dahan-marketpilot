# Phase 13: QC API Client & Safety Foundation — Discussion Log

**Date:** 2026-06-16
**Duration:** ~3 minutes
**Areas discussed:** 1 of 4

## Areas Presented

1. ~~ארכיטקטורת הלקוח~~ — not selected
2. ~~אסטרטגיית Safety ו-Endpoint Blocking~~ — not selected
3. **ניהול Credentials ו-Config** — DISCUSSED ✓
4. ~~Error Handling ו-Retry Policy~~ — not selected

## Discussion: Credential Management & Config

### Q1: How does QCApiClient receive credentials?
- **Options:** ENV only (recommended) | Config class with fallback chain | Secrets manager
- **User decision:** ENV only. Will configure manually with Codex assistance.
- **Notes:** No fallback chain needed, no secrets manager. Keep it simple.

### Q2: What happens if credentials are missing?
- **Options:** Lazy fail (error on first call) | Eager fail (error at startup) | Graceful degrade
- **User decision:** Alert on absence and fail immediately ("להתריע על החוסר ולהכשיל")
- **Notes:** Pipeline should not start without valid credentials.

### Q3: Validate credentials against QC at startup?
- **Options:** Verify against QC at init (recommended) | Local format check only
- **User decision:** Verify against QC at init — make GET /authenticate call.

### Q4: Environment variable names
- **Options:** QC_USER_ID + QC_API_TOKEN | QUANTCONNECT_USER_ID + QUANTCONNECT_API_TOKEN
- **User decision:** `QUANTCONNECT_USER_ID` + `QUANTCONNECT_API_TOKEN` (longer, more explicit)

## Agent Discretion (not discussed — left for researcher/planner)

- Client architecture (single class vs namespaced methods)
- Exception hierarchy depth
- Safety enforcement implementation details (URL allowlist vs deny-by-default)
- Retry budget and circuit breaker specifics
