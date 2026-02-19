"""Simulated execution: fill at next bar open with fees and slippage."""

from decimal import Decimal

from src.core.types import Bar, Fill, Order, Side
from src.execution.base import Execution


class SimulatedExecution(Execution):
    """
    Simulates fills at the next bar's open price.
    Applies configurable fee (as fraction of notional) and slippage (worse price).
    """

    def __init__(
        self,
        fee_pct: Decimal = Decimal("0"),
        slippage_pct: Decimal = Decimal("0"),
    ) -> None:
        """
        fee_pct: fee as decimal of notional (e.g. 0.001 = 0.1%).
        slippage_pct: price impact as decimal (e.g. 0.0005 = 5 bps worse).
        """
        self._fee_pct = fee_pct
        self._slippage_pct = slippage_pct

    def execute(self, order: Order, fill_bar: Bar) -> Fill:
        """Fill at bar open, then apply slippage and fee."""
        base_price = fill_bar.open
        if order.side == Side.BUY:
            # Pay more: price goes up
            fill_price = base_price * (Decimal("1") + self._slippage_pct)
        else:
            # Receive less: price goes down
            fill_price = base_price * (Decimal("1") - self._slippage_pct)

        notional = order.quantity * fill_price
        fee = notional * self._fee_pct

        return Fill(
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=fill_price,
            fee=fee,
            timestamp=fill_bar.timestamp,
        )
