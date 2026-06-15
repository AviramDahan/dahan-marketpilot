# Safety

SIMULATED PAPER TRADING ONLY - NOT FINANCIAL ADVICE

Dahan MarketPilot is simulated Paper Trading only. The central safety rule is
that `PAPER_TRADING_ONLY` must remain true and unsafe configuration must fail
closed.

Disallowed features:

- Real-money trading or instructions for activating it.
- Real broker adapters, real-money credentials, live-money order support, or
  hidden live-trading switches.
- Leverage, margin, short selling, options, futures, cryptocurrency, Forex, or
  unsupported asset classes.
- Manual dashboard order submission or any Render control that modifies orders.
- Fake Backtest results, fake Paper Trading results, fake portfolio values, or
  unverified profitability claims.

QuantConnect is the source of truth for simulated cash, portfolio equity,
holdings, open positions, orders, fills, Paper Trading state, algorithm status,
and QuantConnect Backtest results. Render must remain read-only and must not
maintain authoritative active portfolio state. Telegram is a notification channel only;
Telegram delivery failures must not control or block trading safety logic.

Phase 2 QuantConnect verification is documented in
`docs/quantconnect_verification.md`. That verification may reference LEAN CLI
and Cloud API documentation, but it does not authorize repository credentials,
broker settings, cloud backtest execution, Paper Trading deployment, or live
deployment.

Credentials and secrets must never appear in source files, logs, tests, reports,
planning artifacts, documentation examples, or chat. Use approved secret stores
for QuantConnect, GitHub Actions, Telegram, Render, and dashboard secrets.

Every user-facing dashboard page and generated report must display the exact
disclaimer phrase above.

Volume Breakout remains setup evidence only in Phase 4. It may emit valid or
rejected setup results, numeric evidence, explanations, and rejection reasons,
but it must not contain orders, sizing, portfolio state, backtest results,
Telegram delivery, live or Paper deployment, credentials, fake performance, or
profitability claims.

## Multi-Timeframe Safety

Phase 4.1 does not authorize production orders, Paper Trading, Telegram
delivery, real Backtests, broker adapters, portfolio mutation, stops, targets,
or fake performance artifacts.

Strategy modes are signal-evidence modes only:

- `daily_only`
- `daily_filter_4h_setup`
- `daily_filter_4h_setup_1h_optional`

They are separate from environment modes such as `backtest`, `shadow`, and
`paper`. 1H confirmation is optional support only and cannot independently
create a trade or override failed Daily, invalid 4H, `RISK_OFF`, stale data,
hard rejection, or invalid reward/risk.

## Scoring And Ranking Safety

Phase 5 scoring and ranking are audit-only. Classification labels are evidence
labels, not trade instructions. Ranked candidates contain no entry, stop,
target, quantity, order, broker, Paper Trading, Telegram delivery, credential,
fake backtest, portfolio mutation, or profitability behavior.

## Risk Safety

Phase 6 risk decisions are still paper-only domain decisions. They may calculate
candidate quantity and rejection reasons, but they do not submit orders, mutate
QuantConnect state, create an authoritative local portfolio, send Telegram
messages, or enable real-money behavior.

Order lifecycle objects are also audit mirrors only. They can model intent,
state transitions, and idempotency, but they cannot submit, cancel, replace, or
modify real or Paper orders.

Exit plans are obligations for existing positions, not execution commands.
`RISK_OFF` blocks new long entries but must not erase existing stop, target,
partial-close, full-close, or recovery obligations.

The Phase 6 audit journal is append-only recovery context only. It must not
become a hidden portfolio database. On restart mismatch, QuantConnect remains
authoritative and local state is marked mismatched.

Notification-domain events are transport-neutral and cannot control risk,
order, or exit safety. Real Telegram delivery remains deferred to Phase 8, and
delivery failures must never block protective logic.

## Backtesting And Validation Safety

Phase 7 does not approve Paper Trading. QuantConnect Cloud/LEAN remains the
authority for real backtest results. Local harnesses can test timing and
contract behavior only.

