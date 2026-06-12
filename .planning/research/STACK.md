# Research: Stack

## Scope

This research captures official source anchors for Dahan MarketPilot planning. It does not approve any specific production API usage. Implementation phases must re-verify exact APIs, signatures, limits, permissions, and pricing before code is written.

## Official Sources Checked

- [QuantConnect/Lean](https://github.com/QuantConnect/Lean) - official LEAN engine repository. The repository describes LEAN as an event-driven algorithmic trading platform and lists Apache-2.0 licensing.
- [QuantConnect/Tutorials](https://github.com/QuantConnect/Tutorials) - official tutorial notebooks and examples for LEAN concepts, also Apache-2.0 licensed.
- [QuantConnect/lean-cli](https://github.com/QuantConnect/lean-cli) - official CLI for LEAN local and cloud workflows. The README describes cloud backtest and cloud live commands and notes installation via `pip install --upgrade lean`.
- [QuantConnect Documentation v2](https://www.quantconnect.com/docs/v2/) - primary official documentation entry point.
- [QuantConnect Cloud API Reference](https://www.quantconnect.com/docs/v2/cloud-platform/api-reference) - official REST API reference for cloud server communication, project management, compiling code, backtest management, live management, and related endpoints.
- [QuantConnect Notifications](https://www.quantconnect.com/docs/v2/writing-algorithms/live-trading/notifications) - official notification docs covering email, FTP, SMS, Telegram, webhooks, and receive-notification behavior.
- [QuantConnect Object Store](https://www.quantconnect.com/docs/v2/writing-algorithms/object-store) - official docs for saving, reading, deleting, caching, and file-path access for Object Store data.
- [Render Docs](https://render.com/docs) - official Render documentation for web services, static sites, private services, workers, cron jobs, and deployment options.
- [Streamlit Documentation](https://docs.streamlit.io/) - official Streamlit documentation for app development, API reference, deployment guidance, and knowledge base.
- [Telegram Bot API](https://core.telegram.org/bots/api) - official Telegram Bot API reference, including `sendMessage`.

## Stack Decisions For Planning

- Core algorithm engine: QuantConnect LEAN.
- Cloud execution authority: QuantConnect Cloud Backtesting and QuantConnect Cloud Paper Trading.
- Local/cloud workflow: LEAN CLI, GitHub, and GitHub Actions after API verification.
- Dashboard: Streamlit hosted as a Render Web Service.
- Notifications: Telegram alerts, with official QuantConnect notification support and/or Telegram Bot API verified during implementation.
- State authority: QuantConnect, not Render, GitHub, Excel, SQLite, CSV, or JSON.
- Reports: generated artifacts only; never authoritative paper portfolio state.

## Implementation Warnings

- Do not invent QuantConnect classes, methods, REST endpoints, or notification APIs.
- Do not assume a tutorial is current without checking current official documentation and source.
- Do not copy code from official repositories unless license requirements and attribution are documented.
- Do not implement real-money trading paths, broker adapters, or dashboard order controls.
- Do not create fake backtest or portfolio artifacts.
