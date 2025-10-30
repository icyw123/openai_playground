"""Data provider implementations for the backtesting framework."""
from __future__ import annotations

from functools import lru_cache
from typing import Dict, Iterable, List, Optional

import importlib.util

import pandas as pd
from pydantic import BaseModel, Field

if importlib.util.find_spec("akshare") is None:  # pragma: no cover - runtime dependency check
    raise ImportError(
        "akshare is required to fetch market data. Install it with `pip install akshare`."
    )

import akshare as ak  # type: ignore  # noqa: E402  (import after dependency check)


class Bar(BaseModel):
    """Represents a single OHLCV bar."""

    date: pd.Timestamp
    open: float = Field(..., ge=0)
    high: float = Field(..., ge=0)
    low: float = Field(..., ge=0)
    close: float = Field(..., ge=0)
    volume: float = Field(..., ge=0)

    class Config:
        arbitrary_types_allowed = True


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
        self._index_constituents: Dict[str, List[str]] = {}

    def get_index_data(self) -> pd.DataFrame:
        """Return the cached index data frame sorted by date."""
        if self._index_data is None:
            df = ak.index_zh_a_hist(symbol=self._index_symbol)

            if "日期" in df.columns:
                df = df.rename(columns={"日期": "date"})
            if "date" not in df.columns:
                raise ValueError(
                    "Unable to locate a date column in the index data returned by akshare."
                )

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

    def get_index_constituents(self, symbol: str) -> List[str]:
        """Return the list of stock codes that form the given index."""

        if symbol not in self._index_constituents:
            df = ak.index_stock_cons(symbol=symbol)
            if df.empty:
                raise ValueError(f"No constituents returned for index {symbol}.")
            code_column = None
            for candidate in ("品种代码", "股票代码", "成分券代码", "证券代码", "code"):
                if candidate in df.columns:
                    code_column = candidate
                    break
            if code_column is None:
                raise ValueError(
                    "Unable to locate a column with stock codes in the index constituents data."
                )
            codes = (
                df[code_column]
                .astype(str)
                .str.replace(".SH", "", regex=False)
                .str.replace(".SZ", "", regex=False)
                .str.zfill(6)
                .tolist()
            )
            self._index_constituents[symbol] = codes
        return self._index_constituents[symbol]

    def get_close_prices(self, symbols: Iterable[str], date: pd.Timestamp) -> Dict[str, float]:
        """Return the closing price for each symbol on ``date``."""

        prices: Dict[str, float] = {}
        for symbol in symbols:
            bar = self.get_bar(symbol, date)
            if bar is None:
                continue
            prices[symbol] = bar.close
        return prices
