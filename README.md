# Trading Backtester — futures, stocks, forex, crypto (stablecoin-only)

## Quick run
```bash
cd /Users/rajarshi/Code/trading-backtester
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

## More examples
```bash
python run.py --asset stock --symbol QQQ
python run.py --asset future --symbol GC=F
python run.py --asset forex --symbol EURUSD=X
python run.py --asset forex           # all forex in config.py
python run.py --asset forex --strategy fx_pullback  # forex-specific only
python run.py --asset forex --strategy bb           # Bollinger only
python run.py --asset crypto --symbol ETH/USDT
python run.py --asset crypto --symbol SOL/USDC --timeframe 1h
python run.py --asset stock            # all stocks in config.py
python run.py --asset future           # all futures in config.py
python run.py --asset crypto           # all crypto in config.py
```

## Strategies
| name | file | idea | best for |
|---|---|---|---|
| `sma` | `sma_cross.py` | SMA20/50 cross | stocks/futures trend |
| `rsi` | `rsi_meanrev.py` | RSI(14) oversold/overbought | stocks bounce |
| `donchian` | `donchian_breakout.py` | 20-day high breakout / 10-day low exit | futures/FX breakout |
| `fx_pullback` | `forex_trend_pullback.py` | **forex-specific:** EMA50 trend + RSI pullback + ATR news filter + ATR trailing stop | FX daily |
| `bb` | `bollinger_meanrev.py` | Bollinger(30, 2.5σ) fade, exit at mean | FX/crypto range |

Run one: `python run.py --asset forex --strategy fx_pullback`

## Results
Every run writes a **separate timestamped file** (never overwritten):
```
results/20261007-140359_forex-EURUSDXX_all.json
```
Each file records `run_at_utc`, filters, cash/commission, and per-strategy stats.

## Layout
```
trading-backtester/
  config.py            # symbols + params (edit to add tickers)
  data_loader.py       # yfinance (stocks/futures) + ccxt (crypto)
  strategies/
    sma_cross.py       # trend: SMA20/50 cross
    rsi_meanrev.py     # mean-reversion: RSI(14)
    donchian_breakout.py    # Donchian 20/10 breakout
    forex_trend_pullback.py # FOREX-SPECIFIC: EMA+RSI pullback+ATR filter
    bollinger_meanrev.py    # Bollinger(30,2.5) fade
  data/                # cached CSVs
  results/             # one timestamped .json PER RUN (never overwritten)
  run.py               # entry point (--strategy sma|rsi|donchian|fx_pullback|bb|all)
```

## Notes
- Crypto is **stablecoin-quoted only** (`USDT/USDC/DAI/FDUSD/TUSD/USDP`). `data_loader` rejects others.
- Futures use yfinance front-month (`ES=F, NQ=F, GC=F, CL=F`).
- Forex uses yfinance spot (`EURUSD=X, GBPUSD=X, USDJPY=X, ...`). No volume feed — `Volume=0`.
  FX backtests here are price-return based, not leveraged lots — apply your lot/contract size for live sizing.
- Futures P&L here is price-return based, not leveraged notional — multiply by contract spec for real sizing.
- Always check Sharpe > 1, Max Drawdown, #Trades > 100, and test out-of-sample before live.
- Not financial advice. Paper-trade first.
