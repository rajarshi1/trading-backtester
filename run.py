"""Run backtests across stocks, futures, forex, crypto(stablecoin-only) and compare strategies.

Strategies: sma, rsi, donchian, fx_pullback (forex-specific), bb
Results: separate timestamped file per run in results/ (never overwritten).

Examples:
  python run.py                                        # defaults: SPY + ES=F + EURUSD=X + BTC/USDT
  python run.py --asset stock --symbol QQQ
  python run.py --asset future --symbol GC=F
  python run.py --asset forex --symbol EURUSD=X
  python run.py --asset forex                         # all forex in config.py
  python run.py --asset forex --strategy fx_pullback  # forex-specific only
  python run.py --asset crypto --symbol ETH/USDT --timeframe 1h
  python run.py --asset stock --symbol SPY --no-cache
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))

from backtesting import Backtest

import config
import data_loader
from strategies.sma_cross import SmaCross
from strategies.rsi_meanrev import RsiMeanRevert
from strategies.donchian_breakout import DonchianBreakout
from strategies.forex_trend_pullback import ForexTrendPullback
from strategies.bollinger_meanrev import BollingerMeanRev

STRATEGIES = {
    "sma": SmaCross,
    "rsi": RsiMeanRevert,
    "donchian": DonchianBreakout,
    "fx_pullback": ForexTrendPullback,  # forex-specific
    "bb": BollingerMeanRev,
}
# Forex runs all 5; other assets skip fx_pullback by default is False —
# actually run all everywhere so you can compare; filter with --strategy.
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")


def run_one(asset: str, symbol: str, **kwargs) -> dict:
    if asset == "stock":
        df = data_loader.load_stock(symbol, use_cache=kwargs.get("use_cache", True))
    elif asset == "future":
        df = data_loader.load_future(symbol, use_cache=kwargs.get("use_cache", True))
    elif asset == "forex":
        df = data_loader.load_forex(symbol, use_cache=kwargs.get("use_cache", True))
    elif asset == "crypto":
        df = data_loader.load_crypto(
            symbol,
            timeframe=kwargs.get("timeframe") or config.TIMEFRAME,
            use_cache=kwargs.get("use_cache", True),
        )
    else:
        raise ValueError("asset must be stock|future|forex|crypto")

    out: dict = {"asset": asset, "symbol": symbol, "bars": len(df), "strategies": {}}
    strats = kwargs.get("strategies") or STRATEGIES
    for name, cls in strats.items():
        bt = Backtest(df, cls, cash=config.CASH, commission=config.COMMISSION, exclusive_orders=True)
        stats = bt.run()
        out["strategies"][name] = {
            "Return [%]": round(float(stats["Return [%]"]), 2),
            "Sharpe Ratio": round(float(stats["Sharpe Ratio"]), 3),
            "Profit Factor": round(float(stats["Profit Factor"]) if stats["Profit Factor"] == stats["Profit Factor"] else 0, 3),
            "Max Drawdown [%]": round(float(stats["Max. Drawdown [%]"]), 2),
            "# Trades": int(stats["# Trades"]),
            "Win Rate [%]": round(float(stats["Win Rate [%]"]), 2),
        }
    return out


def main() -> None:
    p = argparse.ArgumentParser(description="Backtest stocks, futures, forex, stablecoin crypto.")
    p.add_argument("--asset", choices=["stock", "future", "forex", "crypto"], default=None)
    p.add_argument("--symbol", default=None)
    p.add_argument("--timeframe", default=config.TIMEFRAME)
    p.add_argument("--strategy", choices=list(STRATEGIES) + ["all"], default="all",
                   help="Run one strategy or all (default: all)")
    p.add_argument("--no-cache", action="store_true")
    a = p.parse_args()

    selected = STRATEGIES if a.strategy == "all" else {a.strategy: STRATEGIES[a.strategy]}

    jobs: list[tuple[str, str]] = []
    if a.asset and a.symbol:
        jobs = [(a.asset, a.symbol)]
    elif a.asset == "stock":
        jobs = [("stock", s) for s in config.STOCKS]
    elif a.asset == "future":
        jobs = [("future", s) for s in config.FUTURES]
    elif a.asset == "forex":
        jobs = [("forex", s) for s in config.FOREX]
    elif a.asset == "crypto":
        jobs = [("crypto", s) for s in config.CRYPTO_SYMBOLS]
    else:
        # default demo: one of each
        jobs = [("stock", "SPY"), ("future", "ES=F"), ("forex", "EURUSD=X"), ("crypto", "BTC/USDT")]

    all_results = []
    for asset, symbol in jobs:
        print(f"\n=== {asset.upper()} {symbol} ===")
        try:
            r = run_one(asset, symbol, timeframe=a.timeframe, use_cache=not a.no_cache,
                        strategies=selected)
        except Exception as e:
            print(f"  FAILED: {e}")
            continue
        print(f"  bars: {r['bars']}")
        for name, s in r["strategies"].items():
            print(f"  [{name}] Return {s['Return [%]']}% | Sharpe {s['Sharpe Ratio']} | "
                  f"MaxDD {s['Max Drawdown [%]']}% | Trades {s['# Trades']} | Win {s['Win Rate [%]']}%")
        all_results.append(r)

    os.makedirs(RESULTS_DIR, exist_ok=True)
    # Separate file per run: results/<UTC-timestamp>_<assets>_<strategies>.json
    # e.g. results/20261007-153000_forex-EURUSD-X_all.json — never overwrites.
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    asset_tag = a.asset or "mixed"
    if a.symbol:
        asset_tag = f"{a.asset}-{a.symbol}".replace("/", "-").replace("=", "X")
    strat_tag = a.strategy
    fname = f"{ts}_{asset_tag}_{strat_tag}.json"
    path = os.path.join(RESULTS_DIR, fname)
    payload = {
        "run_at_utc": ts,
        "asset_filter": a.asset,
        "symbol_filter": a.symbol,
        "strategy_filter": a.strategy,
        "timeframe": a.timeframe,
        "cash": config.CASH,
        "commission": config.COMMISSION,
        "results": all_results,
    }
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"\nSaved -> {path}")


if __name__ == "__main__":
    main()
