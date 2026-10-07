"""Donchian breakout: buy N-day high breakout, exit N-day low breakdown. Long-only.

Classic trend-following that works on FX/futures. Default 20/10 (shorter than
stocks' 55/20 because FX trends are shorter-lived on daily bars).
"""
from backtesting import Strategy
from backtesting.lib import crossover


def _highest(close, n):
    s = close._s if hasattr(close, "_s") else close
    import pandas as pd
    return pd.Series(s).rolling(n).max().values


def _lowest(close, n):
    import pandas as pd
    s = close._s if hasattr(close, "_s") else close
    return pd.Series(s).rolling(n).min().values


class DonchianBreakout(Strategy):
    entry_window = 20
    exit_window = 10

    def init(self):
        close = self.data.Close
        self.upper = self.I(_highest, close, self.entry_window)
        self.lower = self.I(_lowest, close, self.exit_window)

    def next(self):
        price = self.data.Close[-1]
        if not self.position and len(self.data.Close) > self.entry_window:
            if price >= self.upper[-2]:  # breakout of prior N-day high
                self.buy(size=0.95)
        elif self.position and len(self.data.Close) > self.exit_window:
            if price <= self.lower[-2]:
                self.position.close()
