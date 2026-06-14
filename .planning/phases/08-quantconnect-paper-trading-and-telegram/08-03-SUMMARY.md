---
phase: 08-quantconnect-paper-trading-and-telegram
plan: "03"
subsystem: telegram-notifications
tags: [telegram, notifications, sendMessage, secrets, safety, tdd]
requires:
  - phase: 08-quantconnect-paper-trading-and-telegram/08-02
    provides: "Notification-domain events emitted by reconciliation and protective recovery remain non-authoritative"
  - phase: 06-portfolio-risk-and-order-lifecycle
    provides: "NotificationDomainEvent, fake collector, deduplication, and local rate limiting contracts"
provides:
  - "Secret-safe Telegram config loader using non-secret env var names and injected external secret sources"
  - "Typed Telegram delivery results for disabled, missing token, missing chat ID, duplicate, rate-limited, rejected, failed, and delivered outcomes"
  - "Official Bot API sendMessage transport boundary with fake/injected HTTP client support"
  - "Plain-text sanitized Telegram formatter with paper-only warning and no paid broadcast fields"
  - "Tests proving Telegram delivery failure remains observational and cannot alter protective recovery decisions"
affects: [phase-08, phase-09-dashboard, phase-10-cicd-security]
tech-stack:
  added: []
  patterns:
    - "External Telegram secrets are resolved through injected mappings or environment variables only"
    - "Telegram HTTP is isolated behind an injectable sendMessage boundary"
    - "Delivery result parsing is typed and sanitized before logging or reporting"
key-files:
  created:
    - marketpilot/telegram.py
    - tests/test_telegram_transport.py
    - tests/test_telegram_secret_handling.py
    - tests/test_telegram_safety.py
    - docs/telegram.md
  modified:
    - marketpilot/notification_events.py
    - config/notifications.yaml
    - docs/notification_events.md
    - docs/configuration.md
    - docs/safety.md
key-decisions:
  - "Telegram real delivery remains disabled by default and requires explicit config plus externally supplied token and chat target."
  - "NotificationDomainEvent remains the internal contract; Telegram sendMessage is only an outbound adapter."
  - "Telegram delivery success, failure, duplicate suppression, and rate limiting are typed observations only and cannot control Paper gates, lifecycle, reconciliation, or protective recovery."
  - "Messages are plain text by default, include the simulated-paper warning, omit paid broadcast fields, and remove secret-like or unsafe profitability text."
patterns-established:
  - "Use notification_delivery_key(event) for event_type plus correlation_id deduplication."
  - "Use fake or injected HTTP clients for all Telegram tests; never call real Telegram from tests."
requirements-completed: [TEL-03, TEL-04, TEL-05, TEL-06]
test-results:
  targeted: "python -m pytest tests/test_telegram_transport.py tests/test_telegram_secret_handling.py tests/test_telegram_safety.py -q -> 13 passed"
  broad: "python -m pytest -q -> passed"
  static-scan: "rg token/chat/paid-broadcast/profitability patterns -> only env var names, source field names, fake test placeholders, and safety prohibition text; no real Telegram token/chat ID found"
metrics:
  duration: "9 min"
  completed: 2026-06-14
---

# Phase 08 Plan 03: Telegram Integration Path Summary

**Secret-safe Telegram Bot API sendMessage delivery with typed outcomes, local dedup/rate limiting, and failure isolation from Paper Trading safety.**

## Performance

- **Duration:** 9 min
- **Started:** 2026-06-14T14:57:58Z
- **Completed:** 2026-06-14T15:06:51Z
- **Tasks:** 3
- **Files modified:** 10

## Accomplishments

- Added `marketpilot.telegram` with `TelegramConfig`, `TelegramDeliveryStatus`, `TelegramDeliveryResult`, `TelegramDeliveryService`, and `format_telegram_message`.
- Added config loading from `config/notifications.yaml` that permits only non-secret reference names in repository config and resolves bot token/chat target from injected external secret sources or process environment.
- Added typed delivery results for disabled, missing token, missing chat ID, duplicate suppression, local rate limiting, Telegram API rejection, network failure, and delivered messages.
- Added plain-text `sendMessage` payload generation without `parse_mode` or paid broadcast fields.
- Added tests proving Telegram delivery failures, duplicates, and local rate limits are notification-only outcomes and do not alter protective recovery decisions.

## Task Commits

1. **Task 1 RED:** `b04db4b` test(08-03): add failing telegram secret handling tests
2. **Task 1 GREEN:** `0bc0702` feat(08-03): add telegram secret-safe config loader
3. **Task 2 RED:** `be0d4ab` test(08-03): add failing telegram transport tests
4. **Task 2 GREEN:** `609617e` feat(08-03): add telegram sendMessage delivery results
5. **Task 3 RED:** `325df36` test(08-03): add failing telegram safety isolation tests
6. **Task 3 GREEN:** `dcfe692` feat(08-03): isolate telegram delivery from safety decisions

