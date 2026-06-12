PRODUCT NAME
============

Dahan MarketPilot

==================================================
PRODUCT PURPOSE
===============

Dahan MarketPilot is a cloud-hosted US-equities Swing Trading research,
Backtesting and simulated Paper Trading product.

The system must:

1. Scan a broad dynamic universe of US stocks.
2. Detect predefined and explainable Swing Trading setups.
3. Rank candidates using transparent numeric scoring.
4. Backtest the exact same strategy rules historically.
5. Validate strategies before allowing Paper Trading actions.
6. Run approved strategies in QuantConnect Cloud Paper Trading.
7. Manage simulated positions, orders, Stops, Targets and exits.
8. Continue operating while the user's computer is turned off.
9. Display the simulated portfolio through a mobile-friendly website.
10. Send Telegram alerts for signals and Paper Trading activity.
11. Explain every signal and action using actual numeric evidence.
12. Keep a complete audit trail.
13. Never execute a real-money trade.

Expected holding period:

Approximately 3–30 trading days.

The product is intended for research, Backtesting and simulated
Paper Trading only.

==================================================
VERSION 1 SCOPE
===============

Version 1 includes:

* US-listed common equities
* long positions only
* daily signal resolution
* Swing Trading
* dynamic universe selection
* QuantConnect LEAN
* QuantConnect Cloud Backtesting
* QuantConnect Cloud Paper Trading
* GitHub repository
* GitHub Actions
* Render dashboard
* Streamlit
* Telegram notifications
* portfolio values displayed in USD and NIS
* deterministic rule-based decisions
* transparent explanations
* automated tests
* reports and audit artifacts

Version 1 excludes:

* real-money trading
* real brokerage integrations
* leverage
* margin borrowing
* short selling
* options
* futures
* cryptocurrency
* Forex
* high-frequency trading
* intraday scalping
* day trading
* manual order buttons
* automatic transition to real trading
* an AI model making unauditable trade decisions
* promises of future profitability

==================================================
CORE ARCHITECTURE
=================

Use the following architecture.

QuantConnect LEAN:

* algorithm engine
* historical data processing
* dynamic universe selection
* indicators
* strategy execution
* Backtesting
* portfolio management
* order models
* fill models
* fee models
* slippage models
* risk management
* Paper Trading compatibility

QuantConnect Cloud Paper Trading:

* authoritative simulated cash
* authoritative simulated portfolio value
* authoritative holdings
* authoritative open positions
* authoritative orders
* authoritative fills
* continuous cloud algorithm execution
* restart behavior
* live algorithm status

GitHub:

* source code
* version control
* pull requests
* unit tests
* CI/CD
* documentation
* LEAN CLI synchronization
* QuantConnect Cloud Backtest workflows
* report artifacts
* configuration history
* strategy-version history

Render:

* read-only Streamlit dashboard
* mobile access
* password protection
* cached QuantConnect reads
* Backtest presentation
* Paper Trading presentation
* system-health presentation
* Telegram health presentation

Telegram:

* signal alerts
* Paper order alerts
* fill alerts
* Stop and Target alerts
* position-close alerts
* market-regime alerts
* system and error alerts
* daily summaries

==================================================
SOURCE OF TRUTH
===============

QuantConnect must remain the source of truth for:

* cash
* portfolio equity
* holdings
* open positions
* orders
* fills
* Paper Trading state
* algorithm status
* Paper Trading performance
* QuantConnect Backtest results

Render must never maintain an independent simulated portfolio.

GitHub must not be used as the authoritative live portfolio database.

CSV, JSON, SQLite, Excel or Render local storage must not replace
QuantConnect as the active Paper Trading portfolio source.

Reports and cached presentation files may exist, but they are not
authoritative portfolio state.

==================================================
MANDATORY OFFICIAL SOURCES
==========================

Inspect and use the current official versions of:

* QuantConnect/Lean
* QuantConnect/Tutorials
* QuantConnect/lean-cli
* current official QuantConnect documentation
* current official QuantConnect Cloud API documentation
* current official QuantConnect notification documentation
* current official QuantConnect Object Store documentation
* current official Render documentation
* current official Streamlit documentation
* current official Telegram Bot documentation where needed

Rules:

1. Verify every QuantConnect API before using it.
2. Do not invent QuantConnect classes.
3. Do not invent LEAN methods.
4. Do not invent API endpoints.
5. Do not assume an old tutorial still uses the current API.
6. Prefer official QuantConnect examples and source code.
7. Verify licenses before reusing code.
8. Do not copy from repositories without an explicit reusable license.
9. Attribute directly reused source code.
10. Record the exact source of substantial copied logic.

The completed repository must contain:

* LICENSE
* NOTICE
* THIRD_PARTY_NOTICES.md
* DISCLAIMER.md

Use Apache 2.0 attribution requirements correctly for directly reused
QuantConnect code.

Do not claim that the entire Dahan MarketPilot repository must use
Apache 2.0 unless required by the reused code and chosen project license.

Document the licensing decision.

==================================================
SAFETY REQUIREMENTS
===================

The product is simulated Paper Trading only.

Create a central safety guard:

PAPER_TRADING_ONLY = True

This guard must not be silently overridden.

Unsafe configuration must fail validation.

Reject:

* PAPER_TRADING_ONLY = False
* real brokerage configuration
* real-money credentials
* live-money order support
* leverage
* margin
* short selling
* options
* futures
* cryptocurrency
* manual order submission from the Render dashboard

Do not implement:

* a hidden live-trading switch
* a future live-broker adapter
* a “production trading” environment
* automatic migration to real trading
* instructions for activating real-money trading
* dashboard buttons that submit or modify orders

Every dashboard page and every generated report must display:

SIMULATED PAPER TRADING ONLY — NOT FINANCIAL ADVICE

Never state or imply:

* guaranteed profits
* guaranteed returns
* risk-free performance
* that Backtesting predicts future results with certainty
* that Paper Trading is identical to real execution

==================================================
STARTING PORTFOLIO
==================

Starting simulated capital:

100,000 NIS

QuantConnect account and trading currency:

USD

Configuration must include:

* starting_budget_nis
* initial_usd_ils_rate
* starting_cash_usd
* trading_currency
* display_currency
* fx_rate_timestamp
* fx_rate_source

