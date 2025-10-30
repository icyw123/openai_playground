"""Portfolio and position management primitives."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Mapping, MutableMapping

import pandas as pd


@dataclass
class Position:
    """A simple container for holding information about a single position."""

    symbol: str
    quantity: float
    avg_price: float

    def market_value(self, price: float) -> float:
        return self.quantity * price


class Portfolio:
    """Tracks cash and positions for the backtest."""

    def __init__(self, cash: float) -> None:
        self.cash: float = cash
        self._positions: MutableMapping[str, Position] = {}

    @property
    def positions(self) -> Mapping[str, Position]:
        return dict(self._positions)

    def get_position(self, symbol: str) -> Position:
        if symbol not in self._positions:
            self._positions[symbol] = Position(symbol=symbol, quantity=0.0, avg_price=0.0)
        return self._positions[symbol]

    def remove_position(self, symbol: str) -> None:
        if symbol in self._positions:
            del self._positions[symbol]

    def total_value(self, price_lookup: Mapping[str, float]) -> float:
        value = self.cash
        for symbol, position in self._positions.items():
            price = price_lookup.get(symbol)
            if price is None:
                continue
            value += position.market_value(price)
        return value

    def sell(self, symbol: str, quantity: float, price: float) -> None:
        position = self.get_position(symbol)
        quantity = min(quantity, position.quantity)
        proceeds = quantity * price
        position.quantity -= quantity
        if position.quantity == 0:
            position.avg_price = 0.0
            self.remove_position(symbol)
        self.cash += proceeds

    def buy(self, symbol: str, quantity: float, price: float) -> None:
        if quantity <= 0:
            return
        cost = quantity * price
        if cost > self.cash:
            raise ValueError(
                f"Insufficient cash to buy {quantity} shares of {symbol} at {price:.2f}."
            )
        position = self.get_position(symbol)
        total_cost = position.avg_price * position.quantity + cost
        position.quantity += quantity
        position.avg_price = total_cost / position.quantity
        self.cash -= cost

    def snapshot(self) -> Dict[str, Dict[str, float]]:
        return {
            symbol: {"quantity": pos.quantity, "avg_price": pos.avg_price}
            for symbol, pos in self._positions.items()
        }

    def summary(self, price_lookup: Mapping[str, float]) -> pd.DataFrame:
        rows = []
        for symbol, position in self._positions.items():
            price = price_lookup.get(symbol, float("nan"))
            rows.append(
                {
                    "symbol": symbol,
                    "quantity": position.quantity,
                    "avg_price": position.avg_price,
                    "market_price": price,
                    "market_value": position.market_value(price) if pd.notna(price) else float("nan"),
                }
            )
        return pd.DataFrame(rows)
