from AlgorithmImports import QCAlgorithm, Resolution


class DahanMarketPilotFoundation(QCAlgorithm):
    """Minimal benchmark-only LEAN shell for Phase 1 compile verification."""

    def Initialize(self):
        self.SetStartDate(2026, 1, 1)
        self.SetEndDate(2026, 1, 31)
        self.SetCash(27027.03)

        self.AddEquity("SPY", Resolution.Daily)
        self.AddEquity("QQQ", Resolution.Daily)

        self.Debug("SIMULATED PAPER TRADING ONLY - NOT FINANCIAL ADVICE")