Formula:

starting_cash_usd =
starting_budget_nis / initial_usd_ils_rate

Use a configurable launch FX rate.

The launch FX rate creates the starting portfolio.

The dashboard must display portfolio values in both USD and NIS.

Later FX-rate changes may update current NIS display values but must
not rewrite historical trade accounting or historical USD results.

Display an FX warning when the configured rate is stale.

==================================================
TRADING STYLE
=============

Style:

Long-only US-equity Swing Trading.

Expected holding period:

3–30 trading days.

Primary signal resolution:

Daily.

Version 1 must not use intraday data to generate primary signals.

Optional hourly confirmation may be designed as a future feature but
must remain disabled.

Signals based on a completed daily bar must execute only at a later
valid tradable price.

Never create a signal from a bar and fill at the same bar's closing
price unless it was technically possible to submit the order before
the close, which is not the default design.

Default execution timing:

* evaluate completed daily bars
* create signal after the bar is final
* schedule the Paper order for the next valid session
* record the exact assumed execution method

==================================================
DYNAMIC UNIVERSE
================

Use QuantConnect dynamic fundamental or liquidity universe selection.

Do not depend only on a static hand-written ticker list.

Initial universe requirements:

* US-listed common equities
* price at least $5
* at least 250 completed daily bars
* average 20-day volume at least 500,000 shares
* average 20-day dollar volume at least $20,000,000
* configurable minimum market capitalization
* fundamental data where required
* exclude ETFs
* exclude OTC securities
* exclude preferred shares where identifiable
* exclude warrants
* exclude invalid securities
* exclude securities with stale data
* exclude securities with critical missing data
* exclude securities that cannot be traded by the configured model

Selection flow:

1. Start from a broad US-equity universe.
2. Apply security-type and price filters.
3. Rank by liquidity and dollar volume.
4. Keep approximately 500–750 liquid equities.
5. Apply history and data-quality requirements.
6. Run complete technical analysis on approximately 300–500 equities.
7. Preserve sector and industry classifications.
8. Limit memory and indicator creation safely.

Universe refresh:

* broad membership: weekly
* liquidity and data quality: daily
* tradability: before every order
* sector data: when membership changes

Record:

* initial universe count
* filtered count
* final analyzed count
* added symbols
* removed symbols
* exclusions
* exclusion reasons
* sector distribution
* update timestamp
* data-quality status

Do not silently reduce the universe to a tiny list.

Handle indicator cleanup when symbols leave the universe.

Document:

* survivorship-bias risks
* universe-history limitations
* fundamental-data limitations
* the effect of current constituents on historical tests

==================================================
MARKET REGIME
=============

Use SPY and QQQ as market-regime references.

Calculate:

* EMA20
* EMA50
* EMA200
* EMA20 slope
* EMA50 slope
* EMA200 slope
* 20-day return
* 60-day return
* optional universe-breadth measures

Initial states:

RISK_ON:

* SPY above EMA200
* QQQ above EMA200
* at least one benchmark above EMA50
* long-term slopes are not materially negative

NEUTRAL:

* benchmark conditions are mixed
* require a higher signal score
* reduce new-position size
* limit the number of new positions

RISK_OFF:

* SPY and QQQ below EMA200
* or both benchmarks have materially negative medium-term trends
* block new long entries
* continue managing existing positions and protective exits

Do not automatically liquidate every position solely because the
market regime changes.

Individual exit rules remain authoritative for existing positions.

All regime thresholds must be:

* configurable
* documented
* unit tested
* included in Backtest reports
* included in Telegram transition alerts

==================================================
INDICATORS
==========

Calculate per analyzed security:

Trend:

* EMA8
* EMA20
* EMA50
* EMA200
* EMA slopes
* moving-average alignment
* distance from EMA20
* distance from EMA50
* distance from EMA200
* distance from 52-week high

Momentum:

* RSI14
* MACD 12/26/9
* MACD signal
* MACD histogram
* ROC20
* ROC60
* 20-day return
* 60-day return
* relative strength versus SPY
* relative strength versus QQQ
* momentum percentile within the analyzed universe where practical

Volume:

* average volume 20
* average volume 50
* relative volume
* average dollar volume 20
* average dollar volume 50
* volume trend
* pullback-volume behavior

Risk and volatility:

* ATR14
* ATR percentage
* rolling volatility
* recent structural swing low
* recent structural swing high
* recent drawdown
* gap-risk approximation
* maximum adverse movement approximation where practical

Required indicators must be ready before a signal is generated.

Missing, invalid, infinite or NaN values must reject the signal.

Never convert missing data into a default positive score.

==================================================
SETUP 1 — TREND PULLBACK
========================

Goal:

Find strong stocks in an established uptrend that temporarily pull
back toward EMA20 or EMA50 and begin to recover.

Initial mandatory trend requirements:

* close above EMA50
* EMA50 above EMA200
* EMA20 rising
* EMA50 not materially falling
* positive relative strength versus SPY
* sufficient liquidity
* acceptable ATR percentage

Pullback requirements:

* price approaches EMA20 or EMA50 within a configurable distance
* no decisive close below EMA50
* pullback volume is not abnormally high
* RSI is approximately 42–65
* the latest completed bar indicates stabilization or recovery

Possible triggers:

* close reclaims EMA20
* close exceeds the previous completed bar's high
* configurable bullish reversal condition
* momentum begins improving after the pullback

Reject when:

* market regime is RISK_OFF
* ATR is excessive
* stop distance is excessive
* price is too extended
* trend structure is broken
* data is incomplete
* earnings-risk policy rejects the trade
* expected reward/risk is below the configured threshold
* portfolio constraints fail

The exact trigger variants must be independently testable.

==================================================
SETUP 2 — VOLUME BREAKOUT
=========================

Goal:

Find liquid stocks breaking above recent resistance or consolidation
with volume confirmation.

Initial requirements:

* positive long-term technical structure
* close exceeds the highest high of the previous 20 completed bars
* current bar excluded from the prior-resistance calculation
* relative volume at least 1.5
* acceptable ATR percentage
* price no more than approximately 10% above EMA20
* sufficient average dollar volume
* market regime is not RISK_OFF
* expected reward/risk passes
* breakout range is not abnormally wide
* data quality is valid

