# Phase 13: QC API Client & Safety Foundation — Context

**Gathered:** 2026-06-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 13 delivers an authenticated QuantConnect REST API client with defense-in-depth safety preventing any real-money operations. It creates the `marketpilot/qc_api.py` module with typed endpoint wrappers, HMAC authentication, retry logic, credential redaction, and layered paper-only enforcement.

Phase 13 must NOT: deliver signals, deploy algorithms, sync portfolio state, schedule anything, or introduce any new database. Those belong to Phases 14-17.
</domain>

<decisions>
## Implementation Decisions

### Credential Management & Configuration

- **D-01:** Credentials sourced exclusively from environment variables: `QUANTCONNECT_USER_ID` and `QUANTCONNECT_API_TOKEN`. No fallback chain, no config files, no secrets manager integration.
- **D-02:** `python-dotenv` loads `.env` in local development only. In production (Render Background Worker), env vars are set natively via Render dashboard.
- **D-03:** If either `QUANTCONNECT_USER_ID` or `QUANTCONNECT_API_TOKEN` is missing at QCApiClient creation time, the system raises a clear error with an informative message and fails immediately. No graceful degradation — the pipeline should not start without valid credentials.
- **D-04:** On creation, QCApiClient performs a lightweight GET /authenticate call to QuantConnect to validate credentials are real and the account exists. Invalid credentials fail loudly at startup, not on first real API call.
- **D-05:** User will configure env vars manually on local machine. No automated provisioning or secrets rotation workflow needed at this stage.

### Safety (Carried Forward from v1.0 + Research)

- **D-06:** `PAPER_TRADING_ONLY = True` remains a hardcoded constant in `marketpilot/constants.py` (already exists). Runtime startup assertion validates it. Pre-commit hook rejects any commit setting it to False.
- **D-07:** QCApiClient validates `PAPER_TRADING_ONLY` before constructing any deployment/modification endpoint URL. This is defense-in-depth on top of the constant.
- **D-08:** No code path in this phase accepts or stores live brokerage credentials. The only env vars consumed are the QC Cloud API paper-trading credentials.
- **D-09:** All credentials are redacted in logs and error outputs. The HTTP client wrapper masks Authorization headers and token patterns in any logged exception.
- **D-10:** A `detect-secrets` pre-commit hook is added (or extended from v1.0) to prevent credential leakage into the repository.

### Prior Decisions Carried Forward (Phase 8)

- **D-11:** QuantConnect remains authoritative for all portfolio state — local records are audit mirrors only (Phase 8 D-11).
- **D-12:** All existing 433 v1.0 tests must pass unchanged after v1.1 implementation; new modules use lazy imports to avoid breaking existing test isolation (SAFE-03).
</decisions>

<code_context>
## Reusable Codebase Assets

- `marketpilot/constants.py` — `PAPER_TRADING_ONLY = True` already defined
- `marketpilot/safety.py` — Existing fail-closed validation with `SECRET_HINTS`, `FORBIDDEN_TRUE_KEYS`; the QC API client can leverage this module for credential redaction patterns
- `marketpilot/quantconnect_paper.py` — Frozen dataclasses: `QuantConnectHolding`, `QuantConnectPaperOrder`, `QuantConnectPaperFill`, `QuantConnectPaperSnapshot` — the API client should return these existing types
- `marketpilot/reconciliation.py` — Already imports from `quantconnect_paper.py`; downstream consumer of API client results
- `marketpilot/notification_events.py` — Existing alert pipeline for system incidents (reusable for auth failures)
- `marketpilot/configuration.py` — Existing config loading patterns to follow for consistency
</code_context>

<canonical_refs>
## Canonical References

- `.planning/research/STACK.md` — Stack decisions: requests, tenacity 9.x, python-dotenv 1.0.x
- `.planning/research/ARCHITECTURE.md` — QCApiClient module design, interface specification
- `.planning/research/PITFALLS.md` — Pitfalls 1-8 directly relevant (safety bypass, credential leakage, rate limits, schema changes, algorithm ID mapping, token expiry)
- `.planning/REQUIREMENTS.md` — Requirements API-01..05, SAFE-01, SAFE-02
- `.planning/phases/08-quantconnect-paper-trading-and-telegram/08-CONTEXT.md` — Prior QC decisions D-06..D-15
</canonical_refs>

<deferred>
## Deferred Ideas

(None raised during discussion)
</deferred>
