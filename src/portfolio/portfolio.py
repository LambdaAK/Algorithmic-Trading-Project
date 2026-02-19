"""Portfolio state and fill application."""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from src.core.types import Fill, PortfolioState, Position, Side


class Portfolio:
    """Tracks cash, position, equity, and PnL. Applies fills and exposes state snapshots."""

    def __init__(self, initial_cash: Decimal) -> None:
        self._cash = initial_cash
        self._position = Position(quantity=Decimal("0"), average_price=Decimal("0"))
        self._realized_pnl = Decimal("0")

    def apply_fill(self, fill: Fill) -> None:
        """Update cash, position, and realized PnL from a fill."""
        qty = fill.quantity
        price = fill.price
        fee = fill.fee

        if fill.side == Side.BUY:
            self._cash -= qty * price + fee
            # Update position: add to long (or reduce short if we add that later)
            old_qty = self._position.quantity
            old_avg = self._position.average_price
            new_qty = old_qty + qty
            if new_qty != 0:
                new_avg = (old_qty * old_avg + qty * price) / new_qty
            else:
                new_avg = Decimal("0")
            self._position = Position(quantity=new_qty, average_price=new_avg)
        else:  # SELL
            self._cash += qty * price - fee
            # Realized PnL on the portion sold (long: sell at price, cost was average_price)
            self._realized_pnl += (price - self._position.average_price) * qty - fee
            new_qty = self._position.quantity - qty
            # Average price of remaining position unchanged when reducing
            new_avg = self._position.average_price if new_qty != 0 else Decimal("0")
            self._position = Position(quantity=new_qty, average_price=new_avg)

    def equity_at(self, price: Decimal) -> Decimal:
        """Mark-to-market equity at given price."""
        return self._cash + self._position.quantity * price

    def unrealized_pnl_at(self, price: Decimal) -> Decimal:
        """Unrealized PnL on open position at given price (long: (price - avg) * qty)."""
        if self._position.is_flat:
            return Decimal("0")
        return (price - self._position.average_price) * self._position.quantity

    def state_at(
        self,
        price: Decimal,
        timestamp: Optional[datetime] = None,
    ) -> PortfolioState:
        """Snapshot of portfolio state at given price for recording."""
        unrealized = self.unrealized_pnl_at(price)
        equity = self.equity_at(price)
        return PortfolioState(
            cash=self._cash,
            position=Position(
                quantity=self._position.quantity,
                average_price=self._position.average_price,
            ),
            equity=equity,
            realized_pnl=self._realized_pnl,
            unrealized_pnl=unrealized,
            timestamp=timestamp,
        )

    @property
    def cash(self) -> Decimal:
        return self._cash

    @property
    def position(self) -> Position:
        return self._position

    @property
    def realized_pnl(self) -> Decimal:
        return self._realized_pnl
