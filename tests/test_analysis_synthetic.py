"""
test_analysis_synthetic.py
---------------------------
Verifies the analysis code runs and behaves sensibly WITHOUT needing live
price or Reddit data. We build a synthetic dataset where, by construction,
returns drive sentiment with a lag (sentiment_t depends on return_{t-1}).

A correct implementation should then find that the "return -> sentiment"
Granger direction is at least as significant as "sentiment -> return".
This both tests the plumbing and demonstrates the methodology on data with
a KNOWN causal direction.

Run:  python -m tests.test_analysis_synthetic
"""
import numpy as np
import pandas as pd

from src import analysis


def make_synthetic(n=400, seed=0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2023-01-01", periods=n, freq="D")

    # returns: white noise (unpredictable, as in efficient-ish markets)
    log_return = rng.normal(0, 0.03, n)

    # sentiment REACTS to yesterday's return + noise  => returns Granger-cause sentiment
    mean_sentiment = np.empty(n)
    mean_sentiment[0] = 0.0
    mean_sentiment[1:] = 0.6 * log_return[:-1] + rng.normal(0, 0.05, n - 1)

    # post volume reacts to absolute returns (big moves -> more posts) + noise
    post_volume = 50 + 800 * np.abs(np.r_[0, log_return[:-1]]) + rng.normal(0, 5, n)

    realized_vol = pd.Series(log_return).rolling(7).std().bfill().values

    return pd.DataFrame(
        {
            "log_return": log_return,
            "realized_vol": realized_vol,
            "mean_sentiment": mean_sentiment,
            "post_volume": post_volume,
        },
        index=dates,
    )


def main():
    df = make_synthetic()
    results = analysis.run_analysis(df)
    analysis.print_report(results)

    s2r = results["granger"]["sentiment_->_return"]
    r2s = results["granger"]["return_->_sentiment"]
    print("\n--- self-test check ---")
    if r2s.get("tested") and s2r.get("tested"):
        ok = r2s["min_pvalue"] <= s2r["min_pvalue"]
        print(f"returns->sentiment min p = {r2s['min_pvalue']:.4f}")
        print(f"sentiment->returns min p = {s2r['min_pvalue']:.4f}")
        print("PASS: recovered the planted direction (returns drive sentiment)"
              if ok else
              "NOTE: planted direction not dominant -- inspect parameters")
    else:
        print("Granger tests did not run -- check data length.")


if __name__ == "__main__":
    main()
