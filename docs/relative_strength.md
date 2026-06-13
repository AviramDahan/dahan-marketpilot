# Relative Strength Leader

Phase 5 implements Relative Strength Leader as an independently testable
setup-only evaluator and as confirmation evidence for other setups.

The setup uses SPY as the hard relative-strength benchmark. RS20 and RS60
versus SPY must be positive. QQQ RS20 and RS60 are measured for every candidate
as evidence only; weak QQQ relative strength cannot reject a symbol by itself.

Relative Strength Leader rejects:

- unready, stale, missing, invalid, or incomplete data
- `RISK_OFF`
- weak SPY RS20 or RS60
- broken EMA50/EMA200 structure
- insufficient average dollar volume
- excessive ATR percentage
- excessive EMA20 extension
- excessive 52-week-high distance, default 15.0%

The output is `SetupResult` evidence only. There is no score, rank,
classification, entry, stop, target, quantity, order, portfolio mutation,
Telegram delivery, Paper deployment, Live deployment, credential, fake backtest,
or profitability claim.

Phase 5 scoring may consume this evidence. Combined Swing remains disabled until
all individual setup validation and later backtesting gates pass.
