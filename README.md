# AkShare Daily Backtesting Framework

This project contains a lightweight daily backtesting framework that pulls
market data from [AkShare](https://akshare.akfamily.xyz/) and evaluates
strategies on the Shanghai Composite Index (上证指数) trading calendar. A sample
momentum strategy is provided to demonstrate how to implement custom logic.

## Features

- Fetches index and stock data using AkShare.
- Executes strategy logic once per index trading day.
- Provides a portfolio abstraction that keeps track of cash and positions.
- Supports weight-based rebalancing decisions (`hold`, `调仓`, `开仓`, `平仓`).
- Marks positions to market using the **next day's opening price** to compute
daily floating PnL.
- Saves a chart of the backtest account value over time.

## Installation

```bash
pip install -r requirements.txt
```

Alternatively, install the dependencies directly:

```bash
pip install akshare matplotlib pandas
```

## Running the sample backtest

```bash
python run_backtest.py --start 20220101 --end 20221231 \
    --watchlist 600519 000858 000333 000651 000001 600036 \
    --initial-capital 1000000 --lookback 60 --top-n 3
```

The script prints the last few rows of the equity curve and saves the
chart to `backtest_equity_curve.png`.

## Implementing your own strategy

1. Subclass `backtest.strategy.Strategy` and implement the `on_date` method.
2. Use `StrategyContext` to access historical prices and the current
   portfolio snapshot.
3. Return a list of `Order` instances with target portfolio weights.
4. Plug your strategy into the `Backtester` class and call `run()`.

Refer to `backtest/momentum.py` for a reference implementation.