## Files Created/Modified

- `marketpilot/telegram.py` - Telegram config loader, delivery result enum/dataclass, sendMessage service, HTTP boundary, and formatter.
- `marketpilot/notification_events.py` - Added `notification_delivery_key()` and reused it in `NotificationDeduplicator`.
- `config/notifications.yaml` - Added safe Telegram message length setting while keeping delivery disabled by default and secrets external.
- `tests/test_telegram_secret_handling.py` - Secret-safe config, external secret lookup, redaction, and committed config tests.
- `tests/test_telegram_transport.py` - Typed delivery result and fake HTTP sendMessage tests.
- `tests/test_telegram_safety.py` - Failure-isolation, dedup, rate-limit, and sanitized message tests.
- `docs/telegram.md` - Telegram setup, secret policy, delivery status, and safety semantics.
- `docs/notification_events.md` - Delivery key, dedup, rate-limit, and non-authority documentation.
- `docs/configuration.md` - Notifications config documentation.
- `docs/safety.md` - Telegram safety boundary documentation.

## Verification

- `python -m pytest tests/test_telegram_secret_handling.py -q` -> 5 passed.
- `python -m pytest tests/test_telegram_transport.py -q` -> 4 passed.
- `python -m pytest tests/test_telegram_safety.py -q` -> 4 passed.
- `python -m pytest tests/test_telegram_transport.py tests/test_telegram_secret_handling.py tests/test_telegram_safety.py -q` -> 13 passed.
- `python -m pytest -q` -> passed.
- `python --version` -> Python 3.10.10.
- `python -m pytest --version` -> pytest 7.3.1.
- Static scan for Telegram token/chat ID shapes, paid broadcast fields, parse modes, and unsafe profitability text found no real Telegram credentials. Findings were env var names, source field names, fake test placeholders, and safety prohibition text.

No test called real Telegram, required internet access, or required bot token/chat ID values.

## Decisions Made

- Real Telegram delivery is opt-in and remains disabled unless `telegram_enabled: true` and both external secret values are available.
- `delivery_required_for_safety` must remain false; Telegram can never be required for safety-critical operation.
- `NotificationDomainEvent` stays transport-neutral; Telegram returns adapter-specific delivery results instead of changing domain event contracts.
- Plain text remains the default Telegram message format to avoid Markdown escaping failures and accidental formatting ambiguity.
- Local deduplication uses `event_type|correlation_id`; rate limiting is conservative and local, with no paid broadcast support.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- An initial `apply_patch` call targeted the session's original working directory instead of the requested repository. The stray test file was deleted immediately, the worktree root was verified, and the patch was reapplied with an absolute path inside the repository before any commit.
- Local Python remains 3.10.10 while `pyproject.toml` expects Python >=3.11 for strict release validation. The targeted and broad suites passed in the available local environment.

## Known Stubs

None introduced by this plan. Stub scan findings outside the plan scope were pre-existing placeholder documentation/tests and dataclass optional `None` defaults.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: telegram_secret_boundary | `marketpilot/telegram.py` | External bot token/chat target values can enter only through injected env/secret sources; mitigated by committed config rejection and result/config redaction. |
| threat_flag: telegram_outbound_network | `marketpilot/telegram.py` | New outbound Bot API sendMessage boundary; mitigated by explicit enablement, missing-secret typed results, injected fake client tests, and no test network calls. |
| threat_flag: telegram_api_response_parsing | `marketpilot/telegram.py` | External API responses are untrusted; mitigated by typed parsing of ok/error_code/description/retry_after into sanitized delivery results. |

## TDD Gate Compliance

- RED commits exist for all three TDD tasks.
- GREEN commits exist after each RED commit.
- No refactor commit was needed.

## User Setup Required

Real Telegram delivery still requires operator-managed setup outside repository files: create a bot through BotFather, identify the chat target, and store token/chat target values in approved secret stores such as QuantConnect secure parameters, GitHub Secrets, Render environment variables, or local environment variables. Do not paste secrets into chat or commit them.

## Next Phase Readiness

Plan 08-04 can build full alert coverage, regime transition suppression, daily summaries, and historical-backtest real-Telegram-disabled behavior on top of the typed Telegram delivery adapter and stable domain-event dedup key.

## Self-Check: PASSED

- Verified all created and modified files exist.
- Verified task commits exist: `b04db4b`, `0bc0702`, `be0d4ab`, `609617e`, `325df36`, `dcfe692`.

---
*Phase: 08-quantconnect-paper-trading-and-telegram*
*Completed: 2026-06-14*
