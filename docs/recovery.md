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
