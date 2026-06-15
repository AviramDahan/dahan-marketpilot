# Phase 13: QC API Client & Safety Foundation - Research

**Researched:** 2026-06-16
**Domain:** QuantConnect REST API v2 integration, HMAC authentication, retry patterns, credential safety
**Confidence:** HIGH

## Summary

Phase 13 delivers a single `marketpilot/qc_api.py` module that authenticates to the QuantConnect Cloud REST API using HMAC-SHA256 timestamped headers, wraps the required endpoints with typed responses using existing frozen dataclasses, enforces paper-only safety at the client layer, and redacts credentials from all log outputs. The module uses `tenacity` for exponential backoff with jitter on transient failures, and a `detect-secrets` pre-commit hook prevents credential leakage.

The QuantConnect API uses a non-standard authentication scheme: SHA-256 hash of `apiToken:unixTimestamp`, then `userId:hashedToken` base64-encoded as a Basic Auth header, plus a `Timestamp` header. All API calls are POST requests (even reads) to `https://www.quantconnect.com/api/v2/`. There is no official Python SDK — raw `requests` with this custom auth is the documented approach.

**Primary recommendation:** Build a single `QCApiClient` class with HMAC auth helper, URL allowlist enforcement, tenacity retry decorator, and credential-redacting logging filter. Return existing `quantconnect_paper.py` frozen dataclasses from all endpoint wrappers.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Credentials sourced exclusively from environment variables: `QUANTCONNECT_USER_ID` and `QUANTCONNECT_API_TOKEN`. No fallback chain, no config files, no secrets manager integration.
- **D-02:** `python-dotenv` loads `.env` in local development only. In production (Render Background Worker), env vars are set natively via Render dashboard.
- **D-03:** If either credential is missing at QCApiClient creation time, raise clear error and fail immediately. No graceful degradation.
- **D-04:** On creation, QCApiClient performs a lightweight GET /authenticate call to validate credentials. Invalid credentials fail loudly at startup.
- **D-05:** User will configure env vars manually on local machine.
- **D-06:** `PAPER_TRADING_ONLY = True` remains a hardcoded constant in `marketpilot/constants.py`. Runtime startup assertion validates it. Pre-commit hook rejects any commit setting it to False.
- **D-07:** QCApiClient validates `PAPER_TRADING_ONLY` before constructing any deployment/modification endpoint URL. Defense-in-depth.
- **D-08:** No code path accepts or stores live brokerage credentials.
- **D-09:** All credentials redacted in logs and error outputs. HTTP client masks Authorization headers and token patterns.
- **D-10:** `detect-secrets` pre-commit hook added to prevent credential leakage.
- **D-11:** QuantConnect remains authoritative for all portfolio state.
- **D-12:** All existing 433 v1.0 tests must pass unchanged. New modules use lazy imports.

### Copilot's Discretion
- Internal module structure within `qc_api.py` (single file vs sub-package)
- Exact retry count and backoff parameters
- Specific logging filter implementation approach
- Test fixture structure

### Deferred Ideas (OUT OF SCOPE)
(None raised during discussion)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| API-01 | System authenticates to QC REST API using HMAC credentials from env vars | HMAC auth pattern documented below; `get_auth_headers()` implementation verified against QC official docs |
| API-02 | System refuses to construct/call any live/real-money endpoint; PAPER_TRADING_ONLY gate at client layer | URL allowlist pattern + `PAPER_TRADING_ONLY` assertion before every mutating call |
| API-03 | All API calls use exponential backoff with jitter (tenacity); respect QC rate limits | tenacity 9.x decorator pattern with retry_if_exception_type for 429/5xx |
| API-04 | API credentials redacted in all logs and error outputs; detect-secrets hook prevents leakage | `CredentialRedactionFilter` logging filter + detect-secrets pre-commit config |
| API-05 | API client provides typed wrappers for: /live/create, /live/read, /live/update/stop, /live/update/liquidate, /live/orders/read, /backtests/create, /backtests/read | Endpoint specifications and response schemas documented below |
| SAFE-01 | PAPER_TRADING_ONLY hardcoded constant; runtime assertion; pre-commit hook rejects False | Existing `constants.py` already has it; add startup assertion in client + pre-commit grep hook |
| SAFE-02 | No code path accepts live brokerage credentials; defense-in-depth | URL allowlist blocks live brokerage endpoints; only `QuantConnectBrokerage` (paper) brokerage ID accepted |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| HMAC Authentication | API Client | — | Auth headers are generated per-request at the HTTP layer |
| Safety gate (PAPER_TRADING_ONLY) | API Client | Constants module | Defense-in-depth: client refuses before request leaves process |
| Retry / rate-limit handling | API Client | — | Transport-level concern, transparent to callers |
| Credential redaction | Logging infrastructure | API Client | Filter class attached to Python logging; client also masks in exceptions |
| Credential leakage prevention | Pre-commit hook | CI pipeline | detect-secrets runs on every commit; CI validates baseline |
| Response parsing | API Client | Existing dataclasses | Client maps JSON → existing `quantconnect_paper.py` types |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| requests | 2.32.x | HTTP client for QC REST API | Already installed; de facto standard for sync HTTP; QC docs use it |
| tenacity | 9.0.x | Retry with exponential backoff + jitter | Best-in-class retry library; decorator-based; jitter built-in |
| python-dotenv | 1.0.x+ | Load `.env` in local dev | Already installed (1.2.1); standard pattern |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| detect-secrets | 1.5.0 | Pre-commit secret scanning | Pre-commit hook; generates `.secrets.baseline` |
| pre-commit | 4.x | Git hook framework | Runs detect-secrets and PAPER_TRADING_ONLY grep hook |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| requests | httpx | Async support unnecessary; requests already in project |
| tenacity | backoff | Less maintained, fewer features |
| detect-secrets | trufflehog | trufflehog is heavier; detect-secrets integrates with pre-commit natively |

