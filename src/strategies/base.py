"""Strategy interface: observe bar and portfolio, output target position."""

from abc import ABC, abstractmethod
from decimal import Decimal

from src.core.types import Bar, PortfolioState


class Strategy(ABC):
    """
    Strategy observes market data and portfolio state and outputs target position.
    Does not create or execute orders. Deterministic; may keep internal state.
    """

    @abstractmethod
    def next(self, bar: Bar, state: PortfolioState) -> Decimal:
        """
        Return target BTC position (quantity).
        Positive = long, zero = flat, negative = short.
        """
        ...
