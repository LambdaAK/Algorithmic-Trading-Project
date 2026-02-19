"""Execution interface: orders in, fills out."""

from abc import ABC, abstractmethod

from src.core.types import Bar, Fill, Order


class Execution(ABC):
    """Converts orders into fills. Implementations: simulated, (later) live."""

    @abstractmethod
    def execute(self, order: Order, fill_bar: Bar) -> Fill:
        """Produce a fill for the order at the given bar (e.g. bar t+1 open)."""
        ...
