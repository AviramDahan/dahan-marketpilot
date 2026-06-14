# Phase 8 Operator Setup

SIMULATED PAPER TRADING ONLY - NOT FINANCIAL ADVICE

This checklist is for operator-owned setup that cannot be completed by
automated tests because it requires external accounts, credentials, and payment
decisions.

## Secret Handling

Do not commit real secrets to the repository. Use local environment variables,
QuantConnect secure parameters, GitHub Secrets, Render environment variables, or
another approved external secret store.

The repository may reference these names:

- `QUANTCONNECT_USER_ID`
- `QUANTCONNECT_API_TOKEN`
- `QUANTCONNECT_PROJECT_ID`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

Local development may use `.env.local`; it is ignored by git.

## QuantConnect Paper Trading

1. Sign in to QuantConnect.
2. Create or select the Dahan MarketPilot project.
3. Create an API token and note the QuantConnect user ID.
4. Log in to Lean CLI locally:

   ```bash
   lean login
   ```

5. Sync or deploy only to QuantConnect Paper Trading.
6. If a Live Node or paid data/provider setup is required, the operator must
   approve and complete payment in QuantConnect.

Automated tests must not run `lean cloud live deploy`, start a Live Node, or
require QuantConnect credentials.

## Telegram Smoke Test

1. Create a bot through BotFather.
2. Add the bot to the target chat or group.
3. Store the bot token and chat target outside repository files.
4. For a local smoke test, create `.env.local` with:

   ```text
   TELEGRAM_BOT_TOKEN=...
   TELEGRAM_CHAT_ID=...
   ```

5. Temporarily set `telegram_enabled: true` only in the smoke-test environment.
6. Run:

   ```bash
   python scripts/telegram_smoke.py
   ```

7. Confirm the message appears in Telegram and contains the paper-only warning.

Telegram delivery is non-authoritative. Missing tokens, Telegram rejection,
network failure, duplicate suppression, or rate limiting must never affect Paper
Trading gates, order lifecycle, reconciliation, recovery, or protective exits.