**Installation:**
```bash
pip install tenacity>=9.0.0 detect-secrets>=1.5.0 pre-commit>=4.0.0
```

**Version verification:**
- requests 2.32.4 — already installed [VERIFIED: pip show]
- python-dotenv 1.2.1 — already installed [VERIFIED: pip show]
- tenacity 9.0.x — NOT installed, must be added [VERIFIED: pip shows not present]
- detect-secrets 1.5.0 — NOT installed, must be added [VERIFIED: pip shows not present]
- pre-commit — NOT installed, must be added [VERIFIED: pip shows not present]

## Package Legitimacy Audit

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| requests | PyPI | 13+ yrs | 300M+/wk | github.com/psf/requests | OK | Approved (already installed) |
| tenacity | PyPI | 8+ yrs | 40M+/wk | github.com/jd/tenacity | OK | Approved |
| python-dotenv | PyPI | 10+ yrs | 30M+/wk | github.com/theskumar/python-dotenv | OK | Approved (already installed) |
| detect-secrets | PyPI | 8+ yrs | 2M+/wk | github.com/Yelp/detect-secrets | OK | Approved |
| pre-commit | PyPI | 10+ yrs | 15M+/wk | github.com/pre-commit/pre-commit | OK | Approved |

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      CALLER (orchestrator / tests)                │
└────────────────────────────────┬────────────────────────────────┘
                                 │ calls typed methods
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                        QCApiClient                               │
│  ┌──────────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Safety Gate      │  │ HMAC Auth    │  │ Retry Logic      │  │
│  │ (PAPER_TRADING_  │  │ (SHA-256 +   │  │ (tenacity:       │  │
│  │  ONLY check +   │  │  timestamp + │  │  exp backoff +   │  │
│  │  URL allowlist) │  │  base64)     │  │  jitter)         │  │
│  └──────────────────┘  └──────────────┘  └──────────────────┘  │
│  ┌──────────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Credential       │  │ Request      │  │ Response Parser  │  │
│  │ Redaction        │  │ Builder      │  │ (JSON → frozen   │  │
│  │ (logging filter) │  │ (endpoints)  │  │  dataclasses)    │  │
│  └──────────────────┘  └──────────────┘  └──────────────────┘  │
└────────────────────────────────┬────────────────────────────────┘
                                 │ HTTP POST (requests)
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│          https://www.quantconnect.com/api/v2/                    │
│  /authenticate | /live/read | /live/create | /backtests/read     │
└─────────────────────────────────────────────────────────────────┘
```

### Recommended Project Structure
```
marketpilot/
├── qc_api.py              # Single module: QCApiClient, auth, safety, retry, parsing
├── constants.py           # PAPER_TRADING_ONLY = True (existing)
├── safety.py              # SECRET_HINTS, validate functions (existing)
├── quantconnect_paper.py  # Frozen dataclasses for responses (existing)
└── ...

.pre-commit-config.yaml    # NEW: detect-secrets + PAPER_TRADING_ONLY hooks
.secrets.baseline           # NEW: detect-secrets baseline file
```

### Pattern 1: HMAC Authentication Header Generation
**What:** Generate per-request authentication headers for QuantConnect API
**When to use:** Every API request to QC Cloud
**Example:**
```python
# Source: https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/authentication
from base64 import b64encode
from hashlib import sha256
from time import time