Signal timing:

* calculate only after the breakout bar is complete
* execute only at a later valid tradable price
* never fill at the same close that created the signal

Reject:

* excessive extension
* invalid resistance calculation
* insufficient volume
* excessively wide stop
* poor reward/risk
* stale data
* earnings-risk conflict
* sector or portfolio constraint conflict

Support configurable breakout windows, but begin with 20 completed bars.

Do not optimize dozens of windows simultaneously.

==================================================
SETUP 3 — RELATIVE STRENGTH LEADER
==================================

Goal:

Find stocks outperforming SPY and QQQ while maintaining a healthy
technical structure.

Initial requirements:

* positive 20-day relative return versus SPY
* positive 60-day relative return versus SPY
* positive relative behavior versus QQQ where appropriate
* close above EMA50
* close above EMA200
* EMA50 above EMA200
* price reasonably close to the 52-week high
* acceptable liquidity
* acceptable ATR percentage
* no extreme overextension
* valid data

Relative Strength Leader may operate as:

* an independent setup
* a ranking factor
* confirmation for Trend Pullback
* confirmation for Volume Breakout

Implement and validate each setup independently before creating a
Combined Swing strategy.

==================================================
COMBINED SWING STRATEGY
=======================

Do not implement Combined Swing first.

Combined Swing may be created only after:

1. Trend Pullback is implemented and tested.
2. Volume Breakout is implemented and tested.
3. Relative Strength Leader is implemented and tested.
4. Each setup has independent Backtest results.
5. Each setup has Out-of-Sample results.
6. The contribution of every score component is understood.
7. Combining them does not create duplicate entries or overfitting.

Combined Swing must not simply add every possible condition.

Keep the final rules understandable and explainable.

==================================================
SCORING
=======

Create MarketPilot Score from 0 to 100.

Initial weights:

* trend structure: 25
* relative strength: 20
* momentum: 15
* setup quality: 20
* volume confirmation: 10
* risk quality: 10

Total must equal 100.

Classification:

BUY_CANDIDATE:

* score at least 75
* confidence at least 75
* all hard filters pass
* market regime permits a new position
* expected reward/risk at least 2.0
* portfolio constraints pass
* setup is approved by the strategy activation gate

WATCH:

* score 60–74
* or a strong setup awaiting confirmation
* or a setup that is valid but not yet approved for Paper execution

AVOID:

* score below 60
* or a hard rejection condition

REJECTED:

* critical data failure
* critical risk failure
* invalid calculation
* portfolio constraint failure
* unsupported security
* strategy disabled
* activation gate failed

Every signal result must include:

* ticker
* company name where available
* sector
* timestamp
* setup
* classification
* score
* score components
* confidence
* latest completed-bar price
* planned entry
* initial stop
* Target 1
* Target 2
* expected reward/risk
* market regime
* actual indicator values
* numeric evidence
* warnings
* rejection reasons
* human-readable explanation

No generic explanation such as “technical indicators are positive”.

Use actual values.

==================================================
PORTFOLIO RISK
==============

Initial limits:

* maximum 5 open positions
* maximum 3 new positions per trading day
* maximum 20% of portfolio equity per position
* maximum 35% total exposure per sector
* risk 1% of current portfolio equity per trade
* no duplicate ticker position
* no averaging down
* no leverage
* no margin borrowing
* no short selling
* no fractional shares in version 1
* no entry when data quality is invalid
* no entry when protective-stop creation cannot be guaranteed

Position sizing:

risk_budget =
portfolio_equity × risk_per_trade_percentage

risk_per_share =
entry_price - stop_price

quantity_by_risk =
floor(risk_budget / risk_per_share)

maximum_position_value =
portfolio_equity × maximum_position_percentage

quantity_by_allocation =
floor(maximum_position_value / entry_price)

final_quantity =
minimum of:

* quantity_by_risk
* quantity_by_allocation
* available-cash limit
* sector-exposure limit
* buying-power limit
* configured maximum quantity where applicable

Reject when:

* risk_per_share is not positive
* stop is invalid
* final quantity is zero
* available cash is insufficient
* sector exposure would exceed the maximum
* the position would exceed allocation limits

Record all sizing calculations.

==================================================
INITIAL STOP
============

Preferred initial stop:

recent structural swing low minus an ATR buffer.

Initial ATR buffer:

0.25 × ATR14

Fallback:

approximately 1.5–2 ATR below planned entry.

Rules:

* stop must be below entry
* stop distance must be positive
* stop must represent a valid technical structure
* stop must not be unrealistically close
* stop distance must not exceed the configured maximum
* initial maximum stop distance: 8%
* record the exact methodology used
* reject the trade when no valid stop can be produced

The structural swing-low algorithm must be deterministic and tested.

Do not use future bars to determine the swing low.

==================================================
PROFIT MANAGEMENT
=================

Define:

R = entry price - initial stop price

Initial proposal:

* Target 1 at 2R
* sell 50% at Target 1
* Target 2 at 3R
* manage the remaining position using a tested EMA20 or ATR trailing rule
* maximum holding period: 30 trading days

Additional exits:

* protective Stop
* trailing Stop
* Target 1
* Target 2
* confirmed close below EMA50
* setup invalidation
* market-structure breakdown
* maximum holding period
* optional earnings-risk exit
* security delisting or non-tradable status

Do not assume moving the Stop to break-even is beneficial.

Backtest the following separately:

* no break-even move
* move to break-even after Target 1
* ATR-based Stop adjustment after Target 1
* EMA20 trailing exit
* ATR trailing exit

Do not choose the version with the highest historical return without
checking stability and Out-of-Sample behavior.

==================================================
EARNINGS RISK
=============

Implement a configurable earnings-risk policy.

Initial conservative proposal:

* do not open a new trade within 3 trading days before scheduled earnings
* optionally reduce or close a position before earnings
* identify when earnings data is unavailable

If reliable earnings data is unavailable:

* do not invent a date
* disable the filter explicitly
* display a warning
* record the limitation in Backtest and Paper results

Test variants:

* no earnings filter
* block entries 3 trading days before earnings
* exit before earnings
* hold through earnings

