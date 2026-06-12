# Dahan MarketPilot

## What This Is

Dahan MarketPilot is a cloud-hosted US-equities swing-trading research, backtesting, and simulated Paper Trading product. It scans a dynamic universe of liquid US common equities, identifies predefined explainable swing setups, ranks candidates with transparent numeric evidence, validates rules through QuantConnect Cloud Backtests, and runs only approved simulated Paper Trading strategies in QuantConnect Cloud.

The product is for research, validation, audit, and read-only monitoring. It must never execute real-money trades, never expose credentials, never fabricate performance, and never imply guaranteed profitability.

## Core Value

The system must provide an auditable paper-only swing-trading workflow where every signal, backtest, paper action, portfolio display, alert, and report is traceable to verified rules and numeric evidence.

## Requirements

### Validated

(None yet - project is newly initialized and no product implementation has shipped.)

### Active

- [ ] Establish a repository foundation with licensing, attribution, disclaimer, AGENTS.md, and GSD planning context.
- [ ] Enforce simulated Paper Trading only through central safety configuration and validation.
- [ ] Use QuantConnect LEAN and QuantConnect Cloud as the authoritative engine for backtests and Paper Trading state.
- [ ] Build long-only daily-resolution US-equity swing strategies with dynamic universe selection, market regime controls, transparent scoring, and no look-ahead behavior.
- [ ] Validate strategies with realistic backtesting, chronological validation, explicit fees/slippage, activation gates, and non-fabricated artifacts.
- [ ] Send Telegram alerts for configured signals, paper orders, fills, stops, targets, regime changes, daily summaries, and system incidents without letting notification failures compromise trading safety.
- [ ] Provide a password-protected, mobile-friendly, read-only Render Streamlit dashboard that displays QuantConnect-sourced paper state in USD and NIS.
- [ ] Maintain complete audit trails, reports, tests, and operational documentation.

### Out of Scope

- Real-money trading - explicitly forbidden for v1 and by product safety policy.
- Real brokerage integrations - would create a live-money path and violate the paper-only constraint.
- Leverage, margin borrowing, short selling, options, futures, cryptocurrency, Forex, day trading, HFT, and intraday scalping - outside v1 scope and risk model.
- Manual dashboard order buttons - Render must remain read-only.
- AI models making unauditable trade decisions - v1 decisions must be deterministic and rule-based.
- Claims of profitability or guaranteed returns - prohibited unless supported by real generated artifacts, and even then must not imply future certainty.
- Fake backtests, fake portfolios, or synthetic performance claims - prohibited.
- Automatic migration from Paper Trading to live trading - prohibited.

## Context

- The project starts from an empty repository named `dahan-marketpilot`.
- The master specification is stored at `docs/Dahan-MarketPilot-Master-Spec.md`.
- The requested v1 architecture uses QuantConnect LEAN, QuantConnect Cloud Backtesting and Paper Trading, GitHub, GitHub Actions, Render, Streamlit, and Telegram.
- QuantConnect must remain the source of truth for simulated cash, holdings, orders, fills, paper performance, algorithm status, and QuantConnect Backtest results.
- Render is a read-only dashboard and must not maintain an independent simulated portfolio.
- Telegram is a notification channel and must not be required for trading-safety logic to continue.
- The starting simulated budget is 100,000 NIS, converted to USD at a configurable launch FX rate. Later FX changes may affect NIS display but must not rewrite historical USD accounting.
- Expected holding period is approximately 3-30 trading days, with primary signals generated only from completed daily bars.
- GSD is the planning and execution system for this repository. Phase work must read `.planning/PROJECT.md`, `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`, and `.planning/STATE.md`.

## Constraints

- **Language**: Project files, code, tests, identifiers, configuration, and GSD artifacts are English. User-facing chat communication is Hebrew.
- **Safety**: `PAPER_TRADING_ONLY = True` must be central, validated, and not silently overridden.
- **Trading scope**: v1 is US-listed common equities, long-only, daily primary signal resolution, simulated Paper Trading only.
- **Execution timing**: Signals from completed daily bars must execute only at a later valid tradable price unless a phase proves a different execution assumption is technically valid.
- **Data authority**: QuantConnect is authoritative for paper portfolio state and backtest results.
- **Dashboard**: Render Streamlit dashboard is read-only and password-protected.
- **Credentials**: No credentials or secrets may be written to repository files or chat.
- **Testing**: Core unit tests must use deterministic offline fixtures where practical and must not require QuantConnect, Telegram, Render, broker credentials, internet, or real market access.
- **Research**: Current official QuantConnect, Render, Streamlit, and Telegram documentation must be verified before implementation APIs are used.
- **Licensing**: Reused code must be licensed, attributed, and recorded in `NOTICE` and `THIRD_PARTY_NOTICES.md` where required.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Use GSD for project planning and phased execution. | The user explicitly requested official GSD Core skills and a complete planning roadmap before implementation. | Pending execution |
| Initialize a Git repository but create no commits. | GSD new-project expects Git initialization when none exists, while the user explicitly forbids commits unless requested. | Pending execution |
| Store the master specification at `docs/Dahan-MarketPilot-Master-Spec.md`. | The user explicitly required this path and required the full specification, not a vague summary. | Pending execution |
| Keep QuantConnect as paper portfolio source of truth. | Prevents Render, GitHub, CSV, JSON, SQLite, Excel, or local storage from becoming hidden live state. | Pending execution |
| Keep Render read-only. | Prevents manual order entry or state mutation outside QuantConnect. | Pending execution |
| Treat Telegram as non-authoritative notification infrastructure. | Alerts are important, but delivery failure must not stop trading-safety logic. | Pending execution |
| Do not implement Phase 1 during initialization. | The user requested planning only and explicitly said to stop before Phase 1. | Active |

## External Actions Required Later

- Create or confirm a QuantConnect account.
- Select an appropriate QuantConnect subscription and confirm Cloud Backtesting/Paper Trading capabilities.
- Enable or provision a QuantConnect Paper Trading Live Node if required.
- Create QuantConnect API credentials and store them only in approved secret stores.
- Add GitHub Actions Secrets for QuantConnect and deployment workflows.
- Create a Telegram bot through BotFather.
- Obtain a Telegram chat ID.
- Store Telegram secrets securely, never in repository files or chat.
- Create a Render Web Service for the Streamlit dashboard.
- Add Render environment variables and a dashboard password through Render secrets/configuration.
- Confirm the launch FX rate source and timestamp for the starting NIS to USD conversion.

## Unresolved Decisions

- Final project license for Dahan MarketPilot source code.
- Exact QuantConnect subscription and Paper Trading Live Node requirements.
- Exact QuantConnect Cloud API endpoints and permissions after implementation-phase verification.
- Exact data export method from QuantConnect to the read-only dashboard.
- Whether Telegram alerts should use QuantConnect built-in notifications, a separate Telegram service, or both after official API verification.
- FX rate source, staleness threshold, and operational update process.
- Earnings-risk data source and policy.
- Sector/industry classification source and availability in QuantConnect.
- Render authentication approach beyond password protection.

## Evolution

After each phase:

1. Move shipped and verified requirements to Validated when appropriate.
2. Move invalidated or descoped requirements to Out of Scope with reasons.
3. Add decisions that constrain future work to the Key Decisions table.
4. Refresh Context and Constraints if implementation reality changes.

---
*Last updated: 2026-06-12 after initial GSD project initialization.*
