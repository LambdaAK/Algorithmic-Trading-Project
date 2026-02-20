"""Dual moving average crossover: long when fast MA > slow MA, else flat."""

from collections import deque
from decimal import Decimal

from src.core.types import Bar, PortfolioState
from src.strategies.base import Strategy


class DualMAStrategy(Strategy):
    """
    Stateful strategy: long when fast SMA(close) > slow SMA(close), else flat.
    Requires slow_lookback bars before the first signal.
    """

    def __init__(
        self,
        fast_lookback: int,
        slow_lookback: int,
        size: Decimal,
    ) -> None:
        """
        fast_lookback: bars for fast MA (e.g. 10).
        slow_lookback: bars for slow MA (e.g. 30). Must be >= fast_lookback.
        size: target BTC quantity when long (positive).
        """
        if fast_lookback < 1 or slow_lookback < 1:
            raise ValueError("lookbacks must be >= 1")
        if fast_lookback >= slow_lookback:
            raise ValueError("fast_lookback must be < slow_lookback")
        self._fast = fast_lookback
        self._slow = slow_lookback
        self._size = size
        self._closes: deque[Decimal] = deque(maxlen=slow_lookback)

    def next(self, bar: Bar, state: PortfolioState) -> Decimal:
        self._closes.append(bar.close)
        if len(self._closes) < self._slow:
            return Decimal("0")
        fast_ma = sum(list(self._closes)[-self._fast :]) / self._fast
        slow_ma = sum(self._closes) / self._slow
        if fast_ma > slow_ma:
            return self._size
        return Decimal("0")