Do not assume one policy is universally superior.

==================================================
EXECUTION REALISM
=================

Never use future data.

Never include the current bar in a prior-high or prior-low calculation
when that would create look-ahead bias.

Signals produced after a completed daily bar must execute only at a
later valid price.

Explicitly configure and record:

* brokerage model
* security initializer
* fee model
* slippage model
* fill model
* order type
* time in force
* extended-hours behavior
* data normalization mode
* corporate-action handling
* stale-price behavior

Do not silently use zero slippage.

Run at least these slippage scenarios:

* 5 basis points per side
* 10 basis points per side
* 20 basis points per side

Use realistic fee assumptions.

When both a Stop and Target may have been reached within the same
daily bar:

* use a conservative adverse-first assumption
* or validate the ambiguous trade using finer-resolution historical data
* record the chosen resolution
* report the number of ambiguous trades

Do not allow same-bar ambiguity to silently inflate performance.

==================================================
BACKTESTING PERIOD
==================

Primary historical period:

2020-01-01 through 2025-12-31

Support configurable start and end dates.

The system must also support later extension to earlier history when
the required data is available.

==================================================
BACKTESTING ANALYSES
====================

Required analyses:

1. Full-period Backtest
2. Year-by-year Backtests
3. In-Sample test
4. Out-of-Sample test
5. Walk-Forward analysis
6. Parameter-sensitivity analysis
7. Slippage stress tests
8. Fee stress tests
9. SPY benchmark comparison
10. QQQ benchmark comparison
11. Results by setup
12. Results by market regime
13. Results by sector
14. Results by ticker
15. Contribution by trade
16. Concentration analysis
17. Holding-period analysis
18. Entry-day gap analysis
19. Stop and Target ambiguity analysis
20. Data-quality warning analysis

Initial split:

* In-Sample: 2020–2023
* Out-of-Sample: 2024–2025

Never randomly shuffle time-series data.

==================================================
BACKTEST METRICS
================

Required metrics:

* starting equity
* ending equity
* total return
* CAGR
* maximum drawdown
* annualized volatility
* Sharpe ratio
* Sortino ratio
* Calmar ratio
* win rate
* loss rate
* average win
* average loss
* payoff ratio
* profit factor
* expectancy
* number of trades
* exposure
* turnover
* average holding period
* median holding period
* longest winning streak
* longest losing streak
* best trade
* worst trade
* monthly returns
* annual returns
* benchmark return
* alpha where supported
* beta where supported
* fees
* estimated slippage
* performance by setup
* performance by regime
* performance by sector
* top contributors
* worst contributors

==================================================
BACKTEST WARNINGS
=================

Generate explicit warnings when:

* there are too few completed trades
* one trade produces a disproportionate amount of profit
* one ticker produces a disproportionate amount of profit
* one sector produces most of the profit
* one year produces most of the profit
* Out-of-Sample expectancy is negative
* Out-of-Sample profit factor is weak
* maximum drawdown exceeds the threshold
* parameter changes destroy performance
* results rely on unrealistic fills
* results rely on zero slippage
* survivorship bias may exist
* look-ahead bias may exist
* data is missing
* earnings data is incomplete
* corporate-action handling is uncertain
* ambiguous same-bar exits materially affect results

==================================================
STRATEGY ACTIVATION GATES
=========================

A profitable full-period result alone must not enable Paper Trading.

Initial activation requirements:

* at least 50 completed trades
* positive Out-of-Sample expectancy
* profit factor at least 1.20
* maximum drawdown no greater than 20%
* no critical look-ahead warning
* no critical survivorship-bias warning that invalidates the result
* no extreme dependence on one trade
* no extreme dependence on one ticker
* viability with at least 10 basis points slippage per side
* acceptable results in multiple market conditions
* strategy code version recorded
* configuration hash recorded
* Backtest result artifact available
* approval status explicitly stored

If a setup fails:

* it must not open Paper positions
* it may continue producing WATCH signals
* it may continue producing research reports
* failed activation gates must be displayed
* Telegram alerts must state that the setup is not approved for Paper execution

Activation must never occur solely because total return is positive.

==================================================
PAPER TRADING
=============

Use QuantConnect Cloud Paper Trading only.

Requirements:

* simulated capital only
* no real brokerage
* continuous Paper Trading Live Node
* algorithm-start handling
* algorithm-restart handling
* state recovery
* duplicate-entry prevention
* order-ticket reconciliation
* partial-fill handling
* rejected-order handling
* canceled-order handling
* protective-order restoration
* partial exits
* complete OrderEvent journal
* split handling
* symbol-change handling
* delisting handling
* stale-data handling
* error and recovery logging

For every open position retain:

* symbol
* company and sector where available
* setup
* signal timestamp
* submission timestamp
* fill timestamp
* entry price
* original quantity
* remaining quantity
* initial stop
* active stop
* Target 1
* Target 2
* initial R
* current R
* score at entry
* confidence at entry
* market regime at entry
* indicator evidence
* explanation
* order-ticket identifiers
* protective-order identifiers
* partial-exit status
* highest price since entry
* lowest price since entry
* holding days
* strategy version
* configuration hash

Use only supported QuantConnect persistence mechanisms.

Verify the current persistence API before implementation.

The algorithm must safely recover important custom position state after
restart.

==================================================
PAPER TRADING STAGES
====================

Paper operation should be introduced gradually.

Stage 1 — Shadow Mode:

* calculate signals
* generate explanations
* produce Telegram signal previews where enabled
* submit no Paper orders

Stage 2 — Limited Paper Mode:

* allow one independently validated setup
* limit the number of simultaneous positions
* monitor order and restart behavior

Stage 3 — Full Approved Paper Mode:

* allow every setup that passed activation gates
* continue blocking unapproved setups
* keep all risk limits active

The user must be able to see the active Paper mode in the dashboard.

==================================================
TELEGRAM NOTIFICATIONS
======================

Dahan MarketPilot must include a complete Telegram notification system.

The primary notification source must be the QuantConnect Cloud Paper
Trading algorithm.

Use only the currently supported official QuantConnect notification API.

Before implementation:

