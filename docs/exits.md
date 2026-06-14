# Exits

Phase 6 exit plans are paper-only obligations for existing positions. They
model stops, targets, partial exits, trailing policy, and maximum holding
periods without submitting orders.

Initial stops derive from setup evidence such as structural invalidation, swing
low, breakout level, or explicit stop price. Targets are calculated from risk
per share and default to at least 2R.

Partial exits are modeled as future events only. Trailing stops are represented
by configuration and domain objects, but are disabled by default until
validation.

Existing positions remain governed by their exit obligations even when market
regime changes to `risk_off`. Risk-off blocks new long entries; it does not
erase stops, targets, partial closes, full closes, or recovery obligations.
