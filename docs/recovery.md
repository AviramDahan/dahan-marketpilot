# Recovery

Phase 6 restart recovery is modeled as a comparison between local audit mirror
state and a future QuantConnect snapshot. When they disagree, QuantConnect wins,
local state is marked mismatched, and a recovery event is emitted.

Split and delisting handling are safe placeholders in Phase 6. They create
rejection or recovery-required states and defer full execution behavior until
QuantConnect integration is verified.

## QuantConnect-First Restart Recovery

Phase 8 restart recovery rebuilds active Paper position and order context from
the QuantConnect Paper snapshot first. Reconstructed positions, order IDs, fill
counts, deployment status, algorithm status, and performance context come from
QuantConnect only.

Local JSONL audit records may be attached after the QuantConnect rebuild to
explain intent history and prior lifecycle observations. They remain context
only and must not become the source of truth for cash, equity, holdings,
orders, fills, or active Paper state.

If QuantConnect is unavailable, credentials are missing, deployment has not
run, or no authoritative snapshot is available, recovery blocks new entries and
requires explicit operator recovery. The system must return a typed
`not_configured`, `not_run`, or `recovery_required` style status instead of
pretending that local audit history is complete authority.

## Protective Recovery

A filled QuantConnect Paper position with active exit obligations must have
protective state for both stop and target handling. If the QuantConnect
snapshot shows a filled position but no matching protective stop/target state,
protective recovery blocks new entries, preserves exit obligations, and marks
explicit recovery required for the affected symbols.

Protective recovery may create a high-severity notification-domain event, but
the notification path is non-authoritative. A fake collector or future Telegram
delivery failure must not change whether protective recovery is required, must
not erase stop or target obligations, and must not unblock new entries.

## Release-Era Recovery

CI/CD and dashboard evidence do not change trading authority. QuantConnect
remains authoritative for simulated Paper cash, equity, holdings, orders, fills,
deployment status, algorithm status, and real QuantConnect backtest artifacts.

If a GitHub Actions run cannot reach QuantConnect, lacks GitHub Actions Secrets,
or has an unapproved Lean package checkpoint, record the external check as
`not_run` or `skipped`. Do not treat missing external evidence as approval to
resume entries.

If Paper state is unavailable, stale, mismatched, or recovery-required, block
new entries until an operator completes explicit recovery against QuantConnect.
Dashboard cache, local audit JSONL, GitHub Actions summaries, Telegram delivery,
and Render health status are context only and must not be promoted into
authoritative Paper state.