* inspect the current official QuantConnect notification documentation
* verify the current Python method and parameters
* verify notification quotas and limitations
* do not invent notification methods
* do not hardcode credentials

Telegram delivery must never control trading logic.

Trading, Stops, Targets and exits must continue operating when Telegram
delivery fails.

==================================================
TELEGRAM SECURE CONFIGURATION
=============================

Required secure parameters:

* TELEGRAM_BOT_TOKEN
* TELEGRAM_CHAT_ID

Never commit:

* Telegram bot token
* Telegram chat ID
* private channel information
* QuantConnect credentials

Store secrets using supported QuantConnect secure project parameters
or another verified secure mechanism.

Never print secrets in:

* logs
* errors
* exceptions
* reports
* Telegram previews
* dashboard pages
* test output
* GitHub Actions output

Notification configuration should include:

notifications:
telegram:
enabled: true
send_buy_candidates: true
send_watch_candidates: true
send_rejections_individually: false
send_order_submitted: true
send_partial_fills: true
send_fills: true
send_stop_created: true
send_stop_updated: true
send_stop_triggered: true
send_target_triggered: true
send_position_closed: true
send_order_rejected: true
send_order_canceled: true
send_market_regime_changes: true
send_algorithm_status: true
send_critical_errors: true
send_daily_summary: true
minimum_signal_score: 60
duplicate_suppression_minutes: 60
maximum_notifications_per_minute: 10

==================================================
TELEGRAM ARCHITECTURE
=====================

Create a modular notification layer with components such as:

* NotificationService
* TelegramNotificationService
* NotificationFormatter
* NotificationEvent
* NotificationSeverity
* NotificationDeduplicator
* NotificationRateLimiter
* NotificationDeliveryResult
* FakeNotificationTransport

NotificationSeverity:

* INFO
* SIGNAL
* ACTION
* WARNING
* CRITICAL

NotificationEvent must include:

* ALGORITHM_STARTED
* ALGORITHM_RESTARTED
* ALGORITHM_STOPPED
* BUY_CANDIDATE
* WATCH_CANDIDATE
* SIGNAL_REJECTED
* PAPER_BUY_SUBMITTED
* PAPER_SELL_SUBMITTED
* ORDER_PARTIALLY_FILLED
* ORDER_FILLED
* ORDER_REJECTED
* ORDER_CANCELED
* STOP_CREATED
* STOP_UPDATED
* STOP_TRIGGERED
* TARGET_1_TRIGGERED
* TARGET_2_TRIGGERED
* TRAILING_STOP_UPDATED
* POSITION_PARTIALLY_CLOSED
* POSITION_CLOSED
* MARKET_REGIME_CHANGED
* DATA_STALE
* STATE_RECOVERED
* PROTECTIVE_ORDER_RESTORED
* CRITICAL_ERROR
* DAILY_SUMMARY

==================================================
TELEGRAM SIGNAL ALERTS
======================

Send an individual Telegram alert for:

* every new BUY_CANDIDATE that passes the configured minimum score
* WATCH_CANDIDATE when enabled
* an important classification change
* an important score or risk-state change

Do not send an individual message for every AVOID or rejected stock by
default.

Rejected and avoided candidates should appear in:

* scan summary
* daily summary
* Render dashboard
* downloadable reports

A signal alert must clearly state:

SIGNAL ONLY — NO ORDER HAS BEEN FILLED

Include where applicable:

* ticker
* setup
* classification
* score
* confidence
* latest completed-bar price
* planned entry
* stop
* Target 1
* Target 2
* expected reward/risk
* market regime
* actual numeric evidence
* activation status
* warnings
* UTC timestamp
* America/New_York timestamp
* Paper Trading disclaimer

==================================================
TELEGRAM ORDER ALERTS
=====================

Execution alerts must be generated from authoritative QuantConnect
OrderEvent processing.

Do not send ORDER_FILLED because an order was merely submitted.

Clearly distinguish:

* signal detected
* Paper order submitted
* order partially filled
* order fully filled
* order rejected
* order canceled
* position partially closed
* position fully closed

Order notifications should include where applicable:

* event type
* ticker
* setup
* order ID
* order type
* order status
* side
* requested quantity
* filled quantity
* remaining quantity
* fill price
* fees
* current portfolio value
* signal score
* confidence
* market regime
* reason
* UTC timestamp
* New York timestamp
* simulated Paper Trading warning

Required alerts:

* Paper BUY submitted
* Paper SELL submitted
* partial fill
* complete fill
* rejected order
* canceled order
* partial position close
* full position close

==================================================
TELEGRAM STOP AND TARGET ALERTS
===============================

Send alerts when:

* initial protective Stop is created
* Stop price changes
* trailing Stop changes
* Stop is triggered
* Target 1 is triggered
* Target 2 is triggered
* protective order is rejected
* protective order is canceled
* protective order is restored after restart
* position is fully closed

Include where applicable:

* ticker
* setup
* previous Stop
* new Stop
* target price
* protected quantity
* remaining quantity
* unrealized P/L
* realized P/L
* current R multiple
* holding period
* highest price since entry
* reason for change or exit

Do not send STOP_UPDATED or TRAILING_STOP_UPDATED when the price did
not actually change.

==================================================
TELEGRAM MARKET REGIME ALERTS
=============================

Send Telegram only when the Market Regime actually changes.

Examples:

* RISK_ON to NEUTRAL
* NEUTRAL to RISK_OFF
* RISK_OFF to RISK_ON

Do not send an unchanged regime repeatedly.

Include:

* previous regime
* new regime
* SPY price
* SPY EMA50
* SPY EMA200
* QQQ price
* QQQ EMA50
* QQQ EMA200
* effect on new entries
* timestamp

==================================================
TELEGRAM SYSTEM ALERTS
======================

Send alerts for:

* algorithm started
* algorithm restarted
* algorithm stopped unexpectedly
* important state recovery
* protective-order recovery
* stale critical data
* missing critical data
* repeated rejected orders
* failure to restore protective orders
* critical unhandled exception
* notification subsystem failure summary

Critical errors must not contain secrets.

Telegram delivery failure must not stop:

* signal evaluation
* order reconciliation
* Stop processing
* Target processing
* exit processing
* state recovery

