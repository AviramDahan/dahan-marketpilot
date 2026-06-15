from AlgorithmImports import QCAlgorithm, Resolution

from marketpilot.lean_bridge import (
    LeanRuntimeBridge,
    initialize_runtime_bridge,
    map_quantconnect_bar_to_completed_bar,
)
from marketpilot.timeframes import BarTimeframe


class DahanMarketPilotRuntime(QCAlgorithm):
    """Thin QuantConnect adapter for the MarketPilot runtime bridge."""

    def initialize(self):
        self.set_start_date(2026, 1, 1)
        self.set_end_date(2026, 1, 31)
        self.set_cash(27027.03)

        self.runtime_bridge: LeanRuntimeBridge = initialize_runtime_bridge()
        self.latest_runtime_result = None
        self.latest_dashboard_export_evidence = self.runtime_bridge.export_dashboard_evidence(None)

        self.add_equity("SPY", Resolution.DAILY)
        self.add_equity("QQQ", Resolution.DAILY)
        self.add_universe(self.select_dynamic_universe)

        self.debug("SIMULATED PAPER TRADING ONLY - NOT FINANCIAL ADVICE")

    def select_dynamic_universe(self, coarse):
        return self.runtime_bridge.select_dynamic_universe(coarse)

    def on_securities_changed(self, changes):
        return self.runtime_bridge.on_securities_changed(changes)

    def on_completed_daily_bar(self, sender, bar):
        completed_bar = map_quantconnect_bar_to_completed_bar(
            bar,
            timeframe=BarTimeframe.DAILY,
            exchange_timezone="America/New_York",
            source_resolution="daily",
            is_closed=True,
        )
        symbol = getattr(bar, "Symbol", "")
        result = self.runtime_bridge.on_completed_bar(
            symbol=symbol,
            bar=completed_bar,
            setup_results=(),
            correlation_id=f"lean-{symbol}-{completed_bar.time.isoformat()}",
        )
        self.latest_runtime_result = result
        self.latest_dashboard_export_evidence = self.runtime_bridge.export_dashboard_evidence(result)
        return result
