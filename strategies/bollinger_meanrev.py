"""Bollinger mean-reversion: fade the bands. Long-only.

- Buy when Close crosses below lower band (oversold washout)
- Exit when Close crosses above middle (SMA) — take profit quickly, don't wait for upper
- Widened defaults (2.5σ, 30-period) to reduce whipsaws on FX/crypto

Good complement to trend strategies: wins when SMA/Donchian chop.
"""
from backtesting import Strategy
from backtesting.lib import crossover


def _sma(close, n):
    import pandas as pd
    s = close._s if hasattr(close, "_s") else close
    return pd.Series(s).rolling(n).mean().values


def _std(close, n):
    import pandas as pd
    s = close._s if hasattr(close, "_s") else close
    return pd.Series(s).rolling(n).std(ddof=0).values


class BollingerMeanRev(Strategy):
    period = 30
    mult = 2.5

    def init(self):
        self.mid = self.I(_sma, self.data.Close, self.period)
        self.sd = self.I(_std, self.data.Close, self.period)

    def next(self):
        if len(self.data.Close) < self.period + 1:
            return
        lower = self.mid[-1] - self.mult * self.sd[-1]
        prev_lower = self.mid[-2] - self.mult * self.sd[-2]
        price, prev = self.data.Close[-1], self.data.Close[-2]
        if not self.position:
            if prev > prev_lower and price <= lower:  # washout through lower band
                self.buy(size=0.95)
        else:
            if price >= self.mid[-1]:  # quick profit at the mean
                self.position.close()
