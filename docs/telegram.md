# Telegram

Telegram delivery is an outbound notification transport for existing
`NotificationDomainEvent` records. It is not part of trading safety, order
lifecycle, reconciliation, protective exits, activation gates, or Paper mode
approval.

Real delivery uses the official Telegram Bot API `sendMessage` path only when
all of these are true:

- `config/notifications.yaml` has `telegram_enabled: true`.
- `paper_trading_only: true` remains set.
- `delivery_required_for_safety: false` remains set.
- The bot token and chat target are available from approved external secret
  stores, such as QuantConnect secure parameters, GitHub Secrets, Render
  environment variables, or a local environment outside repository files.

Repository configuration may store only external reference names:

```yaml
notifications:
  paper_trading_only: true
  telegram_enabled: false
  delivery_required_for_safety: false
  token_env_var: TELEGRAM_BOT_TOKEN
  chat_id_env_var: TELEGRAM_CHAT_ID
  message_max_chars: 3900
```

Never write bot tokens, chat IDs, or copied secret values into repository files,
planning artifacts, tests, reports, logs, docs examples, or chat. The loader
rejects committed secret-like values and redacts externally loaded token and
chat values from safe diagnostics.

Operator setup remains outside the repository:

1. Create a bot through BotFather.
2. Identify the Telegram chat target.
3. Store the bot token and chat target in an approved secret store under the
   configured reference names.
4. Enable `telegram_enabled: true` only for the environment that should send
   real Paper Trading notifications.

Missing token, missing chat target, disabled delivery, API rejection,
network failure, local rate limiting, and duplicate suppression are delivery
outcomes only. They must be recorded as typed results and must never stop
trading logic or protective recovery.

Delivery statuses are deterministic and safe for logs or reports:

- `disabled`
- `missing_token`
- `missing_chat_id`
- `duplicate_suppressed`
- `rate_limited`
- `rejected`
- `failed`
- `delivered`

`ok: true` responses from Telegram map to `delivered`. `ok: false` responses
with `error_code`, `description`, or `parameters.retry_after` map to
`rejected` or `rate_limited`. Network exceptions map to `failed`. Result
objects include event type and correlation ID, but never raw token or chat
values.
