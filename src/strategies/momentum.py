"""Momentum strategy: long when price above moving average, else flat."""

from collections import deque
from decimal import Decimal

from src.core.types import Bar, PortfolioState
from src.strategies.base import Strategy


class MomentumStrategy(Strategy):
    """
    Stateful strategy: long when close > simple moving average of close, else flat.
    Not enough history → flat.
    """

    def __init__(self, lookback: int, size: Decimal) -> None:
        """
        lookback: number of bars for the moving average.
        size: target BTC quantity when long (positive).
        """
        if lookback < 1:
            raise ValueError("lookback must be >= 1")
        self._lookback = lookback
        self._size = size
        self._closes: deque[Decimal] = deque(maxlen=lookback)

    def next(self, bar: Bar, state: PortfolioState) -> Decimal:
        self._closes.append(bar.close)
        if len(self._closes) < self._lookback:
            return Decimal("0")
        ma = sum(self._closes) / len(self._closes)
        if bar.close > ma:
            return self._size
        return Decimal("0")
