"""RSI(14) mean-reversion: buy oversold, exit overbought."""
import pandas as pd
from backtesting import Strategy


def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = -delta.clip(upper=0).rolling(period).mean()
    rs = gain / loss.replace(0, float("nan"))
    return 100 - 100 / (1 + rs)


class RsiMeanRevert(Strategy):
    rsi_period = 14
    oversold = 30
    overbought = 70

    def init(self):
        self.rsi = self.I(_rsi, pd.Series(self.data.Close), self.rsi_period)

    def next(self):
        if not self.position and self.rsi[-1] < self.oversold:
            self.buy(size=0.95)
        elif self.position and self.rsi[-1] > self.overbought:
            self.position.close()
