---
status: incomplete
phase: 01-foundation-and-safety
plan: "04"
updated: 2026-06-12
---

# Phase 01 Plan 04 User Setup

This setup is only for optional external LEAN compile verification.

## QuantConnect / LEAN

Required outside the repository:

- Docker installed and running.
- LEAN CLI installed.
- `lean login` completed by the user.
- `lean init` completed in an appropriate LEAN workspace if required.
- QuantConnect organization access if the account requires it.

Do not store QuantConnect credentials, API tokens, account IDs, or organization
secrets in this repository or in chat.

## Verification Command

When prerequisites are available, run:

```powershell
lean build
```

Current automated tests do not require this external setup.
