"""
analysis.py
------------
The quantitative core. Three steps, each chosen for a reason you should be
able to defend:

1. STATIONARITY (Augmented Dickey-Fuller test)
   Correlation and Granger causality assume (roughly) stationary series.
   We test each series; non-stationary ones get differenced. Returns are
   already stationary; raw post_volume often is not.

2. ROLLING CORRELATION
   A single full-sample correlation hides how unstable the relationship is.
   We compute correlation in rolling windows and summarise the distribution
   -- in particular, how often it is even moderately strong. Instability is
   itself a finding.

3. GRANGER CAUSALITY, BOTH DIRECTIONS
   Granger causality asks: does past sentiment help predict returns beyond
   what past returns already predict? We test BOTH directions, because the
   honest and common result in this kind of data is the reverse one:
   price moves drive the chatter (returns -> sentiment), not the other way.
   Testing many lags inflates false positives, so we report the fraction of
   lags that are significant and flag the multiple-testing caveat rather than
   cherry-picking the one lag that "worked".

Run (after build_dataset):  python -m src.analysis
"""
import warnings

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller, grangercausalitytests

import config

warnings.simplefilter("ignore")  # silence statsmodels lag/verbose chatter


# ---------------------------------------------------------------- stationarity
def adf_pvalue(series: pd.Series) -> float:
    series = series.dropna()
    if series.nunique() < 5:
        return np.nan
    return adfuller(series, autolag="AIC")[1]


def make_stationary(series: pd.Series, sig: float) -> pd.Series:
    """Difference the series once if ADF cannot reject a unit root."""
    p = adf_pvalue(series)
    if np.isnan(p) or p <= sig:
        return series  # already stationary
    return series.diff().dropna()


# ----------------------------------------------------------- rolling correlation
def rolling_corr_summary(x: pd.Series, y: pd.Series, window: int) -> dict:
    rc = x.rolling(window).corr(y).dropna()
    if rc.empty:
        return {"n_windows": 0}
    return {
        "n_windows": int(rc.size),
        "mean_corr": float(rc.mean()),
        "median_corr": float(rc.median()),
        "std_corr": float(rc.std()),
        "frac_windows_abs_gt_0.3": float((rc.abs() > 0.3).mean()),
        "frac_windows_abs_gt_0.5": float((rc.abs() > 0.5).mean()),
    }


# ------------------------------------------------------------- Granger causality
def granger_pvalues(y: pd.Series, x: pd.Series, max_lag: int) -> dict:
    """
    Tests whether x Granger-causes y. statsmodels expects columns ordered
    [y, x]; the test at each lag asks if lagged x improves prediction of y.
    Returns {lag: p_value} using the SSR F-test.
    """
    data = pd.concat([y, x], axis=1).dropna()
    if len(data) < (max_lag + 5):
        return {}
    import os, sys, contextlib
    # statsmodels prints a verbose table per lag; silence it cleanly.
    with open(os.devnull, "w") as devnull, contextlib.redirect_stdout(devnull):
        res = grangercausalitytests(data.values, maxlag=max_lag)
    return {lag: res[lag][0]["ssr_ftest"][1] for lag in range(1, max_lag + 1)}


def summarise_granger(pvals: dict, sig: float) -> dict:
    if not pvals:
        return {"tested": False}
    sig_lags = [lag for lag, p in pvals.items() if p < sig]
    return {
        "tested": True,
        "n_lags": len(pvals),
        "n_significant": len(sig_lags),
        "frac_significant": len(sig_lags) / len(pvals),
        "min_pvalue": min(pvals.values()),
        "significant_lags": sig_lags,
    }


# --------------------------------------------------------------------- pipeline
def run_analysis(df: pd.DataFrame) -> dict:
    sig = config.SIGNIFICANCE

    returns = df["log_return"]
    vol = df["realized_vol"]
    sent = df["mean_sentiment"]
    volume = df["post_volume"]

    # 1. stationarity report (pre-differencing p-values)
    stationarity = {
        "log_return": adf_pvalue(returns),
        "realized_vol": adf_pvalue(vol),
        "mean_sentiment": adf_pvalue(sent),
        "post_volume": adf_pvalue(volume),
    }

    # make Granger inputs stationary
    r = make_stationary(returns, sig)
    s = make_stationary(sent, sig)
    v = make_stationary(volume, sig)
    rv = make_stationary(vol, sig)

    # 2. rolling correlations (contemporaneous)
    rolling = {
        "sentiment_vs_return": rolling_corr_summary(sent, returns, config.ROLLING_WINDOW),
        "sentiment_vs_vol": rolling_corr_summary(sent, vol, config.ROLLING_WINDOW),
        "volume_vs_vol": rolling_corr_summary(volume, vol, config.ROLLING_WINDOW),
    }

    # 3. Granger causality, both directions
    granger = {
        "sentiment_->_return": summarise_granger(granger_pvalues(r, s, config.MAX_LAG), sig),
        "return_->_sentiment": summarise_granger(granger_pvalues(s, r, config.MAX_LAG), sig),
        "volume_->_vol": summarise_granger(granger_pvalues(rv, v, config.MAX_LAG), sig),
        "vol_->_volume": summarise_granger(granger_pvalues(v, rv, config.MAX_LAG), sig),
    }

    return {"stationarity": stationarity, "rolling": rolling, "granger": granger}


def print_report(results: dict):
    print("\n=== STATIONARITY (ADF p-value; < {:.2f} => stationary) ===".format(config.SIGNIFICANCE))
    for k, p in results["stationarity"].items():
        flag = "stationary" if (not np.isnan(p) and p <= config.SIGNIFICANCE) else "NON-stationary"
        print(f"  {k:16s} p={p:.4f}  [{flag}]")

    print("\n=== ROLLING CORRELATION (window = {} days) ===".format(config.ROLLING_WINDOW))
    for k, d in results["rolling"].items():
        if d.get("n_windows", 0) == 0:
            print(f"  {k}: not enough data")
            continue
        print(f"  {k}:")
        print(f"    mean={d['mean_corr']:+.3f}  median={d['median_corr']:+.3f}  std={d['std_corr']:.3f}")
        print(f"    |corr|>0.3 in {d['frac_windows_abs_gt_0.3']*100:.0f}% of windows; "
              f"|corr|>0.5 in {d['frac_windows_abs_gt_0.5']*100:.0f}%")

    print("\n=== GRANGER CAUSALITY (lags 1..{}, sig={}) ===".format(config.MAX_LAG, config.SIGNIFICANCE))
    for k, d in results["granger"].items():
        if not d.get("tested"):
            print(f"  {k}: not tested (insufficient data)")
            continue
        print(f"  {k}: significant at {d['n_significant']}/{d['n_lags']} lags "
              f"({d['frac_significant']*100:.0f}%), min p={d['min_pvalue']:.4f}, "
              f"lags={d['significant_lags']}")
    print("\n  NOTE: testing multiple lags inflates false positives. Read the")
    print("  fraction-of-lags-significant, not the single smallest p-value.")


def main():
    df = pd.read_csv(config.MERGED_FILE, index_col="date", parse_dates=True)
    results = run_analysis(df)
    print_report(results)


if __name__ == "__main__":
    main()
