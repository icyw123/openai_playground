"""Simple daily backtesting framework backed by AkShare data."""

from .backtester import Backtester, BacktestResult
from .data import AkshareDataProvider
from .strategy import Order, Strategy, StrategyContext

__all__ = [
    "Backtester",
    "BacktestResult",
    "AkshareDataProvider",
    "Order",
    "Strategy",
    "StrategyContext",
]
