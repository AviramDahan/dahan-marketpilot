# Dahan MarketPilot

## What This Is

Dahan MarketPilot is a cloud-hosted US-equities swing-trading research, backtesting, and simulated Paper Trading product. It scans a dynamic universe of liquid US common equities, identifies predefined explainable swing setups, ranks candidates with transparent numeric evidence, validates rules through QuantConnect Cloud Backtests, and runs only approved simulated Paper Trading strategies in QuantConnect Cloud.

The product is for research, validation, audit, and read-only monitoring. It must never execute real-money trades, never expose credentials, never fabricate performance, and never imply guaranteed profitability.

## Core Value

The system must provide an auditable paper-only swing-trading workflow where every signal, backtest, paper action, portfolio display, alert, and report is traceable to verified rules and numeric evidence.

## Requirements

### Validated

- Phase 1 established repository foundation files, MIT licensing, attribution tracking, disclaimer, setup/config/testing docs, and AI collaboration instructions.
- Phase 1 implemented central paper-only safety validation, safe YAML loading, FX seed calculation, and deterministic offline tests.
- Phase 1 added safe foundational models and tests that protect required project safety files.
- Phase 1 added a minimal non-trading QuantConnect shell and read-only dashboard shell with static safety tests.
- Phase 4.1 implemented the multi-timeframe signal foundation: central StrategyMode config, timeframe-aware completed-bar contracts, generalized setup timing metadata, MTF setup evidence, deterministic tests, and synchronized documentation.

### Active

- [x] Establish a repository foundation with licensing, attribution, disclaimer, AGENTS.md, and GSD planning context.
- [x] Enforce simulated Paper Trading only through central safety configuration and validation.
- [ ] Use QuantConnect LEAN and QuantConnect Cloud as the authoritative engine for backtests and Paper Trading state.
- [ ] Build long-only US-equity swing strategies with dynamic universe selection, market regime controls, transparent scoring, no look-ahead behavior, and controlled strategy modes for daily-only and Daily/4H/optional-1H evidence.
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
- Expected holding period is approximately 3-30 trading days. `daily_only` preserves completed daily-bar signals, while MTF modes may use completed 4H primary setup bars with optional completed 1H confirmation.
- Supported regular strategy modes are exactly `daily_only`, `daily_filter_4h_setup`, and `daily_filter_4h_setup_1h_optional`. Strategy mode is separate from environment modes such as `backtest`, `shadow`, and `paper`.
- GSD is the planning and execution system for this repository. Phase work must read `.planning/PROJECT.md`, `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`, and `.planning/STATE.md`.

## Constraints

- **Language**: Project files, code, tests, identifiers, configuration, and GSD artifacts are English. User-facing chat communication is Hebrew.
- **Safety**: `PAPER_TRADING_ONLY = True` must be central, validated, and not silently overridden.
- **Trading scope**: v1 is US-listed common equities, long-only, swing-trading only, simulated Paper Trading only. No day trading, scalping, 5m/15m/HFT behavior, or mandatory same-day exits are allowed.
- **Strategy modes**: `daily_only` is the default, compatibility mode, and benchmark. `daily_filter_4h_setup` uses Daily as a mandatory filter and completed 4H bars as primary setup signals. `daily_filter_4h_setup_1h_optional` adds optional 1H confirmation only.
- **Execution timing**: Signals from completed bars must execute only at a later valid tradable price unless a phase proves a different execution assumption is technically valid. Future bars, incomplete bars, future context, and unrealistic same-bar assumptions are prohibited.
- **Data authority**: QuantConnect is authoritative for paper portfolio state and backtest results.
- **Dashboard**: Render Streamlit dashboard is read-only and password-protected.
- **Credentials**: No credentials or secrets may be written to repository files or chat.
- **Testing**: Core unit tests must use deterministic offline fixtures where practical and must not require QuantConnect, Telegram, Render, broker credentials, internet, or real market access.
- **Research**: Current official QuantConnect, Render, Streamlit, and Telegram documentation must be verified before implementation APIs are used.
- **Licensing**: Reused code must be licensed, attributed, and recorded in `NOTICE` and `THIRD_PARTY_NOTICES.md` where required.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Use GSD for project planning and phased execution. | The user explicitly requested official GSD Core skills and a complete planning roadmap before implementation. | Active |
| Initialize a Git repository and use focused commits after user approval. | The user approved commits after initial planning. | Active |
| Store the master specification at `docs/Dahan-MarketPilot-Master-Spec.md`. | The user explicitly required this path and required the full specification, not a vague summary. | Active |
| License Dahan MarketPilot source code as MIT. | Phase 1 selected MIT and added `LICENSE`, `NOTICE`, and `THIRD_PARTY_NOTICES.md`. | Active |
| Keep QuantConnect as paper portfolio source of truth. | Prevents Render, GitHub, CSV, JSON, SQLite, Excel, or local storage from becoming hidden live state. | Active |
| Keep Render read-only. | Prevents manual order entry or state mutation outside QuantConnect. | Active |
| Treat Telegram as non-authoritative notification infrastructure. | Alerts are important, but delivery failure must not stop trading-safety logic. | Active |
| Ask technical questions with a `You choose` option when the AI can safely decide. | The user requested this preference during Phase 1 discussion. | Active |
| Insert Phase 4.1 before Phase 5 for multi-timeframe signal foundations. | Strategy modes and timeframe responsibilities must be explicit before scoring/ranking consumes setup evidence. | Active |
| Keep `daily_only` as default and benchmark. | Preserves completed Phase 1-4 behavior and provides a clean comparison baseline. | Active |
| Treat 4H as primary setup timeframe in MTF modes and 1H as optional confirmation only. | Maintains swing-trading intent while avoiding independent intraday trade creation. | Active |
| Use market-open anchored, RTH-only 4H bars as the recommended initial policy. | US equity sessions are 6.5 hours; partial-session bars must be explicit and non-signal by default. | Active |

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

- Exact QuantConnect subscription and Paper Trading Live Node requirements.
- Exact QuantConnect Cloud API endpoints and permissions after implementation-phase verification.
- Exact data export method from QuantConnect to the read-only dashboard.
- Whether Telegram alerts should use QuantConnect built-in notifications, a separate Telegram service, or both after official API verification.
- FX rate source, staleness threshold, and operational update process.
- Earnings-risk data source and policy.
- Sector/industry classification source and availability in QuantConnect.
- Render authentication approach beyond password protection.
- Final 4H alignment safety after implementation tests and backtesting.
- Whether a 2H alternative is justified if 4H alignment proves unsafe or too sparse.
- MTF score weights and thresholds; these must wait for backtesting and sensitivity validation.

## Deferred Future Setup Ideas

- Breakout Retest.
- Volatility Contraction / Base Breakout.

## Evolution

After each phase:

1. Move shipped and verified requirements to Validated when appropriate.
2. Move invalidated or descoped requirements to Out of Scope with reasons.
3. Add decisions that constrain future work to the Key Decisions table.
4. Refresh Context and Constraints if implementation reality changes.

---
*Last updated: 2026-06-14 after Phase 4.1 execution and verification.*