def _get_auth_headers(user_id: str, api_token: str) -> dict[str, str]:
    """Generate timestamped HMAC auth headers for QuantConnect API."""
    timestamp = str(int(time()))
    time_stamped_token = f"{api_token}:{timestamp}".encode("utf-8")
    hashed_token = sha256(time_stamped_token).hexdigest()
    authentication = f"{user_id}:{hashed_token}".encode("utf-8")
    encoded_auth = b64encode(authentication).decode("ascii")
    return {
        "Authorization": f"Basic {encoded_auth}",
        "Timestamp": timestamp,
    }
```

### Pattern 2: Tenacity Retry with Rate Limit Respect
**What:** Exponential backoff with jitter for transient failures
**When to use:** Wrapping all QC API HTTP calls
**Example:**
```python
# Source: tenacity docs (https://tenacity.readthedocs.io/)
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)


@retry(
    retry=retry_if_exception_type((QCRateLimitError, QCServerError)),
    wait=wait_exponential_jitter(initial=1, max=30, jitter=2),
    stop=stop_after_attempt(4),
    reraise=True,
)
def _make_request(self, method: str, endpoint: str, payload: dict) -> dict:
    ...
```

### Pattern 3: URL Allowlist Safety Gate
**What:** Block all live/real-money endpoints at the client level
**When to use:** Before constructing any API request URL
**Example:**
```python
# Defense-in-depth: only these endpoints are callable
_ALLOWED_ENDPOINTS: frozenset[str] = frozenset({
    "authenticate",
    "live/read",
    "live/list",
    "backtests/create",
    "backtests/read",
    "backtests/list",
    "projects/read",
})

# These require PAPER_TRADING_ONLY assertion AND brokerage ID validation
_PAPER_GATED_ENDPOINTS: frozenset[str] = frozenset({
    "live/create",
    "live/update/stop",
    "live/update/liquidate",
})


def _validate_endpoint(self, endpoint: str) -> None:
    """Refuse to call any endpoint not in the allowlist."""
    from marketpilot.constants import PAPER_TRADING_ONLY

    if endpoint not in _ALLOWED_ENDPOINTS | _PAPER_GATED_ENDPOINTS:
        raise QCSafetyError(f"Endpoint '{endpoint}' is not in the safety allowlist")

    if endpoint in _PAPER_GATED_ENDPOINTS:
        if PAPER_TRADING_ONLY is not True:
            raise QCSafetyError("PAPER_TRADING_ONLY must be True for deployment endpoints")
```

### Pattern 4: Credential Redaction Logging Filter
**What:** Prevent credentials from appearing in any log output
**When to use:** Attached to root logger or module-level logger
**Example:**
```python
import logging
import re


class CredentialRedactionFilter(logging.Filter):
    """Redact API tokens and auth headers from log records."""

    _PATTERNS = (
        re.compile(r"(Authorization:\s*Basic\s+)\S+", re.IGNORECASE),
        re.compile(r"(QUANTCONNECT_API_TOKEN[=:]\s*)\S+", re.IGNORECASE),
        re.compile(r"(api_token[=:]\s*['\"]?)\S+", re.IGNORECASE),
    )
    _REDACTED = "***REDACTED***"

    def filter(self, record: logging.LogRecord) -> bool:
        if record.msg:
            msg = str(record.msg)
            for pattern in self._PATTERNS:
                msg = pattern.sub(rf"\1{self._REDACTED}", msg)
            record.msg = msg
        if record.args:
            args = tuple(
                self._redact_value(a) if isinstance(a, str) else a
                for a in (record.args if isinstance(record.args, tuple) else (record.args,))
            )
            record.args = args
        return True

    def _redact_value(self, value: str) -> str:
        for pattern in self._PATTERNS:
            value = pattern.sub(rf"\1{self._REDACTED}", value)
        return value