Backtest artifacts must be labeled as real QuantConnect output, fixture,
schema, example, or not-run. Only documented real QuantConnect output may carry
performance metrics. Missing QuantConnect access must be represented as
`not_run` with prerequisites or commands, not substituted with invented
results.

Activation gates block Paper eligibility by default unless real documented
validation passes every required gate. Preview backtest notifications are
historical, transport-neutral domain events for the fake collector only and
cannot control safety logic.

## QuantConnect Paper Trading Safety

Phase 8 Paper Trading contracts are simulated-paper only. The only allowed
brokerage target is QuantConnect Paper Trading. Real brokerage adapters,
real-money credentials, live-money switching, leverage, margin, short selling,
options, futures, cryptocurrency, Forex, and local fake deployment state remain
forbidden.

Missing QuantConnect account, organization access, Paper Trading Live Node,
project ID, API credentials, or data-provider settings must produce typed
`not_configured` or `not_run` states. They must never be replaced by fake
deployment IDs, fake Paper portfolios, or invented Paper results.

Deployment command text is operator-run documentation only. Tests must not run
`lean cloud live deploy`, start a Live Node, require credentials, or contact
QuantConnect.

Restart recovery must also remain QuantConnect-first. When QuantConnect Paper
state is unavailable, local audit history is context only, new entries are
blocked, and explicit recovery is required before Paper entries resume. Local
JSONL records must not be promoted into authoritative Paper cash, holdings,
orders, fills, deployment status, algorithm status, or performance.

If QuantConnect shows a filled Paper position without required stop, target, or
protective state, protective recovery blocks new entries and preserves exit
obligations until explicit recovery is completed. Notification or Telegram
delivery failure must not change that decision or unblock entries.

## Telegram Safety

Telegram is an outbound delivery adapter over `NotificationDomainEvent`.
Delivery can be disabled, missing secrets, duplicate-suppressed, locally
rate-limited, rejected by Telegram, fail on network errors, or succeed. Those
outcomes are typed notification results only. They must never approve Paper
modes, submit orders, modify order lifecycle states, clear reconciliation
mismatches, erase exit obligations, or unblock protective recovery.
Delivery result records explicitly mark `controls_safety_logic: false` and
`delivery_required_for_safety: false`.

Telegram messages are plain text by default, concise, sanitized, and include
the simulated-paper warning where relevant. They must not include credentials,
secret values, copied token or chat target values, or profitability guarantees.
Historical backtests remain real-Telegram-disabled and use fake collector
previews only unless a future explicit preview path is designed.

## Dashboard Safety

The Render dashboard is password-protected with a single external
`DASHBOARD_PASSWORD` environment variable. No raw dashboard password may appear
in repository files, docs, tests, logs, reports, planning artifacts, or chat.
No dashboard data is rendered before login, and authentication failures must be
redacted.

The dashboard action surface is limited to view, refresh, login, and logout.
It must remain Overview-first on mobile and read-only for every page.

Dashboard cache and FX display are display-only. Cached data must be labeled
with source/cache timestamps and stale status. NIS conversion is never an
accounting source; USD remains authoritative.

## CI/CD And Release Safety

GitHub Actions must keep the default CI path deterministic, offline, and
secret-free. The `tests.yml` workflow runs local pytest only and must not require
QuantConnect, Telegram, Render, broker credentials, internet access, or real
market data.

All workflow actions must be official GitHub-owned actions pinned to full
40-character commit SHAs. Mutable action tags and third-party workflow actions
are not approved for the release foundation.

GitHub Actions Secrets may store these names for guarded external workflows:

- `QUANTCONNECT_USER_ID`
- `QUANTCONNECT_API_TOKEN`
- `QUANTCONNECT_PROJECT_ID`
- `DASHBOARD_HEALTH_URL`
- `DASHBOARD_PASSWORD`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

Repository files may name those secrets, but must never contain their values.

QuantConnect sync/backtest, dashboard health, and other external service checks
are guarded release checks. Unexecuted external checks are not passed checks.
When prerequisites are missing, rejected, or intentionally withheld, the
evidence status must be `skipped` or `not_run`.