==================================================
TELEGRAM DAILY SUMMARY
======================

After the US market closes, send one concise Telegram summary.

Include:

* date
* algorithm status
* active Paper mode
* market regime
* portfolio value in USD
* portfolio value in NIS
* daily change
* total return
* cash
* invested value
* open positions
* new BUY candidates
* WATCH candidates
* new Paper entries
* closed positions
* realized P/L
* unrealized P/L
* Stops triggered
* Targets triggered
* rejected orders
* critical warnings
* Render dashboard URL

Keep the message within Telegram message-length limits.

When too long:

* send a condensed summary
* include the dashboard URL
* do not create excessive message fragments

==================================================
TELEGRAM DEDUPLICATION
======================

Every notification must have a deterministic ID.

Example:

event_type:symbol:order_id:event_timestamp

Prevent duplicates caused by:

* repeated scheduled handlers
* duplicate OrderEvent callbacks
* repeated signal evaluation
* algorithm restart
* retry behavior
* unchanged Stop calculations
* unchanged regime calculations

Persist important notification IDs using a supported durable
QuantConnect mechanism.

Do not suppress legitimate:

* fills
* rejected orders
* Stop triggers
* position closures
* critical errors

==================================================
TELEGRAM RATE LIMITING
======================

QuantConnect or Telegram notification quotas may apply.

Implement:

* configurable rate limiting
* notification priorities
* bounded retries
* duplicate suppression
* summary aggregation
* failure metrics

Priority order:

1. CRITICAL_ERROR
2. ORDER_REJECTED
3. STOP_TRIGGERED
4. ORDER_FILLED
5. POSITION_CLOSED
6. TARGET_TRIGGERED
7. PAPER_ORDER_SUBMITTED
8. BUY_CANDIDATE
9. MARKET_REGIME_CHANGED
10. WATCH_CANDIDATE
11. summaries

If delivery fails:

* record the failure
* increment a failure metric
* retry only with bounded logic
* do not create an infinite retry loop
* expose the failure in Render System Health
* continue the trading algorithm

==================================================
TELEGRAM BACKTEST BEHAVIOR
==========================

Historical Backtests must not send real Telegram messages by default.

During Backtests:

* generate notification-preview records
* test event creation
* test message formatting
* store previews in artifacts where practical
* disable actual Telegram delivery

An explicit notification integration-test mode may send one test message,
but it must be disabled by default and must never run during normal
historical Backtests.

==================================================
RENDER DASHBOARD
================

Build a read-only Streamlit dashboard hosted on Render.

Requirements:

* mobile friendly
* password protected
* read only
* no order buttons
* no portfolio modifications
* QuantConnect credentials stored server-side only
* cached reads
* stale-data warnings
* last successful update timestamp
* Paper Trading warning
* responsive tables and metric cards

Pages:

1. Overview
2. Open Positions
3. Closed Trades
4. Latest Signals
5. BUY Candidates
6. WATCH Candidates
7. Rejections
8. Strategy Performance
9. Backtest Results
10. Backtest versus Paper
11. Equity Curve
12. Drawdown
13. Risk and Sector Exposure
14. Agent Activity
15. Telegram Notifications
16. System Health
17. Disclaimer

Overview must display:

* portfolio value USD
* portfolio value NIS
* cash
* invested value
* realized P/L
* unrealized P/L
* total return
* daily change
* open positions
* current market regime
* enabled setups
* approved setups
* active Paper mode
* algorithm status
* last QuantConnect update
* last dashboard refresh

Open Positions must display:

* ticker
* setup
* sector
* entry date
* entry price
* current price
* original quantity
* remaining quantity
* position value
* P/L amount
* P/L percentage
* Stop
* Target 1
* Target 2
* current R
* score at entry
* holding days
* explanation

Use only currently supported official QuantConnect APIs or durable
QuantConnect exports.

Do not invent API endpoints.

If the API cannot provide a required custom field, use a supported
QuantConnect durable export such as Object Store after verifying the
current API.

==================================================
RENDER SECURITY
===============

Store secrets only in Render environment variables.

Potential variables may include:

* QUANTCONNECT_USER_ID
* QUANTCONNECT_API_TOKEN
* DASHBOARD_PASSWORD
* DASHBOARD_SESSION_SECRET
* GITHUB_REPOSITORY
* DASHBOARD_PUBLIC_URL

Verify actual required QuantConnect authentication fields before
implementation.

Do not expose secrets in:

* HTML
* browser JavaScript
* logs
* error messages
* screenshots
* reports

Cache QuantConnect API requests for approximately 30–60 seconds.

If QuantConnect is unavailable:

* show cached data where available
* label it as stale
* show the last successful update
* do not fabricate current values

==================================================
TELEGRAM DASHBOARD HEALTH
=========================

Add a Telegram section to System Health.

Display:

* enabled or disabled
* delivery status
* last successful notification
* last failed notification
* notifications sent today
* duplicates suppressed
* messages rate limited
* failure count
* configured event categories
* last daily summary time

Do not display:

* bot token
* full chat ID
* private channel information

Mask sensitive identifiers.

==================================================
GITHUB ACTIONS
==============

Plan and implement these workflows.

tests.yml:

* install dependencies
* format check
* lint
* type checks where practical
* unit tests
* security and secret scanning where practical

quantconnect-sync.yml:

* manual trigger initially
* validate before synchronization
* synchronize using the supported current LEAN CLI
* never deploy to real trading
* never expose credentials

cloud-backtest.yml:

Inputs:

* strategy
* start date
* end date
* configuration preset
* slippage preset

Actions:

* validate code
* synchronize safely
* run QuantConnect Cloud Backtest
* retrieve actual results
* publish artifacts
* never fabricate missing results

weekly-validation.yml:

* run selected strategy validation
* compare with approved baseline
* produce a comparison report
* never automatically replace the approved Paper strategy
* require explicit approval for activation changes

dashboard-health.yml:

* test Render health endpoint
* test dashboard parsing
* test stale-data handling
* perform no trading action

No workflow may deploy to real-money trading.

Never commit:

* QuantConnect credentials
* Telegram credentials
* Render secrets
* private account identifiers

==================================================
REPORTS
=======

Generate:

