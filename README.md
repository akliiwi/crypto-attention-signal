# Crypto Attention Signal

**Does social attention/sentiment carry predictive information for short-horizon Bitcoin returns and volatility — or does price simply drive the chatter?**

This project builds a daily dataset of Bitcoin returns/volatility and Reddit sentiment, then tests the relationship with rolling correlations and **bidirectional Granger causality**. The bidirectional part is the point: the interesting and frequently honest result in this kind of data is the *reverse* direction — price moves cause people to post, not the other way around.

## Motivation

There is a real academic literature on investor attention and asset prices (e.g. Da, Engelberg & Gao, *"In Search of Attention"*, 2011, using search volume; and a wave of crypto-specific follow-ups). The hypothesis that retail social activity predicts crypto moves is plausible but mostly fragile out of sample. This project tests it directly and reports what the data actually says, including null and reverse-direction results.

## What it does

1. **Prices** (`src/fetch_prices.py`) — daily BTC-USD from Yahoo Finance (no API key). Computes log returns and a 7-day realized-volatility proxy. Returns are used because price *levels* are non-stationary and would invalidate the tests.
2. **Sentiment** (`src/fetch_sentiment.py`) — recent posts from r/Bitcoin and r/CryptoCurrency via Reddit's public read-only JSON endpoints (no API key required), scored with VADER. Aggregated to a daily mean sentiment score and a daily post count (an attention proxy).
3. **Merge** (`src/build_dataset.py`) — inner-join on date; no forward-filling of sentiment (that would fabricate observations).
4. **Analysis** (`src/analysis.py`):
   - **Stationarity** — Augmented Dickey-Fuller test on each series; non-stationary series are differenced before causality testing.
   - **Rolling correlation** — 30-day windows, summarised by how *often* the correlation is even moderately strong. Instability is treated as a finding, not smoothed away.
   - **Granger causality, both directions** — lags 1–7, reporting the fraction of lags significant rather than the single smallest p-value, with an explicit multiple-testing caveat.

## Methodology notes (read before trusting any number)

- **Granger causality ≠ true causality.** It only tests whether past values of one series improve prediction of another. We use the term in that narrow statistical sense.
- **Multiple testing.** Testing 7 lags × several pairs inflates false positives. Read `frac_significant`, not the minimum p-value.
- **Reddit history is shallow.** The API returns recent posts, so the sentiment series covers a recent window, not years. A production version would log posts continuously. The sample size is reported in the output — do not overstate it.
- **VADER is generic.** It is tuned for general social media, not crypto slang ("HODL", "rekt"). A refinement would be a crypto-specific lexicon.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

No API keys or accounts are required. Price data comes from Yahoo Finance and
sentiment from Reddit's public JSON endpoints, both keyless.

## Run

```bash
python run_pipeline.py          # full pipeline end to end
# or step by step:
python -m src.fetch_prices
python -m src.fetch_sentiment
python -m src.build_dataset
python -m src.analysis
```

Verify the analysis logic without any live data or keys:

```bash
python -m tests.test_analysis_synthetic
```

This builds a synthetic series where returns drive sentiment by construction and confirms the code recovers that direction (a sanity check on the methodology and the plumbing).

## Findings

> _Fill this in after running on real data. Report what you actually observe — including weak, null, or reverse-direction results. Example structure below; replace the bracketed parts with your real numbers._

- **Sample:** [N] days, [date range], [number] of Reddit posts.
- **Stationarity:** [which series were stationary; which needed differencing].
- **Contemporaneous correlation:** sentiment vs. next-day return was [mean / how often |corr| > 0.3].
- **Granger causality:** sentiment → return significant at [x/7] lags; return → sentiment at [y/7] lags. [State which direction dominated.]
- **Takeaway:** [one honest sentence — e.g. "attention appears to follow price moves more than it predicts them."]

## Limitations & next steps

- Shallow Reddit history; would benefit from continuous collection.
- VADER → crypto-specific sentiment model.
- Daily resolution; intraday may reveal faster lead-lag structure.
- No transaction-cost / tradability analysis — this is a signal-research project, not a strategy backtest.

## Repo layout

```
crypto-attention-signal/
├── README.md
├── requirements.txt
├── config.py
├── run_pipeline.py
├── src/
│   ├── fetch_prices.py
│   ├── fetch_sentiment.py
│   ├── build_dataset.py
│   └── analysis.py
└── tests/
    └── test_analysis_synthetic.py
```
