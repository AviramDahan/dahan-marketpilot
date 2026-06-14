from AlgorithmImports import QCAlgorithm, Resolution


class DahanMarketPilotFoundation(QCAlgorithm):
    """Minimal benchmark-only LEAN shell for Phase 1 compile verification."""

    def initialize(self):
        self.set_start_date(2026, 1, 1)
        self.set_end_date(2026, 1, 31)
        self.set_cash(27027.03)

        self.add_equity("SPY", Resolution.DAILY)
        self.add_equity("QQQ", Resolution.DAILY)

        self.debug("SIMULATED PAPER TRADING ONLY - NOT FINANCIAL ADVICE")
