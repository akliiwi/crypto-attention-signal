# Crypto Sentiment Signal

**Does crypto market sentiment carry predictive information for short-horizon Bitcoin returns — or does price simply drive sentiment?**

This project builds a daily dataset of Bitcoin returns/volatility and the Crypto Fear & Greed Index, then tests the relationship with rolling correlations and bidirectional Granger causality. The bidirectional part is the point: the interesting and frequently honest result in this kind of data is the reverse direction — price moves drive sentiment, not the other way around.

## Motivation

There is a real academic literature on investor attention/sentiment and asset prices (e.g. Da, Engelberg & Gao, "In Search of Attention", 2011). The popular belief that retail sentiment predicts crypto moves is plausible but fragile when tested directly. This project tests it and reports what the data actually says, including null and reverse-direction results.

## What it does

1. Prices (src/fetch_prices.py) — daily BTC-USD from Yahoo Finance (no API key). Computes log returns and a 7-day realized-volatility proxy. Returns are used because price levels are non-stationary and would invalidate the tests.
2. Sentiment (src/fetch_sentiment.py) — the Crypto Fear & Greed Index from alternative.me (no API key required): a daily 0-100 market-mood gauge. The index level is the primary sentiment signal; its absolute day-over-day change is a secondary "mood shift" signal.
3. Merge (src/build_dataset.py) — inner-join on date; no forward-filling (that would fabricate observations).
4. Analysis (src/analysis.py):
   - Stationarity — Augmented Dickey-Fuller test on each series; non-stationary series are differenced before causality testing.
   - Rolling correlation — 30-day windows, summarised by how often the correlation is even moderately strong. Instability is treated as a finding, not smoothed away.
   - Granger causality, both directions — lags 1-7, reporting the fraction of lags significant rather than the single smallest p-value, with an explicit multiple-testing caveat.

## Methodology notes (read before trusting any number)

- Granger causality is not true causality. It only tests whether past values of one series improve prediction of another. The term is used in that narrow statistical sense.
- Index construction caveat. The Fear & Greed Index is itself built partly from price volatility and momentum, so it embeds some price information by construction. This means contemporaneous correlation with returns is partly mechanical — which is exactly why the lead-lag (Granger) test is the meaningful one here.
- Multiple testing. Testing 7 lags across several pairs inflates false positives. Read the fraction of lags significant, not the minimum p-value.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

No API keys or accounts are required. Price data comes from Yahoo Finance and sentiment from the alternative.me Fear & Greed endpoint, both keyless.

## Run

```bash
python run_pipeline.py
# or step by step:
python -m src.fetch_prices
python -m src.fetch_sentiment
python -m src.build_dataset
python -m src.analysis
```

Verify the analysis logic without any live data, using synthetic data with a known causal direction:

```bash
python -m tests.test_analysis_synthetic
```

This builds a series where returns drive sentiment by construction and confirms the code recovers that direction — a sanity check on the methodology and the plumbing.

## Findings (live run)

- Sample: 722 daily observations (Bitcoin price + Crypto Fear & Greed Index), aligned over the overlapping window ending 2026-06-18.
- Stationarity: Log returns, realized volatility, and the daily change in the index are stationary (ADF p < 0.05). The sentiment level is non-stationary (p ~ 0.26) — fear/greed regimes persist — so it was differenced before causality testing.
- Contemporaneous correlation: Rolling 30-day correlation between the index and next-day returns is weak and mildly negative (mean ~ -0.17), exceeding |0.3| in only ~15% of windows and never |0.5|. No stable contemporaneous relationship.
- Granger causality: Sentiment to returns was significant at 0 of 7 lags. Returns to sentiment was significant at 7 of 7 lags. The relationship runs one way: price moves drive the sentiment index, not the reverse.
- Takeaway: The Fear & Greed Index does not appear to carry information that leads Bitcoin returns; it largely reflects price action that has already occurred. This is consistent with the index's construction, and underscores why the lead-lag test matters more than contemporaneous correlation here.

## Limitations & next steps

- The Fear & Greed Index is a composite; decomposing it into its sub-signals (social, volatility, momentum) would isolate which components, if any, lead price.
- Daily resolution only; intraday data may reveal faster lead-lag structure.
- No transaction-cost / tradability analysis — this is a signal-research project, not a strategy backtest.
