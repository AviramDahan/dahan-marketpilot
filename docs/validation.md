# Validation

Phase 7 validation models chronological validation and sensitivity analysis as
contracts that can run offline.

Chronological validation checks whether each required report window is
available. Missing windows produce an `unavailable` result with explicit
reasons, not a pass.

Sensitivity analysis compares configured scenarios across fees, slippage, fill
timing, and threshold assumptions. These scenarios are comparative validation
data only. They are not profitability promises and do not approve Paper Trading
by themselves.

Validation gates later combine chronological coverage, no-look-ahead checks,
artifact source, benchmark availability, risk checks, assumptions, and report
completeness.
