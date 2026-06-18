"""
build_dataset.py
-----------------
Merges the daily price series and the daily sentiment series into one aligned
table, ready for analysis.

Design choices worth being able to explain:
  - Inner join on date: we only keep days where BOTH price and sentiment exist.
    (Crypto trades 7 days/week, so unlike equities there is no weekend gap to
    worry about, but the inner join is still the safe default.)
  - We do NOT forward-fill sentiment. Inventing sentiment for days with no
    posts would manufacture a signal that was not really observed.

Run:  python -m src.build_dataset
"""
import pandas as pd

import config


def build() -> pd.DataFrame:
    prices = pd.read_csv(config.PRICE_FILE, index_col="date", parse_dates=True)
    sentiment = pd.read_csv(config.SENTIMENT_FILE, index_col="date", parse_dates=True)

    merged = prices.join(sentiment, how="inner").sort_index()
    merged = merged.dropna()
    return merged


def main():
    merged = build()
    merged.to_csv(config.MERGED_FILE)
    print(f"Merged dataset: {len(merged)} rows -> {config.MERGED_FILE}")
    print(merged.tail())


if __name__ == "__main__":
    main()