* JSON metrics
* CSV signals
* CSV trades
* CSV orders
* Excel report
* HTML report
* strategy comparison report
* Backtest comparison report
* validation-gate report
* Telegram preview report during Backtests

Reports must include:

* Git commit SHA
* strategy version
* configuration hash
* QuantConnect project ID where safe
* QuantConnect Backtest identifier
* data range
* universe settings
* fee assumptions
* slippage assumptions
* generation timestamp
* activation status
* warnings
* disclaimer

Excel sheets:

* Executive Summary
* Backtest Metrics
* Annual Returns
* Monthly Returns
* Trades
* Orders
* Signals
* Setup Comparison
* Market Regime Comparison
* Benchmark Comparison
* Drawdown
* Risk
* Sector Exposure
* Parameter Sensitivity
* Concentration Analysis
* Activation Gates
* Data Quality
* Notification Previews
* Warnings
* Configuration
* Disclaimer

Excel files are reports only.

Do not use Excel as live portfolio state.

==================================================
TESTING
=======

Use deterministic offline fixtures where practical.

Core unit tests must not require:

* internet
* QuantConnect credentials
* Telegram credentials
* Render credentials
* real market access

Test:

Safety:

* Paper-only guard
* real broker rejection
* leverage rejection
* short rejection
* options rejection
* crypto rejection
* read-only dashboard enforcement

Configuration:

* valid configuration
* unsafe configuration rejection
* FX calculation
* range validation
* threshold validation

Indicators:

* EMA calculations
* slopes
* RSI
* MACD
* ATR
* ROC
* relative volume
* dollar volume
* relative strength
* missing-data handling
* NaN rejection

Market Regime:

* RISK_ON
* NEUTRAL
* RISK_OFF
* transition detection
* unchanged-state suppression

Setups:

* Trend Pullback
* Volume Breakout
* Relative Strength
* current-bar exclusion
* recovery trigger
* breakout trigger
* rejection conditions
* stale-data rejection

Scoring:

* score components
* total score
* classification boundaries
* confidence
* hard rejection
* numeric explanation

Risk:

* risk budget
* quantity by risk
* quantity by allocation
* cash constraint
* sector constraint
* maximum position count
* daily entry count
* invalid stop
* zero quantity

Orders and exits:

* submission state
* partial fills
* full fills
* rejection
* cancellation
* protective Stop creation
* Target creation
* partial exit
* full exit
* trailing Stop
* maximum holding period
* duplicate-order prevention
* restart-state restoration
* split handling where practical
* delisting handling where practical

Bias and execution:

* no look-ahead
* prior-high excludes current bar
* signal and fill timing
* same-bar ambiguity
* slippage calculations
* fee calculations

Telegram:

* BUY candidate formatting
* WATCH formatting
* Paper BUY submitted
* Paper SELL submitted
* partial fill
* full fill
* Stop created
* Stop updated
* Stop triggered
* Target 1
* Target 2
* position partially closed
* position closed
* order rejected
* order canceled
* regime transition
* system alert
* daily summary
* duplicate suppression
* rate limiting
* missing token
* missing chat ID
* disabled notifications
* Backtest delivery disabled
* delivery failure does not stop trading
* secrets never appear in logs

Dashboard:

* API parsing
* caching
* stale data
* authentication
* read-only behavior
* error presentation
* secret masking

Use fake transports and fixtures.

Unit tests must never send real Telegram messages.

==================================================
DOCUMENTATION
=============

The completed repository must document:

* product purpose
* architecture
* QuantConnect responsibilities
* GitHub responsibilities
* Render responsibilities
* Telegram responsibilities
* Paper Trading restriction
* strategy rules
* scoring
* risk management
* order lifecycle
* execution assumptions
* Backtesting methodology
* bias risks
* activation gates
* QuantConnect setup
* LEAN CLI setup
* Paper Trading deployment
* Telegram setup
* Render deployment
* GitHub Secrets
* operational monitoring
* restart recovery
* incident recovery
* troubleshooting
* limitations
* licensing
* disclaimer

Documentation must not hide critical logic only inside source code.

==================================================
PROJECT STRUCTURE
=================

Use a structure similar to:

dahan-marketpilot/
├── README.md
├── AGENTS.md
├── LICENSE
├── NOTICE
├── DISCLAIMER.md
├── THIRD_PARTY_NOTICES.md
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── .env.example
├── .gitignore
├── render.yaml
│
├── config/
│   ├── strategy.yaml
│   ├── risk.yaml
│   ├── notifications.yaml
│   ├── dashboard.yaml
│   └── environments/
│       ├── backtest.yaml
│       ├── shadow.yaml
│       └── paper.yaml
│
├── lean/
│   ├── main.py
│   ├── config.json
│   └── marketpilot/
│       ├── **init**.py
│       ├── constants.py
│       ├── configuration.py
│       ├── models.py
│       ├── universe.py
│       ├── symbol_data.py
│       ├── indicators.py
│       ├── regime.py
│       ├── scoring.py
│       ├── explanations.py
│       ├── risk.py
│       ├── sizing.py
│       ├── orders.py
│       ├── exits.py
│       ├── persistence.py
│       ├── journal.py
│       ├── notifications/
│       │   ├── **init**.py
│       │   ├── events.py
│       │   ├── service.py
│       │   ├── formatter.py
│       │   ├── telegram.py
│       │   ├── deduplication.py
│       │   └── rate_limit.py
│       └── strategies/
│           ├── **init**.py
│           ├── base.py
│           ├── trend_pullback.py
│           ├── volume_breakout.py
│           ├── relative_strength.py
│           └── combined_swing.py
│
├── dashboard/
│   ├── app.py
│   ├── api_client.py
│   ├── auth.py
│   ├── cache.py
│   ├── models.py
│   ├── formatters.py
│   ├── charts.py
│   └── pages/
│       ├── overview.py
│       ├── positions.py
│       ├── trades.py
│       ├── signals.py
│       ├── backtests.py
│       ├── strategies.py
│       ├── risk.py
│       ├── notifications.py
│       ├── activity.py
│       └── system_status.py
│
├── scripts/
│   ├── validate_project.py
│   ├── qc_push.py
│   ├── qc_backtest.py
│   ├── qc_pull_results.py
│   ├── compare_versions.py
│   └── generate_report.py
│
├── reports/
│   └── .gitkeep
│
├── tests/
│   ├── fixtures/
│   ├── test_safety.py
│   ├── test_configuration.py
│   ├── test_indicators.py
│   ├── test_regime.py
│   ├── test_trend_pullback.py
│   ├── test_volume_breakout.py
│   ├── test_relative_strength.py
│   ├── test_scoring.py
│   ├── test_sizing.py
│   ├── test_risk.py
│   ├── test_orders.py
│   ├── test_exits.py
│   ├── test_persistence.py
│   ├── test_no_lookahead.py
│   ├── test_notifications.py
│   ├── test_reports.py
│   └── test_dashboard.py
│
├── docs/
│   ├── architecture.md
│   ├── strategy_rules.md
│   ├── scoring.md
│   ├── risk_management.md
│   ├── order_lifecycle.md
│   ├── backtesting_methodology.md
│   ├── bias_and_limitations.md
│   ├── paper_trading_setup.md
│   ├── telegram_setup.md
│   ├── github_setup.md
│   ├── render_setup.md
│   ├── operations.md
│   ├── recovery.md
│   └── troubleshooting.md
│
└── .github/
└── workflows/
├── tests.yml
├── quantconnect-sync.yml
├── cloud-backtest.yml
├── weekly-validation.yml
└── dashboard-health.yml

