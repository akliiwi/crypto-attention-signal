# config.py
# Central configuration for the project. Change values here rather than
# editing the individual scripts.

# ---- Price data (yfinance) ----
PRICE_TICKER = "BTC-USD"   # any yfinance ticker, e.g. "ETH-USD"
PRICE_PERIOD = "2y"        # how far back to pull: e.g. "1y", "2y", "max"
PRICE_INTERVAL = "1d"      # bar size: "1d" daily, "1h" hourly (shorter history)

# ---- Sentiment data (Reddit via PRAW) ----
SUBREDDITS = ["Bitcoin", "CryptoCurrency"]
POSTS_PER_SUBREDDIT = 800  # PRAW caps listings near ~1000; 800 is safe

# ---- Analysis parameters ----
ROLLING_WINDOW = 30        # trading days per rolling-correlation window
MAX_LAG = 7                # max lag (days) tested in Granger causality
SIGNIFICANCE = 0.05        # p-value threshold

# ---- Paths ----
DATA_DIR = "data"
PRICE_FILE = "data/prices.csv"
SENTIMENT_FILE = "data/sentiment.csv"
MERGED_FILE = "data/merged.csv"
