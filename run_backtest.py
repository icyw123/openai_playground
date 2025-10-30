"""Run a sample backtest using AkShare data."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

import matplotlib.pyplot as plt

from backtest import AkshareDataProvider, Backtester
from backtest.momentum import MomentumStrategy


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the sample backtesting framework.")
    parser.add_argument("--start", help="Backtest start date (YYYYMMDD).", required=False)
    parser.add_argument("--end", help="Backtest end date (YYYYMMDD).", required=False)
    parser.add_argument(
        "--watchlist",
        nargs="*",
        default=["600519", "000858", "000333", "000651", "000001", "600036"],
        help="List of stock codes to consider.",
    )
    parser.add_argument("--initial-capital", type=float, default=1_000_000.0)
    parser.add_argument("--lookback", type=int, default=60)
    parser.add_argument("--top-n", type=int, default=3)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("backtest_equity_curve.png"),
        help="Path to save the equity curve chart.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    provider = AkshareDataProvider(start=args.start, end=args.end)
    strategy = MomentumStrategy(
        watchlist=list(args.watchlist),
        lookback=args.lookback,
        top_n=args.top_n,
    )

    backtester = Backtester(provider, strategy, initial_capital=args.initial_capital)
    result = backtester.run()

    df = result.to_dataframe()
    df.set_index("date", inplace=True)
    print(df.tail())

    plt.figure(figsize=(12, 6))
    plt.plot(df.index, df["account_value"], label="Account Value")
    plt.title("Backtest Equity Curve")
    plt.xlabel("Date")
    plt.ylabel("Account Value")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(args.output)
    print(f"Equity curve saved to {args.output.resolve()}")


if __name__ == "__main__":
    main()
