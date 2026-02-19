"""Event-driven backtest engine."""

from src.core.types import Bar, Order, Side
from src.execution.base import Execution
from src.portfolio.portfolio import Portfolio
from src.strategies.base import Strategy

from src.backtest.recorder import Recorder


def run(
    strategy: Strategy,
    portfolio: Portfolio,
    execution: Execution,
    recorder: Recorder,
    bars: list[Bar],
    symbol: str,
) -> None:
    """
    Run backtest over bars. For each bar t: apply fill from order created at t-1
    (at bar t open), record state, get target from strategy, create order to fill at t+1.
    """
    pending_order: Order | None = None

    for i, bar in enumerate(bars):
        # Fill previous order at this bar's open (order from bar t-1 fills at bar t)
        if pending_order is not None:
            fill = execution.execute(pending_order, bar)
            portfolio.apply_fill(fill)
            recorder.record_fill(fill)
            pending_order = None

        state = portfolio.state_at(bar.close, bar.timestamp)
        recorder.record_state(state)

        target = strategy.next(bar, state)
        current = portfolio.position.quantity
        delta = target - current

        if delta != 0:
            side = Side.BUY if delta > 0 else Side.SELL
            quantity = abs(delta)
            pending_order = Order(
                symbol=symbol,
                side=side,
                quantity=quantity,
                timestamp=bar.timestamp,
            )
    # Any pending_order would fill at next bar; we don't have it, so it is dropped
