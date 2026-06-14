# Recovery

Phase 6 restart recovery is modeled as a comparison between local audit mirror
state and a future QuantConnect snapshot. When they disagree, QuantConnect wins,
local state is marked mismatched, and a recovery event is emitted.

Split and delisting handling are safe placeholders in Phase 6. They create
rejection or recovery-required states and defer full execution behavior until
QuantConnect integration is verified.