GSD may refine this structure during planning.

Do not create meaningless empty files.

==================================================
PROPOSED GSD ROADMAP
====================

Use the following phases as the initial roadmap.

GSD may split a phase when it is too large for reliable execution.

Phase 1 — Foundation and Safety

* repository foundation
* project licensing
* attribution files
* Paper-only safety guard
* typed configuration
* domain models
* unit-test foundation
* minimal non-trading QCAlgorithm
* minimal Streamlit foundation
* no stock orders

Phase 2 — QuantConnect Foundation and Universe

* verify current LEAN APIs
* QuantConnect Cloud compilation
* SPY and QQQ
* benchmark indicators
* dynamic universe
* data-quality handling
* SymbolData lifecycle
* Market Regime
* universe and regime tests

Phase 3 — Trend Pullback

* setup rules
* indicator evidence
* rejection logic
* score components
* explanations
* tests
* Backtest-ready shared logic

Phase 4 — Volume Breakout

* prior-resistance logic
* current-bar exclusion
* volume confirmation
* extension checks
* score components
* explanations
* tests

Phase 5 — Relative Strength and Unified Scoring

* relative-strength calculations
* Relative Strength setup
* candidate ranking
* unified MarketPilot Score
* classification
* confidence
* explanations
* setup comparison

Phase 6 — Portfolio Risk and Order Lifecycle

* portfolio constraints
* sector exposure
* risk budgeting
* position sizing
* order state machine
* Stops
* Targets
* partial exits
* trailing exits
* maximum holding period
* restart-state model
* notification-domain events
* notification formatters
* fake transport
* deduplication
* rate limiting

Phase 7 — Backtesting and Validation

* execution realism
* fee model
* slippage models
* no-look-ahead validation
* full-period Backtest
* year-by-year results
* In-Sample
* Out-of-Sample
* Walk-Forward
* sensitivity analysis
* benchmark comparison
* activation gates
* Backtest notification previews
* reports

Phase 8 — QuantConnect Paper Trading and Telegram

* Shadow Mode
* Limited Paper Mode
* Full Approved Paper Mode
* Paper Trading deployment
* Live Trading Node setup
* order reconciliation
* restart recovery
* protective-order recovery
* official QuantConnect Telegram integration
* signal alerts
* order alerts
* fill alerts
* Stop alerts
* Target alerts
* regime alerts
* system alerts
* daily summaries
* notification quota handling

Phase 9 — Render Dashboard

* current official QuantConnect API integration
* durable custom-data exports
* Streamlit pages
* mobile responsiveness
* authentication
* caching
* stale-data handling
* Backtest versus Paper
* Telegram System Health
* system status

Phase 10 — CI/CD, Security and Release

* GitHub Actions
* Cloud Backtest workflow
* weekly validation
* dashboard health
* secret handling
* report artifacts
* end-to-end tests
* security review
* operations documentation
* recovery documentation
* final audit
* release preparation

Do not combine the entire project into one implementation phase.

==================================================
DEFINITION OF DONE
==================

The finished product must:

1. Compile in QuantConnect.
2. Run actual QuantConnect Cloud Backtests.
3. Use identical strategy rules in Backtest and Paper Trading.
4. Contain no real-money trading path.
5. Pass no-look-ahead tests.
6. Use explicit fees and slippage.
7. Produce year-by-year results.
8. Produce In-Sample and Out-of-Sample results.
9. Produce Walk-Forward or equivalent chronological validation.
10. Enforce strategy activation gates.
11. Block unapproved strategies from Paper orders.
12. Recover important Paper position state after restart.
13. Reconcile active orders.
14. Restore protective orders safely.
15. Provide a read-only mobile Render dashboard.
16. Use QuantConnect as portfolio source of truth.
17. Send BUY candidate Telegram alerts.
18. Send WATCH alerts when enabled.
19. Send Paper BUY alerts.
20. Send Paper SELL alerts.
21. Send submitted-order alerts.
22. Send partial-fill alerts.
23. Send full-fill alerts.
24. Send Stop-created alerts.
25. Send Stop-updated alerts.
26. Send Stop-triggered alerts.
27. Send Target 1 alerts.
28. Send Target 2 alerts.
29. Send partial-close alerts.
30. Send full-position-close alerts.
31. Send rejected-order alerts.
32. Send canceled-order alerts.
33. Send Market Regime transition alerts.
34. Send algorithm-start and restart alerts.
35. Send critical-error alerts.
36. Send daily Telegram summaries.
37. Suppress duplicate alerts safely.
38. Respect notification limits.
39. Continue trading logic when Telegram fails.
40. Keep Telegram disabled in normal historical Backtests.
41. Never expose secrets.
42. Pass automated tests.
43. Include operational documentation.
44. Attribute reused code.
45. Never fabricate performance results.
46. Never claim guaranteed profitability.

==================================================
