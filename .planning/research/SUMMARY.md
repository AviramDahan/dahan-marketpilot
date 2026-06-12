# Research Summary

## Stack

Dahan MarketPilot should be planned around QuantConnect LEAN for algorithm/backtest logic, QuantConnect Cloud for authoritative Backtest and Paper Trading execution, GitHub and GitHub Actions for repository workflows, Render Web Service plus Streamlit for a read-only dashboard, and Telegram for notifications. Official source anchors were checked for QuantConnect LEAN, QuantConnect Tutorials, `lean-cli`, QuantConnect docs, QuantConnect Cloud API, QuantConnect Notifications, QuantConnect Object Store, Render docs, Streamlit docs, and Telegram Bot API.

## Table Stakes

- Paper-only safety guard and unsafe configuration rejection.
- QuantConnect source-of-truth architecture.
- Dynamic universe, SPY/QQQ regime, indicator readiness, and no-look-ahead behavior.
- Separate setup validation before any Combined Swing strategy.
- Backtesting validation gates before Paper Trading.
- Telegram alerts with duplicate suppression, rate limiting, and fake transports for tests.
- Read-only mobile dashboard with QuantConnect-sourced data, USD/NIS display, FX warning, and secret masking.
- Documentation, licensing, disclaimer, and third-party attribution.

## Watch Out For

- Re-verify official QuantConnect APIs before implementation.
- Do not infer current API details from old tutorials.
- Avoid same-bar fill assumptions.
- Do not treat Render, GitHub, reports, CSV, JSON, SQLite, Excel, or local files as active paper portfolio state.
- Do not ask for or store secrets during planning.
- Do not create fake Backtest results, fake portfolio data, or profitability claims.
- Do not implement Phase 1 during this initialization.

## Sources

- [QuantConnect/Lean](https://github.com/QuantConnect/Lean)
- [QuantConnect/Tutorials](https://github.com/QuantConnect/Tutorials)
- [QuantConnect/lean-cli](https://github.com/QuantConnect/lean-cli)
- [QuantConnect Documentation v2](https://www.quantconnect.com/docs/v2/)
- [QuantConnect Cloud API Reference](https://www.quantconnect.com/docs/v2/cloud-platform/api-reference)
- [QuantConnect Notifications](https://www.quantconnect.com/docs/v2/writing-algorithms/live-trading/notifications)
- [QuantConnect Object Store](https://www.quantconnect.com/docs/v2/writing-algorithms/object-store)
- [Render Docs](https://render.com/docs)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
