"""Example momentum strategy implementation."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .strategy import Order, Strategy, StrategyContext


@dataclass
class MomentumStrategy(Strategy):
    watchlist: List[str]
    lookback: int = 60
    top_n: int = 3

    def on_date(self, ctx: StrategyContext) -> List[Order]:
        scores = []
        for symbol in self.watchlist:
            history = ctx.get_history(symbol)
            if ctx.current_date not in history.index:
                continue
            hist = history.loc[: ctx.current_date].tail(self.lookback + 1)
            if len(hist) < self.lookback + 1:
                continue
            start_price = hist["close"].iloc[0]
            end_price = hist["close"].iloc[-1]
            if start_price <= 0:
                continue
            momentum = end_price / start_price - 1
            scores.append((symbol, momentum))

        scores.sort(key=lambda item: item[1], reverse=True)
        selected = [symbol for symbol, _ in scores[: self.top_n]]

        orders: List[Order] = []
        if not selected:
            return orders

        weight = 1.0 / len(selected)
        for symbol in selected:
            orders.append(Order(symbol=symbol, target_percent=weight))

        # Close out positions that are no longer selected.
        current_symbols = set(ctx.portfolio.positions.keys())
        for symbol in current_symbols - set(selected):
            orders.append(Order(symbol=symbol, target_percent=0.0))

        return orders
