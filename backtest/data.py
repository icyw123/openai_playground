"""Data provider implementations for the backtesting framework."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, Iterable, Optional

import pandas as pd

try:
    import akshare as ak  # type: ignore
except ImportError as exc:  # pragma: no cover - akshare is an optional dependency during linting
    raise ImportError(
        "akshare is required to fetch market data. Install it with `pip install akshare`."
    ) from exc


@dataclass(frozen=True)
class Bar:
    """Represents a single OHLCV bar."""

    date: pd.Timestamp
    open: float
    high: float
    low: float
    close: float
    volume: float


class AkshareDataProvider:
    """Loads index and stock data from `akshare` with simple in-memory caching."""

    def __init__(
        self,
        index_symbol: str = "sh000001",
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> None:
        self._index_symbol = index_symbol
        self._start = start
        self._end = end
        self._stock_cache: Dict[str, pd.DataFrame] = {}
        self._index_data: Optional[pd.DataFrame] = None

    def get_index_data(self) -> pd.DataFrame:
        """Return the cached index data frame sorted by date."""
        if self._index_data is None:
            df = ak.index_zh_a_daily(symbol=self._index_symbol)
            df["date"] = pd.to_datetime(df["date"])
            df = df.set_index("date").sort_index()
            if self._start:
                df = df.loc[df.index >= pd.to_datetime(self._start)]
            if self._end:
                df = df.loc[df.index <= pd.to_datetime(self._end)]
            self._index_data = df
        return self._index_data

    def get_stock_data(self, symbol: str) -> pd.DataFrame:
        """Return the full history for a single stock.

        The data is cached for repeated access and normalised to a pandas DataFrame with a
        ``DatetimeIndex`` and the columns ``open``, ``high``, ``low``, ``close`` and ``volume``.
        """

        if symbol not in self._stock_cache:
            df = ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust="qfq")
            if df.empty:
                raise ValueError(f"No historical data returned for symbol {symbol}.")
            df = df.rename(
                columns={
                    "日期": "date",
                    "开盘": "open",
                    "收盘": "close",
                    "最高": "high",
                    "最低": "low",
                    "成交量": "volume",
                }
            )
            df["date"] = pd.to_datetime(df["date"])
            df = df.set_index("date").sort_index()
            self._stock_cache[symbol] = df[["open", "high", "low", "close", "volume"]]
        return self._stock_cache[symbol]

    @lru_cache(maxsize=2048)
    def get_bar(self, symbol: str, date: pd.Timestamp) -> Optional[Bar]:
        """Return the trading bar for ``symbol`` on ``date`` if it exists."""

        data = self.get_stock_data(symbol)
        if date in data.index:
            row = data.loc[date]
            return Bar(
                date=date,
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=float(row["volume"]),
            )
        return None

    def get_open_prices(self, symbols: Iterable[str], date: pd.Timestamp) -> Dict[str, float]:
        """Return the opening price for each symbol on ``date``."""

        prices: Dict[str, float] = {}
        for symbol in symbols:
            bar = self.get_bar(symbol, date)
            if bar is None:
                continue
            prices[symbol] = bar.open
        return prices

    def get_close_prices(self, symbols: Iterable[str], date: pd.Timestamp) -> Dict[str, float]:
        """Return the closing price for each symbol on ``date``."""

        prices: Dict[str, float] = {}
        for symbol in symbols:
            bar = self.get_bar(symbol, date)
            if bar is None:
                continue
            prices[symbol] = bar.close
        return prices