```

### Anti-Patterns to Avoid
- **Accepting deployment mode as a parameter:** Never let callers pass `"live"` vs `"paper"` — the client hardcodes paper-only.
- **Caching auth headers:** The timestamp must be fresh per request. Cached headers become invalid quickly.
- **Logging raw response bodies unconditionally:** QC responses may contain token-like strings in error messages.
- **Catching all exceptions in retry:** Only retry transient failures (429, 5xx, network). Never retry 401 or 400.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Retry with backoff | Custom while loops with sleep | `tenacity` decorator | Handles jitter, max attempts, exception filtering, logging |
| Secret detection in commits | grep scripts | `detect-secrets` + `pre-commit` | Maintained heuristics, baseline management, audit workflow |
| HMAC auth | — (must hand-roll) | Custom `_get_auth_headers()` | QC uses non-standard auth; no library wraps this |
| HTTP session management | Raw `requests.get/post` | `requests.Session` | Connection pooling, persistent headers, cookie handling |

**Key insight:** The HMAC authentication is unique to QuantConnect and must be implemented manually, but all other cross-cutting concerns (retry, secret detection) have mature library solutions.

## QuantConnect REST API v2 — Endpoint Specifications

### Authentication
| Property | Value |
|----------|-------|
| Base URL | `https://www.quantconnect.com/api/v2/` |
| Auth scheme | Custom HMAC: SHA-256 hash of `apiToken:unixTimestamp`, base64 of `userId:hash` as Basic Auth |
| Required headers | `Authorization: Basic <encoded>`, `Timestamp: <unix_seconds>` |
| Content-Type | `application/json` (all requests) |
| Method | All endpoints use POST (even reads) |

### Endpoint: `/authenticate` (GET — exception to POST rule)
- **Purpose:** Validate credentials are working
- **Request:** Headers only, no body
- **Response 200:** `{ "success": true }`
- **Response 401:** `www_authenticate` header
- **Phase 13 usage:** Called at `QCApiClient.__init__()` to fail fast on bad credentials [CITED: quantconnect.com/docs/v2/cloud-platform/api-reference/authentication]

### Endpoint: `/live/create` (POST)
- **Purpose:** Deploy algorithm to live paper node
- **Key request fields:** `versionId`, `projectId`, `compileId`, `nodeId`, `brokerage` (must be `{"id": "QuantConnectBrokerage", ...}`)
- **Response 200:** `{ "success": true, "deployId": "L-...", "projectId": ..., "live": {...} }`
- **Live status enum:** `DeployError | InQueue | Running | Stopped | Liquidated | Deleted | Completed | RuntimeError | Invalid | LoggingIn | Initializing | History`
- **Safety gate:** PAPER_TRADING_ONLY assertion + brokerage.id must be "QuantConnectBrokerage" [CITED: quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/create-live-algorithm]

### Endpoint: `/live/read` (POST)
- **Purpose:** Read live algorithm status, portfolio, orders
- **Request:** `{ "projectId": int, "deployId": "L-..." }`
- **Response 200:** Algorithm status, runtime statistics, holdings, cash, charts
- **Sub-endpoints (via query params):** Portfolio State, Orders, Logs
- **Phase 13 usage:** Read-only endpoint, no safety gate needed [CITED: quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/read-live-algorithm]

### Endpoint: `/live/update/stop` (POST)
- **Purpose:** Stop a running live algorithm
- **Request:** `{ "projectId": int }`
- **Response 200:** `{ "success": true }`
- **Safety gate:** PAPER_TRADING_ONLY assertion required [CITED: quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/create-live-algorithm (examples section)]

### Endpoint: `/live/update/liquidate` (POST)
- **Purpose:** Liquidate all positions in running algorithm
- **Request:** `{ "projectId": int }`
- **Response 200:** `{ "success": true }`
- **Safety gate:** PAPER_TRADING_ONLY assertion required [CITED: quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/create-live-algorithm (examples section)]

### Endpoint: `/live/read` (POST — orders sub-resource)
- **Purpose:** Retrieve order history and fills for live algorithm
- **Request:** `{ "projectId": int, "deployId": "L-..." }` with orders query
- **Response:** Order objects with `id`, `symbol`, `status`, `quantity`, `filledQuantity`, `price`, etc.
- **Phase 13 usage:** Typed wrapper returning `QuantConnectPaperOrder` / `QuantConnectPaperFill` [CITED: quantconnect.com/docs/v2/cloud-platform/api-reference/live-management/read-live-algorithm]

