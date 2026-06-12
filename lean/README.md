# LEAN Shell

The current LEAN project is a minimal benchmark-only shell used for compile
shape verification. It subscribes to `SPY` and `QQQ`, emits the project
disclaimer, and contains no order, brokerage, Paper deployment, or live
deployment behavior.

Optional external verification:

```powershell
lean build
```

Run this only from a properly initialized LEAN workspace. It may require Docker,
LEAN CLI installation, `lean login`, `lean init`, and QuantConnect organization
access.

If any prerequisite is unavailable, record the check as not run.
Do not claim a successful compile without executing it, and do not store
QuantConnect credentials in this repository or chat.
