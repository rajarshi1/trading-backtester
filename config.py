"""Central config: symbols for stocks, futures, forex, crypto (stablecoin-quoted only)."""
from __future__ import annotations

# --- Stocks (via yfinance) ---
STOCKS = [
    "SPY",   # S&P 500 ETF
    "QQQ",   # Nasdaq 100 ETF
    "AAPL",
]

# --- Futures (via yfinance continuous front-month contracts) ---
# ES=F S&P500, NQ=F Nasdaq, YM=F Dow, RTY=F Russell, GC=F Gold, SI=F Silver, CL=F Crude, NG=F NatGas
FUTURES = [
    "ES=F",
    "NQ=F",
    "GC=F",
    "CL=F",
]

# --- Forex (via yfinance spot FX, format BASEXXX=X e.g. EURUSD=X) ---
# Majors + a few crosses. yfinance FX has no Volume — loader fills Volume=0.
FOREX = [
    "EURUSD=X",  # Euro / US Dollar
    "GBPUSD=X",  # Pound / US Dollar
    "USDJPY=X",  # US Dollar / Yen
    "USDCHF=X",  # US Dollar / Swiss Franc
    "AUDUSD=X",  # Aussie / US Dollar
    "USDCAD=X",  # US Dollar / Canadian Dollar
]

# --- Crypto, STABLECOIN-QUOTED ONLY (via ccxt, default exchange: binance) ---
# Only pairs quoted in USDT / USDC / DAI / FDUSD / TUSD / USDP. No fiat, no BTC-quoted alts.
STABLE_QUOTES = {"USDT", "USDC", "DAI", "FDUSD", "TUSD", "USDP"}
CRYPTO_SYMBOLS = [
    "BTC/USDT",
    "ETH/USDT",
    "SOL/USDC",
]

EXCHANGE_ID = "binance"
TIMEFRAME = "1d"  # 1m, 5m, 1h, 4h, 1d
START = "2020-01-01"
END = "2025-01-01"

CASH = 10_000
COMMISSION = 0.001  # 0.1% per side — realistic for stocks/crypto; futures use approx
