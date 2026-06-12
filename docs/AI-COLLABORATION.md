# AI Collaboration Guide

This project is designed to be worked on by Codex or another AI assistant across many sessions without losing context. The rule is simple: planning state, implementation state, and documentation must move together.

## Required Reading Before Work

Before discussing, planning, implementing, reviewing, or resuming work, read these files:

- `AGENTS.md`
- `.planning/PROJECT.md`
- `.planning/REQUIREMENTS.md`
- `.planning/ROADMAP.md`
- `.planning/STATE.md`
- `docs/Dahan-MarketPilot-Master-Spec.md`

For phase work, also read the relevant phase directory once it exists:

- `.planning/phases/<phase>/`
- phase `CONTEXT.md`
- phase `PLAN.md`
- prior phase `SUMMARY.md` or `VERIFICATION.md` files when available

## Language Rules

- Communicate with the user in Hebrew.
- Keep source code, identifiers, file names, configuration keys, tests, technical documentation, GSD artifacts, commit messages, and repository files in English.
- Keep commands, paths, environment variables, QuantConnect API names, GSD skill names, and configuration keys in English.

## Documentation Sync Contract

Every meaningful change must update the documentation that would otherwise become stale.

Update these files when the corresponding facts change:

- `.planning/PROJECT.md` - product context, core value, constraints, key decisions, unresolved decisions.
- `.planning/REQUIREMENTS.md` - requirements, v1/v2 scope, out-of-scope items, traceability, completion status.
- `.planning/ROADMAP.md` - phase list, phase goals, plan counts, dependencies, progress.
- `.planning/STATE.md` - current phase, status, last activity, blockers, session continuity, recent decisions.
- `AGENTS.md` - persistent instructions for AI agents and workflow rules.
- `docs/Dahan-MarketPilot-Master-Spec.md` - master product specification only when the user explicitly changes the product definition.
- Domain docs under `docs/` - architecture, setup, operations, recovery, limitations, licensing, safety, and strategy explanations as they are created.

Do not leave implementation behavior documented only in code. If a rule affects safety, execution assumptions, QuantConnect behavior, Telegram behavior, dashboard behavior, validation, licensing, or operations, document it.

## Commit Policy

Commits are approved after the initial planning setup. Use focused commits for coherent completed units:

- One commit for a completed planning update.
- One commit for a completed phase plan.
- One commit for a verified implementation unit when practical.
- One commit for documentation-only synchronization when needed.

Before committing:

1. Run the relevant checks or state clearly why they were not run.
2. Update affected GSD and project documentation.
3. Check `git status --short`.
4. Review the staged diff.
5. Use an English commit message.

Do not commit secrets, generated fake performance data, fake portfolio data, or unverified claims.

## Safety Rules That Must Stay Visible

- The product is simulated Paper Trading only.
- `PAPER_TRADING_ONLY = True` must not be silently overridden.
- No real broker code, real-money credentials, leverage, margin, short selling, options, futures, cryptocurrency, Forex, or manual dashboard order controls.
- QuantConnect remains the source of truth for simulated portfolio state, orders, fills, Paper Trading status, and QuantConnect Backtest results.
- Render is read-only and must not maintain active simulated portfolio state.
- Telegram is a notification channel and must not become required for trading safety logic.
- No fake Backtest results, fake portfolio data, or profitability claims.

## Resuming Work

When resuming:

1. Read `AGENTS.md` and this guide.
2. Read `.planning/STATE.md` to identify the current phase and status.
3. Read `.planning/ROADMAP.md` and the active phase artifacts.
4. Run `git status --short --branch`.
5. Preserve user changes and do not reset or clean the worktree.
6. Continue through the active GSD command rather than improvising a parallel workflow.

## User Action And Secrets

When external credentials or subscriptions are needed, ask the user in Hebrew to complete the action outside chat. Never ask the user to paste secrets into chat. Use approved secret stores for:

- QuantConnect API credentials.
- GitHub Actions Secrets.
- Telegram bot token and chat ID.
- Render environment variables.
- Dashboard password and session secret.

## Reporting Back

Final responses to the user should include:

- What changed.
- Which files were created or modified.
- Which checks were run.
- Whether a commit was created.
- Current Git status summary.
- The next exact GSD command when relevant.
