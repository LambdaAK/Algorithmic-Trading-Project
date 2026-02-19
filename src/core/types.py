"""Core domain types for the trading system."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional


class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


@dataclass(frozen=True)
class Bar:
    """One time interval of market data."""

    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal


@dataclass
class Order:
    """Instruction to buy or sell."""

    symbol: str
    side: Side
    quantity: Decimal
    timestamp: datetime


@dataclass
class Fill:
    """Executed order."""

    symbol: str
    side: Side
    quantity: Decimal
    price: Decimal
    fee: Decimal
    timestamp: datetime


@dataclass
class Position:
    """Current BTC position. Positive = long, zero = flat, negative = short."""

    quantity: Decimal
    average_price: Decimal = Decimal("0")

    @property
    def is_flat(self) -> bool:
        return self.quantity == 0


@dataclass
class PortfolioState:
    """Snapshot of portfolio financial state."""

    cash: Decimal
    position: Position
    equity: Decimal
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    timestamp: Optional[datetime] = None