### Endpoint: `/backtests/create` (POST)
- **Purpose:** Launch a cloud backtest
- **Request:** `{ "projectId": int, "compileId": "...", "backtestName": "..." }`
- **Response 200:** `{ "success": true, "backtest": { "backtestId": "...", ... } }`
- **Phase 13 usage:** No safety gate needed (backtests don't trade real money) [CITED: quantconnect.com/docs/v2/cloud-platform/api-reference/backtest-management]

### Endpoint: `/backtests/read` (POST)
- **Purpose:** Read backtest results/statistics
- **Request:** `{ "projectId": int, "backtestId": "..." }`
- **Response 200:** Full backtest results with statistics
- **Phase 13 usage:** Read-only, no safety gate [CITED: quantconnect.com/docs/v2/cloud-platform/api-reference/backtest-management]

## Error Hierarchy Design

```python
class QCApiError(Exception):
    """Base exception for all QuantConnect API errors."""
    def __init__(self, message: str, status_code: int | None = None, response_body: str | None = None):
        self.status_code = status_code
        self.response_body = response_body  # redacted before storage
        super().__init__(message)


class QCAuthenticationError(QCApiError):
    """401 — credentials invalid or expired. NOT retryable."""
    pass


class QCRateLimitError(QCApiError):
    """429 — rate limit exceeded. Retryable with backoff."""
    pass


class QCServerError(QCApiError):
    """5xx — server-side transient error. Retryable."""
    pass


class QCClientError(QCApiError):
    """4xx (not 401/429) — bad request. NOT retryable."""
    pass


class QCNetworkError(QCApiError):
    """Connection/timeout errors. Retryable."""
    pass


class QCSafetyError(QCApiError):
    """Safety gate violation — endpoint blocked by PAPER_TRADING_ONLY."""
    pass
```

**Retry matrix:**
| Error Type | HTTP Code | Retryable | Action |
|------------|-----------|-----------|--------|
| QCAuthenticationError | 401 | No | Raise immediately, alert |
| QCRateLimitError | 429 | Yes | Exponential backoff with jitter |
| QCServerError | 500, 502, 503, 504 | Yes | Exponential backoff with jitter |
| QCClientError | 400, 403, 404 | No | Raise immediately |
| QCNetworkError | — (ConnectionError, Timeout) | Yes | Exponential backoff with jitter |
| QCSafetyError | — (local) | No | Raise immediately, never send request |

## Reusing Existing Dataclasses

The API client MUST return existing types from `marketpilot/quantconnect_paper.py`:

| QC API Response | Maps To | Factory Method Needed |
|-----------------|---------|----------------------|
| Live algorithm portfolio state | `QuantConnectPaperSnapshot` | `from_api_response(raw: dict)` |
| Individual holding | `QuantConnectHolding` | Direct construction |
| Order record | `QuantConnectPaperOrder` | Direct construction from JSON fields |
| Fill event | `QuantConnectPaperFill` | Direct construction |
| Algorithm status | `QuantConnectDeploymentStatus` / `QuantConnectAlgorithmStatus` | Enum mapping |

**Mapping notes:**
- QC API returns status as strings like `"Running"`, `"Stopped"`, `"DeployError"` — map to existing enum values
- QC API cash/holdings are in nested structures — flatten to match existing dataclass fields
- Add `QuantConnectDeploymentStatus.DEPLOYING` enum value for `"InQueue"` / `"LoggingIn"` / `"Initializing"` transitional states

## detect-secrets Pre-Commit Hook Setup

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.5.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
        exclude: \.secrets\.baseline$

  - repo: local
    hooks:
      - id: paper-trading-only-guard
        name: Reject PAPER_TRADING_ONLY = False
        entry: bash -c 'if grep -rn "PAPER_TRADING_ONLY\s*=\s*False" --include="*.py" .; then echo "ERROR: PAPER_TRADING_ONLY must never be set to False"; exit 1; fi'
        language: system
        types: [python]
        pass_filenames: false
```

**Setup commands:**
```bash
pip install detect-secrets pre-commit
detect-secrets scan > .secrets.baseline
pre-commit install
```

[CITED: github.com/Yelp/detect-secrets README]

## Common Pitfalls

### Pitfall 1: Stale Timestamp in Auth Headers
**What goes wrong:** If auth headers are generated once and reused across multiple requests (e.g., stored in a Session), the timestamp becomes stale and QC rejects the request.
**Why it happens:** Developer assumes Basic Auth is static; QC's HMAC scheme requires a fresh timestamp per request.
**How to avoid:** Generate headers inside `_make_request()` — never cache them. Use `requests.Session` for connection pooling but override `Authorization` + `Timestamp` per call.
**Warning signs:** Requests succeed initially then start returning 401 after a few seconds.

### Pitfall 2: Retrying 401 Authentication Errors
**What goes wrong:** If 401 is included in the retry list, the client retries indefinitely with invalid credentials, wasting time and potentially triggering account lockout.
**Why it happens:** Developer uses a blanket "retry all non-200" policy.
**How to avoid:** Only retry `429` and `5xx`. Treat `401` as a fatal error — raise immediately and alert.
**Warning signs:** CI tests hanging; QC account receiving many failed auth attempts.

### Pitfall 3: Logging Raw Exception with Credentials
**What goes wrong:** `requests.exceptions.HTTPError` includes the full request including Authorization header. `logging.exception("API failed")` dumps the token.
**Why it happens:** Python's default exception formatting includes __repr__ of the request.
**How to avoid:** Catch exceptions, extract only safe fields (status_code, url, response body), then raise a custom `QCApiError` with redacted information. Attach the `CredentialRedactionFilter` to the module logger.
**Warning signs:** Token strings appearing in pytest output or CI logs.

### Pitfall 4: Safety Gate Bypass via Direct requests.post()
**What goes wrong:** A developer bypasses `QCApiClient` and calls `requests.post(f"{BASE_URL}/live/create", ...)` directly, skipping the safety check.
**Why it happens:** Convenience during debugging or feature development.
**How to avoid:** (1) All QC API calls MUST go through `QCApiClient`. (2) Add a meta-test that greps codebase for direct requests to QC URLs outside `qc_api.py`. (3) Never expose `_base_url` or `_session` as public attributes.
**Warning signs:** New files importing `requests` and containing `quantconnect.com`.

### Pitfall 5: QC API Response Schema Drift
**What goes wrong:** QuantConnect updates their API response format (adds fields, renames keys). Client crashes on `KeyError` or silently returns `None`.
**Why it happens:** QC API isn't versioned with strict SemVer.
**How to avoid:** Use `.get()` with defaults for non-critical fields. Log warnings for unexpected response shapes. Pin test fixtures to known response format. Validate critical fields explicitly.
**Warning signs:** Intermittent `KeyError` or `TypeError` in production after a QC platform update.

## Code Examples

### Complete QCApiClient Skeleton
```python
# Source: QuantConnect official API docs + tenacity docs
"""QuantConnect Cloud REST API client with defense-in-depth safety."""

from __future__ import annotations

import logging
import os
from base64 import b64encode
from dataclasses import dataclass
from hashlib import sha256
from time import time
from typing import Any

import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from marketpilot.constants import PAPER_TRADING_ONLY

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class QCApiConfig:
    user_id: str
    api_token: str
    base_url: str = "https://www.quantconnect.com/api/v2"


class QCApiClient:
    """Authenticated QuantConnect Cloud API client with paper-only safety."""

    def __init__(self, config: QCApiConfig | None = None) -> None:
        if config is None:
            user_id = os.environ.get("QUANTCONNECT_USER_ID", "")
            api_token = os.environ.get("QUANTCONNECT_API_TOKEN", "")
            if not user_id or not api_token:
                raise QCAuthenticationError(
                    "QUANTCONNECT_USER_ID and QUANTCONNECT_API_TOKEN environment "
                    "variables are required but missing or empty."
                )
            config = QCApiConfig(user_id=user_id, api_token=api_token)

        self._config = config
        self._session = requests.Session()
        self._session.headers["Content-Type"] = "application/json"

        # Fail fast: validate credentials on creation
        self._validate_credentials()

    def _get_auth_headers(self) -> dict[str, str]:
        timestamp = str(int(time()))
        time_stamped_token = f"{self._config.api_token}:{timestamp}".encode("utf-8")
        hashed_token = sha256(time_stamped_token).hexdigest()
        auth_bytes = f"{self._config.user_id}:{hashed_token}".encode("utf-8")
        encoded_auth = b64encode(auth_bytes).decode("ascii")
        return {"Authorization": f"Basic {encoded_auth}", "Timestamp": timestamp}

    def _validate_credentials(self) -> None:
        """GET /authenticate to verify credentials work."""
        response = self._session.get(
            f"{self._config.base_url}/authenticate",
            headers=self._get_auth_headers(),
        )
        if response.status_code == 401:
            raise QCAuthenticationError("Invalid QC credentials — authentication failed")
        response.raise_for_status()
        data = response.json()
        if not data.get("success"):
            raise QCAuthenticationError("QC authentication returned success=false")
```

### Tenacity Retry Configuration
```python
# Source: tenacity docs
_RETRY_DECORATOR = retry(
    retry=retry_if_exception_type((QCRateLimitError, QCServerError, QCNetworkError)),
    wait=wait_exponential_jitter(initial=1, max=30, jitter=2),
    stop=stop_after_attempt(4),
    reraise=True,
    before_sleep=_log_retry_attempt,  # custom callback for observability
)
```

## Integration Test Strategy

### Mocking Patterns (No Real QC Credentials Needed)

| Layer | Tool | Purpose |
|-------|------|---------|
| Unit tests | `unittest.mock.patch` on `requests.Session` | Fast, deterministic; test all error paths |
| Integration tests | `responses` library (or `pytest-responses`) | Mock HTTP at transport level; validate URL construction, headers |
| Contract tests | Recorded fixtures (JSON files) | Pin known QC API response shapes; detect drift |
| Smoke tests (optional, CI weekly) | Real QC credentials in CI secrets | Canary for API changes; not blocking |

**Key pattern: fixture-based testing**
```python
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "qc_api"


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURES_DIR / f"{name}.json").read_text())


