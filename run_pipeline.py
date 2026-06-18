"""
run_pipeline.py
----------------
Runs the whole thing end to end:
    fetch prices -> fetch sentiment -> merge -> analyse

Run:  python run_pipeline.py
(No API keys required.)
"""
from src import fetch_prices, fetch_sentiment, build_dataset, analysis


def main():
    print(">> Fetching prices...")
    fetch_prices.main()
    print("\n>> Fetching Reddit sentiment...")
    fetch_sentiment.main()
    print("\n>> Building merged dataset...")
    build_dataset.main()
    print("\n>> Running analysis...")
    analysis.main()


if __name__ == "__main__":
    main()
