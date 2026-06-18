"""fetch_sentiment.py -- Crypto Fear & Greed Index (alternative.me), keyless."""
import os
import requests
import pandas as pd
import config

FNG_URL = "https://api.alternative.me/fng/"

def fetch_fng():
    resp = requests.get(FNG_URL, params={"limit": 0, "format": "json"}, timeout=20)
    resp.raise_for_status()
    records = resp.json()["data"]
    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["timestamp"].astype(int), unit="s")
    df["mean_sentiment"] = df["value"].astype(float)
    df = df.sort_values("date").set_index("date")
    df["post_volume"] = df["mean_sentiment"].diff().abs()
    out = df[["mean_sentiment", "post_volume"]].dropna()
    out.index.name = "date"
    return out

def main():
    os.makedirs(config.DATA_DIR, exist_ok=True)
    daily = fetch_fng()
    daily.to_csv(config.SENTIMENT_FILE)
    print(f"Collected Fear & Greed Index over {len(daily)} days "
          f"({daily.index.min().date()} to {daily.index.max().date()}).")
    print(daily.tail())

if __name__ == "__main__":
    main()