def test_authenticate_success():
    """QCApiClient authenticates successfully with valid credentials."""
    with patch("requests.Session") as mock_session_cls:
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_session.get.return_value = mock_response

        client = QCApiClient(QCApiConfig(user_id="12345", api_token="fake-token"))
        assert client is not None
```

**Test credentials convention:** All test fixtures use obviously fake values:
- User ID: `"99999"` or `"TEST-USER"`
- API Token: `"FAKE-TOKEN-DO-NOT-USE"`
- Deploy ID: `"L-00000000000000000000000000000000"`

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| QC used simple Basic Auth (userId:apiToken base64) | QC uses HMAC timestamped auth (SHA-256 of token:timestamp) | ~2023 | Must use timestamped hash, not raw token |
| `lean-cli` for API access | Raw requests (lean-cli is for local LEAN only) | Always | No SDK; direct HTTP is the official approach |
| `backoff` library | `tenacity` (more features, better maintained) | 2020+ | tenacity is the modern standard |
| Manual .gitignore for secrets | `detect-secrets` with baseline + pre-commit | 2019+ | Automated scanning catches what .gitignore misses |

**Deprecated/outdated:**
- QuantConnect's old simple Basic Auth (raw token in header) — replaced by HMAC timestamped scheme
- `lean-cli` as API wrapper — it's only for local LEAN engine, not Cloud REST API

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | QC rate limit is undocumented; 429 responses happen under burst load | Common Pitfalls | If QC has explicit documented limits, retry config should match them |
| A2 | QC API tokens don't expire (no OAuth rotation needed) | Architecture | If tokens expire, need re-auth logic in retry path |
| A3 | All QC read endpoints use POST method | Endpoint Specs | /authenticate uses GET; if other reads use GET, adjust client |
| A4 | 4 retry attempts with max 30s backoff is sufficient | Standard Stack | If QC rate limits require longer backoff windows, increase |

## Open Questions

1. **Exact QC rate limit thresholds**
   - What we know: 429 responses happen; no public documentation of exact limits
   - What's unclear: Requests per minute/hour, per-endpoint limits, burst allowance
   - Recommendation: Start conservative (4 retries, 1-30s exponential backoff with jitter); adjust based on production observations

2. **QC API response format for live algorithm orders sub-endpoint**
   - What we know: `/live/read` has sub-resources for Portfolio State, Orders, Insights, Logs
   - What's unclear: Exact JSON structure of order records within the live/read response
   - Recommendation: Build initial parser based on known fields from docs; add `.get()` with defaults for missing fields; log unknown structures

3. **`/authenticate` is GET while all other endpoints are POST**
   - What we know: Official docs show GET for authenticate, POST for everything else
   - What's unclear: Whether any other read endpoints also accept GET
   - Recommendation: Use GET only for /authenticate; POST for everything else per documentation

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Runtime | ✓ | 3.12.4 | — |
| requests | HTTP client | ✓ | 2.32.4 | — |
| python-dotenv | Local env loading | ✓ | 1.2.1 | — |
| tenacity | Retry logic | ✗ | — | Must install; no fallback |
| detect-secrets | Pre-commit secret scanning | ✗ | — | Must install; no fallback |
| pre-commit | Git hook framework | ✗ | — | Must install; no fallback |
| pytest | Test runner | ✓ | 8.x+ | — |

**Missing dependencies with no fallback:**
- `tenacity` — required for API-03 (retry with backoff); must be added to requirements.txt
- `detect-secrets` — required for API-04 (credential leakage prevention); must be added to requirements-dev.txt
- `pre-commit` — required for API-04 / SAFE-01 (pre-commit hooks); must be added to requirements-dev.txt

**Missing dependencies with fallback:**
- None

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.x |
| Config file | `pyproject.toml` [tool.pytest.ini_options] |
| Quick run command | `pytest tests/test_qc_api.py -x -q` |
| Full suite command | `pytest -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| API-01 | HMAC auth generates correct headers; validates at startup | unit | `pytest tests/test_qc_api.py::test_hmac_auth -x` | ❌ Wave 0 |
| API-02 | Safety gate blocks live endpoints; URL allowlist enforced | unit | `pytest tests/test_qc_api.py::test_safety_gate -x` | ❌ Wave 0 |
| API-03 | Retry on 429/5xx; no retry on 401/400 | unit | `pytest tests/test_qc_api.py::test_retry_logic -x` | ❌ Wave 0 |
| API-04 | Credentials never appear in logs; detect-secrets baseline clean | unit + integration | `pytest tests/test_qc_api.py::test_credential_redaction -x` | ❌ Wave 0 |
| API-05 | Typed wrappers parse responses into frozen dataclasses | unit | `pytest tests/test_qc_api.py::test_endpoint_wrappers -x` | ❌ Wave 0 |
| SAFE-01 | PAPER_TRADING_ONLY runtime assertion; pre-commit hook rejects False | unit + meta | `pytest tests/test_qc_api.py::test_paper_only_assertion -x` | ❌ Wave 0 |
| SAFE-02 | No live brokerage credential paths exist | meta-test (grep) | `pytest tests/test_qc_api.py::test_no_live_brokerage_paths -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_qc_api.py -x -q`
- **Per wave merge:** `pytest -q` (full 433+ test suite)
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_qc_api.py` — covers API-01 through API-05, SAFE-01, SAFE-02
- [ ] `tests/fixtures/qc_api/` — recorded API response fixtures (authenticate, live_read, etc.)
- [ ] `tenacity` package install: `pip install tenacity>=9.0.0`
- [ ] `detect-secrets` + `pre-commit` install: `pip install detect-secrets>=1.5.0 pre-commit>=4.0.0`

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | Yes | HMAC timestamped auth per QC spec; env-only credential sourcing |
| V3 Session Management | No | Stateless API calls; no session tokens |
| V4 Access Control | Yes | URL allowlist + PAPER_TRADING_ONLY gate blocks all real-money paths |
| V5 Input Validation | Yes | Response parsing validates expected fields; rejects malformed data |
| V6 Cryptography | Yes (SHA-256) | stdlib `hashlib.sha256` — never hand-roll; don't store raw tokens |
| V8 Data Protection | Yes | Credential redaction in logs; `.env` in `.gitignore`; detect-secrets baseline |
| V13 API Security | Yes | Rate limiting respect; auth headers regenerated per request; no credential caching |

### Known Threat Patterns for This Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Credential leakage in logs | Information Disclosure | `CredentialRedactionFilter` + detect-secrets pre-commit |
| Safety bypass via direct HTTP call | Elevation of Privilege | URL allowlist in client + meta-test grepping for raw QC URLs |
| Replay attack on stale auth header | Spoofing | Timestamp in header; QC server validates freshness |
| Rate limit exhaustion (DoS on own quota) | Denial of Service | tenacity backoff; conservative retry limits |
| PAPER_TRADING_ONLY override | Tampering | Hardcoded constant; runtime assertion; pre-commit hook; no env var override |

## Sources

### Primary (HIGH confidence)
- [QuantConnect API Reference — Authentication](https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/authentication) — HMAC auth scheme, header format, /authenticate endpoint
- [QuantConnect API Reference — Live Management](https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/live-management) — /live/create, /live/read, /live/update/stop, /live/update/liquidate endpoints
- [QuantConnect API Reference — Backtest Management](https://www.quantconnect.com/docs/v2/cloud-platform/api-reference/backtest-management) — /backtests/create, /backtests/read endpoints
- [Yelp/detect-secrets GitHub](https://github.com/Yelp/detect-secrets) — pre-commit config, baseline workflow, version 1.5.0
- Existing codebase: `marketpilot/quantconnect_paper.py`, `marketpilot/safety.py`, `marketpilot/constants.py`

### Secondary (MEDIUM confidence)
- [tenacity documentation](https://tenacity.readthedocs.io/) — retry patterns, wait strategies [ASSUMED based on training data]
- `.planning/research/STACK.md` — stack decisions locked by milestone research
- `.planning/research/PITFALLS.md` — pitfalls 1-8 directly applicable

### Tertiary (LOW confidence)
- QC rate limit behavior — inferred from pitfalls doc and community reports [ASSUMED]
- QC token expiry behavior — assumed non-expiring based on STACK.md note [ASSUMED]

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries verified installed or in PyPI; QC auth scheme confirmed from official docs
- Architecture: HIGH — existing codebase patterns clear; dataclass reuse confirmed; module location specified in ARCHITECTURE.md
- Pitfalls: HIGH — documented in milestone research and confirmed against QC API behavior
- Endpoint schemas: MEDIUM — verified from official docs but some sub-resource details require runtime discovery

**Research date:** 2026-06-16
**Valid until:** 2026-07-16 (QC API is stable; 30 days conservative)
