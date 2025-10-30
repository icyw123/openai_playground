"""Core backtesting engine."""
from __future__ import annotations

from typing import Iterable, List

import pandas as pd
from pydantic import BaseModel, Field

from .data import AkshareDataProvider
from .portfolio import Portfolio
from .strategy import Order, Strategy, StrategyContext


class BacktestResult(BaseModel):
    dates: List[pd.Timestamp] = Field(default_factory=list)
    values: List[float] = Field(default_factory=list)

    class Config:
        arbitrary_types_allowed = True

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame({"date": self.dates, "account_value": self.values})


class Backtester:
    def __init__(
        self,
        data_provider: AkshareDataProvider,
        strategy: Strategy,
        initial_capital: float = 1_000_000.0,
    ) -> None:
        self.data_provider = data_provider
        self.strategy = strategy
        self.portfolio = Portfolio(initial_capital)

    def run(self) -> BacktestResult:
        index_data = self.data_provider.get_index_data()
        index_dates = list(index_data.index)
        if len(index_dates) < 2:
            raise ValueError("Not enough index data to run the backtest.")

        account_dates: List[pd.Timestamp] = []
        account_values: List[float] = []

        for idx, current_date in enumerate(index_dates[:-1]):
            next_date = index_dates[idx + 1]

            ctx = StrategyContext(
                current_date=current_date,
                data_provider=self.data_provider,
                portfolio=self.portfolio,
            )
            orders = self.strategy.on_date(ctx)
            self._execute_orders(current_date, orders)

            next_open_prices = self.data_provider.get_open_prices(
                symbols=list(self.portfolio.positions.keys()),
                date=next_date,
            )
            portfolio_value = self.portfolio.cash
            for symbol, position in self.portfolio.positions.items():
                price = next_open_prices.get(symbol)
                if price is None:
                    # Skip valuation for symbols that do not trade on the next day.
                    continue
                portfolio_value += position.quantity * price

            account_dates.append(next_date)
            account_values.append(portfolio_value)

        return BacktestResult(dates=account_dates, values=account_values)

    def _execute_orders(self, date: pd.Timestamp, orders: Iterable[Order]) -> None:
        order_list = list(orders)
        symbols = {order.symbol for order in order_list}
        close_prices = self.data_provider.get_close_prices(symbols, date)

        if not close_prices:
            return

        # Determine current portfolio value using closing prices.
        all_symbols = set(self.portfolio.positions.keys()) | symbols
        valuation_prices = {
            **self.data_provider.get_close_prices(all_symbols, date),
        }
        total_value = self.portfolio.total_value(valuation_prices)

        for order in order_list:
            price = close_prices.get(order.symbol)
            if price is None:
                continue
            target_value = total_value * order.target_percent
            current_position = self.portfolio.positions.get(order.symbol)
            current_value = (
                current_position.quantity * price if current_position else 0.0
            )
            value_diff = target_value - current_value
            quantity = value_diff / price
            if quantity > 0:
                try:
                    self.portfolio.buy(order.symbol, quantity, price)
                except ValueError:
                    # Skip orders we cannot afford; the framework keeps running.
                    continue
            elif quantity < 0:
                self.portfolio.sell(order.symbol, -quantity, price)

