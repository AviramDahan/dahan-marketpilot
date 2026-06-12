# Agent Instructions

## Dahan MarketPilot

This repository uses GSD for planning and implementation. Before starting any phase work, read:

- `.planning/PROJECT.md`
- `.planning/REQUIREMENTS.md`
- `.planning/ROADMAP.md`
- `.planning/STATE.md`

Follow the active GSD phase. Do not modify completed phases without a change plan. Use focused commits only for verified tasks and only when the user explicitly asks for commits.

The user has approved commits starting after the initial planning setup. From this point forward, use focused commits for completed, verified planning or implementation units. Keep GSD planning artifacts, technical documentation, and user-facing project docs synchronized before committing.

For AI handoff and synchronization rules, read `docs/AI-COLLABORATION.md` before phase work or when resuming a partially completed task.

Communication with the user must be in Hebrew. All source code, identifiers, file names, configuration keys, tests, technical documentation, commit messages, GSD planning artifacts, and project files must be written in English.

Verify current official QuantConnect APIs before using them. Verify external package legitimacy before adding dependencies. Never invent QuantConnect APIs, LEAN classes, Cloud API endpoints, package behavior, or tutorial details.

Never invent Backtest results, Paper Trading results, portfolio values, or profitability claims. Never claim that a strategy is profitable without real generated artifacts that support the claim. Distinguish executed checks from unexecuted checks.

The product is simulated Paper Trading only. Never add real-broker code, real-money credentials, leverage, margin, short selling, options, futures, cryptocurrency trading, or a hidden live-trading switch. Keep Render read only and never add dashboard order-entry controls.

QuantConnect is the source of truth for simulated cash, portfolio equity, holdings, open positions, orders, fills, Paper Trading state, algorithm status, and QuantConnect Backtest results. Do not replace active Paper Trading portfolio state with GitHub, Render local storage, CSV, JSON, SQLite, Excel, or ad hoc files.

Telegram failures must remain independent from trading safety. Notification delivery errors must not stop protective trading logic, and Telegram secrets must never appear in logs, docs, tests, reports, or chat.

Never bypass failing tests, remove a test merely to make CI pass, expose credentials, or write secrets into repository files. Document assumptions, limitations, execution assumptions, data limitations, bias risks, and blockers honestly.

When credentials, paid subscriptions, QuantConnect setup, Telegram bot setup, Render setup, or GitHub Secrets are required, request user action in Hebrew and do not ask the user to paste secrets into chat.

<!-- GSD:project-start source:PROJECT.md -->

## Project

**Dahan MarketPilot**

Dahan MarketPilot is a cloud-hosted US-equities swing-trading research, backtesting, and simulated Paper Trading product. It scans a dynamic universe of liquid US common equities, identifies predefined explainable swing setups, ranks candidates with transparent numeric evidence, validates rules through QuantConnect Cloud Backtests, and runs only approved simulated Paper Trading strategies in QuantConnect Cloud.

The product is for research, validation, audit, and read-only monitoring. It must never execute real-money trades, never expose credentials, never fabricate performance, and never imply guaranteed profitability.

**Core Value:** The system must provide an auditable paper-only swing-trading workflow where every signal, backtest, paper action, portfolio display, alert, and report is traceable to verified rules and numeric evidence.

### Constraints

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

<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->

## Technology Stack

## Scope

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

<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->

## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->

## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->

## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->

## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:

- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->

## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
