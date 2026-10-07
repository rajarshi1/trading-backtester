"""SMA crossover: buy when fast crosses above slow, exit on opposite cross."""
from backtesting import Strategy
from backtesting.lib import crossover
from backtesting.test import SMA


class SmaCross(Strategy):
    fast = 20
    slow = 50

    def init(self):
        self.sma_fast = self.I(SMA, self.data.Close, self.fast)
        self.sma_slow = self.I(SMA, self.data.Close, self.slow)

    def next(self):
        if crossover(self.sma_fast, self.sma_slow):
            self.buy(size=0.95)
        elif crossover(self.sma_slow, self.sma_fast):
            self.position.close()
