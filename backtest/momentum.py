"""Example momentum strategy implementation."""
from __future__ import annotations

from typing import List

from pydantic import Field, PrivateAttr, validator

from .strategy import Order, Strategy, StrategyContext


class MomentumStrategy(Strategy):
    """Cross-sectional momentum strategy based on index constituents."""

    universe_index: str = Field("000300", description="Index code used to build the universe")
    lookback: int = Field(60, ge=1)
    top_n: int = Field(3, ge=1)

    _watchlist: List[str] = PrivateAttr(default_factory=list)

    @validator("top_n")
    def validate_top_n(cls, value: int) -> int:
        if value < 1:
            raise ValueError("top_n must be at least 1")
        return value

    def _get_watchlist(self, ctx: StrategyContext) -> List[str]:
        if not self._watchlist:
            self._watchlist = ctx.data_provider.get_index_constituents(self.universe_index)
        return self._watchlist

    def on_date(self, ctx: StrategyContext) -> List[Order]:
        scores = []
        for symbol in self._get_watchlist(ctx):
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

        current_symbols = set(ctx.portfolio.positions.keys())
        for symbol in current_symbols - set(selected):
            orders.append(Order(symbol=symbol, target_percent=0.0))

        return orders
