"""Unified data loader with disk cache in data/.

- Stocks, futures & forex: yfinance (forex: BASEXXX=X, no volume -> Volume=0)
- Crypto (stablecoin-quoted only): ccxt (default: binance, spot OHLCV)
Returns a pandas DataFrame with columns: Open, High, Low, Close, Volume
"""
from __future__ import annotations

import os
import pandas as pd

import config


DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def _flatten_yf(df: pd.DataFrame) -> pd.DataFrame:
    if hasattr(df.columns, "get_level_values") and df.columns.nlevels > 1:
        df.columns = df.columns.get_level_values(0)
    return df


def _standardize(df: pd.DataFrame) -> pd.DataFrame:
    df = _flatten_yf(df)
    # normalize case: yfinance uses Open/High/Low/Close/Volume already
    cols = {c.lower(): c for c in df.columns}
    rename = {}
    for want in ["open", "high", "low", "close", "volume"]:
        if want in cols:
            rename[cols[want]] = want.capitalize()
    df = df.rename(columns=rename)
    df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()
    df.index = pd.to_datetime(df.index)
    return df


def _cache_path(name: str) -> str:
    safe = name.replace("/", "-").replace("=", "")
    return os.path.join(DATA_DIR, f"{safe}.csv")


def load_stock(symbol: str, start: str | None = None, end: str | None = None, use_cache: bool = True) -> pd.DataFrame:
    """Load stock/ETF OHLCV via yfinance."""
    import yfinance as yf

    start = start or config.START
    end = end or config.END
    path = _cache_path(f"stock-{symbol}-{start}-{end}")
    if use_cache and os.path.exists(path):
        df = pd.read_csv(path, index_col=0, parse_dates=True)
        return df
    df = yf.download(symbol, start=start, end=end, auto_adjust=True, progress=False)
    if df.empty:
        raise RuntimeError(f"No data for stock {symbol} ({start} -> {end}). Check symbol/network.")
    df = _standardize(df)
    os.makedirs(DATA_DIR, exist_ok=True)
    df.to_csv(path)
    return df


def load_future(symbol: str, start: str | None = None, end: str | None = None, use_cache: bool = True) -> pd.DataFrame:
    """Load futures front-month continuous OHLCV via yfinance (e.g. ES=F, NQ=F, GC=F, CL=F)."""
    return load_stock(symbol, start=start, end=end, use_cache=use_cache)


def load_forex(symbol: str, start: str | None = None, end: str | None = None, use_cache: bool = True) -> pd.DataFrame:
    """Load spot FX via yfinance (e.g. EURUSD=X). FX has no volume — Volume is filled with 0."""
    import yfinance as yf

    start = start or config.START
    end = end or config.END
    path = _cache_path(f"forex-{symbol}-{start}-{end}")
    if use_cache and os.path.exists(path):
        return pd.read_csv(path, index_col=0, parse_dates=True)
    df = yf.download(symbol, start=start, end=end, auto_adjust=True, progress=False)
    if df.empty:
        raise RuntimeError(f"No data for forex {symbol} ({start} -> {end}). Check symbol/network.")
    df = _flatten_yf(df)
    cols = {c.lower(): c for c in df.columns}
    rename = {}
    for want in ["open", "high", "low", "close"]:
        if want in cols:
            rename[cols[want]] = want.capitalize()
    df = df.rename(columns=rename)
    if "Volume" not in df.columns and "volume" not in cols:
        df["Volume"] = 0.0
    elif "Volume" not in df.columns and "volume" in cols:
        df = df.rename(columns={cols["volume"]: "Volume"})
    df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()
    df.index = pd.to_datetime(df.index)
    os.makedirs(DATA_DIR, exist_ok=True)
    df.to_csv(path)
    return df


def _assert_stablecoin(symbol: str) -> str:
    """Enforce stablecoin-quoted crypto only."""
    if "/" not in symbol:
        raise ValueError(f"Crypto symbol must be BASE/QUOTE, got {symbol!r}")
    quote = symbol.split("/")[1].split(":")[0].upper()
    if quote not in config.STABLE_QUOTES:
        raise ValueError(
            f"Only stablecoin-quoted crypto allowed (quote in {sorted(config.STABLE_QUOTES)}), got {symbol!r}"
        )
    return quote


def load_crypto(
    symbol: str,
    timeframe: str | None = None,
    start: str | None = None,
    end: str | None = None,
    use_cache: bool = True,
) -> pd.DataFrame:
    """Load crypto OHLCV via ccxt. Only stablecoin-quoted pairs (e.g. BTC/USDT, SOL/USDC)."""
    import ccxt

    _assert_stablecoin(symbol)
    timeframe = timeframe or config.TIMEFRAME
    start = start or config.START
    end = end or config.END
    path = _cache_path(f"crypto-{config.EXCHANGE_ID}-{symbol}-{timeframe}-{start}-{end}")
    if use_cache and os.path.exists(path):
        return pd.read_csv(path, index_col=0, parse_dates=True)

    ex = getattr(ccxt, config.EXCHANGE_ID)({"enableRateLimit": True})
    since = int(pd.Timestamp(start).timestamp() * 1000)
    end_ms = int(pd.Timestamp(end).timestamp() * 1000)
    all_rows: list[list] = []
    while True:
        batch = ex.fetch_ohlcv(symbol, timeframe=timeframe, since=since, limit=1000)
        if not batch:
            break
        all_rows.extend(batch)
        since = batch[-1][0] + 1
        if since >= end_ms or len(batch) < 1000:
            break
    if not all_rows:
        raise RuntimeError(f"No OHLCV for {symbol} on {config.EXCHANGE_ID}. Check network/symbol.")
    df = pd.DataFrame(all_rows, columns=["ts", "Open", "High", "Low", "Close", "Volume"])
    df["ts"] = pd.to_datetime(df["ts"], unit="ms")
    df = df.set_index("ts")
    df = df[df.index <= pd.Timestamp(end)]
    df = df[["Open", "High", "Low", "Close", "Volume"]].dropna()
    os.makedirs(DATA_DIR, exist_ok=True)
    df.to_csv(path)
    return df
