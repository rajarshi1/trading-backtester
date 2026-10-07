"""FOREX-SPECIFIC: EMA trend + RSI pullback + ATR risk filter.

Logic (long-only, tuned for ranging/trending FX on daily bars):
- Trend: Close > EMA(50)  → only take longs (avoids counter-trend chop)
- Entry: RSI(14) dips below 40 (pullback in uptrend) then crosses back up
- Volatility filter: skip entries when ATR(14)/Close > max_atr_pct (news spikes)
- Exit: RSI > 60 OR ATR trailing stop (2.5x ATR from entry)

Why forex-specific:
- FX trends less persistently than equities → needs pullback entry, not raw cross
- FX leverage magnifies news spikes → ATR filter avoids CPI/NFP whipsaws
- 24h market → no gap logic, ATR stop instead of fixed %
"""
import pandas as pd
from backtesting import Strategy


def _ema(s, n):
    import pandas as pd
    ser = s._s if hasattr(s, "_s") else s
    return pd.Series(ser).ewm(span=n, adjust=False).mean().values


def _rsi(close, period=14):
    import pandas as pd
    ser = close._s if hasattr(close, "_s") else close
    c = pd.Series(ser)
    delta = c.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = -delta.clip(upper=0).rolling(period).mean()
    rs = gain / loss.replace(0, float("nan"))
    return (100 - 100 / (1 + rs)).values


def _atr(high, low, close, period=14):
    import pandas as pd
    h = pd.Series(high._s if hasattr(high, "_s") else high)
    l = pd.Series(low._s if hasattr(low, "_s") else low)
    c = pd.Series(close._s if hasattr(close, "_s") else close)
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    return tr.rolling(period).mean().values


class ForexTrendPullback(Strategy):
    ema_period = 50
    rsi_period = 14
    rsi_entry = 40      # pullback threshold (below = washed out in uptrend)
    rsi_exit = 60       # momentum restored
    atr_period = 14
    max_atr_pct = 0.015  # skip if daily ATR > 1.5% of price (news storm)
    atr_stop_mult = 2.5

    def init(self):
        self.ema = self.I(_ema, self.data.Close, self.ema_period)
        self.rsi = self.I(_rsi, self.data.Close, self.rsi_period)
        self.atr = self.I(_atr, self.data.High, self.data.Low, self.data.Close, self.atr_period)
        self.entry_atr_stop = None

    def next(self):
        price = self.data.Close[-1]
        if len(self.data.Close) < self.ema_period + 2:
            return
        atr = self.atr[-1]
        if atr != atr:  # NaN guard
            return

        if not self.position:
            uptrend = price > self.ema[-1]
            calm = (atr / price) < self.max_atr_pct
            # pullback: was below entry level, now turning up
            pulled_back = self.rsi[-2] < self.rsi_entry if len(self.rsi) > 1 else False
            turning_up = self.rsi[-1] > self.rsi[-2] if len(self.rsi) > 1 else False
            if uptrend and calm and pulled_back and turning_up:
                self.buy(size=0.95)
                self.entry_atr_stop = price - self.atr_stop_mult * atr
        else:
            # ATR trailing stop
            trail = price - self.atr_stop_mult * atr
            if trail > (self.entry_atr_stop or 0):
                self.entry_atr_stop = trail
            if price <= (self.entry_atr_stop or 0) or self.rsi[-1] > self.rsi_exit:
                self.position.close()
                self.entry_atr_stop = None
