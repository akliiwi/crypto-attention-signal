"""
fetch_prices.py
----------------
Pulls daily crypto price data from Yahoo Finance (no API key required) and
derives the two quantities we actually test against sentiment:

  - log_return    : log(P_t / P_{t-1})  -- stationary, the standard return measure
  - realized_vol  : rolling std of log returns (a simple volatility proxy)

Why log returns instead of raw price?
  Price levels are non-stationary (they trend/wander), which breaks the
  assumptions of correlation and Granger causality. Log returns are
  (approximately) stationary, so they are the correct series to model.

Run:  python -m src.fetch_prices
"""
import os
import numpy as np
import pandas as pd
import yfinance as yf

import config


def fetch_prices() -> pd.DataFrame:
    df = yf.download(
        config.PRICE_TICKER,
        period=config.PRICE_PERIOD,
        interval=config.PRICE_INTERVAL,
        auto_adjust=True,
        progress=False,
    )
    if df.empty:
        raise RuntimeError(
            "yfinance returned no data. Check the ticker / your connection."
        )

    # yfinance can return a MultiIndex column frame for a single ticker;
    # flatten it so we always have a plain 'Close' column.
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    out = pd.DataFrame(index=df.index)
    out["close"] = df["Close"]
    out["log_return"] = np.log(out["close"] / out["close"].shift(1))
    # 7-day rolling realized volatility (std of daily log returns)
    out["realized_vol"] = out["log_return"].rolling(7).std()

    out.index.name = "date"
    out = out.dropna()
    return out


def main():
    os.makedirs(config.DATA_DIR, exist_ok=True)
    prices = fetch_prices()
    prices.to_csv(config.PRICE_FILE)
    print(f"Saved {len(prices)} rows to {config.PRICE_FILE}")
    print(prices.tail())


if __name__ == "__main__":
    main()
