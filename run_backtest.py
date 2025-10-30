"""Run a sample backtest using AkShare data."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import typer

from backtest import AkshareDataProvider, Backtester
from backtest.momentum import MomentumStrategy


app = typer.Typer(help="AkShare-based daily backtesting CLI")


@app.command()
def run(
    start: Optional[str] = typer.Option(None, help="Backtest start date (YYYYMMDD)."),
    end: Optional[str] = typer.Option(None, help="Backtest end date (YYYYMMDD)."),
    index_symbol: str = typer.Option(
        "sh000001", help="Index symbol driving the backtest calendar."
    ),
    universe_index: str = typer.Option(
        "000300", help="Index code used by the strategy to pick candidates."
    ),
    initial_capital: float = typer.Option(1_000_000.0, min=0.0),
    lookback: int = typer.Option(60, min=1),
    top_n: int = typer.Option(3, min=1),
    output: Path = typer.Option(
        Path("backtest_equity_curve.png"), help="Path to save the equity curve chart."
    ),
) -> None:
    """Execute the sample momentum backtest and save the equity curve."""

    provider = AkshareDataProvider(index_symbol=index_symbol, start=start, end=end)
    strategy = MomentumStrategy(universe_index=universe_index, lookback=lookback, top_n=top_n)

    backtester = Backtester(provider, strategy, initial_capital=initial_capital)
    result = backtester.run()

    df = result.to_dataframe()
    df.set_index("date", inplace=True)
    typer.echo(df.tail())

    plt.figure(figsize=(12, 6))
    plt.plot(df.index, df["account_value"], label="Account Value")
    plt.title("Backtest Equity Curve")
    plt.xlabel("Date")
    plt.ylabel("Account Value")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(output)
    typer.echo(f"Equity curve saved to {output.resolve()}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
