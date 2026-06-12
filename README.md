# Dahan MarketPilot

SIMULATED PAPER TRADING ONLY - NOT FINANCIAL ADVICE

Dahan MarketPilot is a safety-first US-equities swing-trading research,
backtesting, and simulated Paper Trading project. It is intended for
transparent rule validation, audit, and read-only monitoring. It must never
execute real-money trades or imply guaranteed profitability.

Phase 1 establishes the repository foundation only:

- Licensing and attribution files.
- Paper-only safety documentation.
- Setup, configuration, testing, and AI collaboration guidance.
- A future shared package boundary for safety/configuration work.

Phase 1 does not connect to real brokers, QuantConnect credentials, Telegram,
Render, or real market data. It does not implement strategy signals, portfolio
state, stock orders, Paper orders, backtest reports, or fake performance data.

## Project Documents

- [Disclaimer](DISCLAIMER.md)
- [Safety](docs/safety.md)
- [Setup](docs/setup.md)
- [Configuration](docs/configuration.md)
- [Testing](docs/testing.md)
- [Licensing](docs/licensing.md)
- [AI collaboration](docs/AI-COLLABORATION.md)
- [Agent instructions](AGENTS.md)
- [Master specification](docs/Dahan-MarketPilot-Master-Spec.md)

## Safety Boundary

The product is simulated Paper Trading only. `PAPER_TRADING_ONLY` must remain
central, true, and validated. Real broker code, real-money credentials,
leverage, margin, short selling, options, futures, cryptocurrency, Forex, and
dashboard order-entry controls are prohibited.

QuantConnect remains the source of truth for future simulated portfolio and
Backtest state. Render is read-only. Telegram is non-authoritative
notification infrastructure.
