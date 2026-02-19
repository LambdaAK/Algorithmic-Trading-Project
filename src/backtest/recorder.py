"""Records portfolio state and trades during a run."""

from datetime import datetime
from typing import Optional

from src.core.types import Fill, PortfolioState


class Recorder:
    """Stores equity curve (state snapshots) and trades (fills)."""

    def __init__(self) -> None:
        self._states: list[PortfolioState] = []
        self._trades: list[Fill] = []

    def record_state(self, state: PortfolioState) -> None:
        self._states.append(state)

    def record_fill(self, fill: Fill) -> None:
        self._trades.append(fill)

    @property
    def states(self) -> list[PortfolioState]:
        return self._states

    @property
    def trades(self) -> list[Fill]:
        return self._trades

    def equity_curve(self) -> list[tuple[Optional[datetime], float]]:
        """List of (timestamp, equity) for plotting. Equity as float."""
        return [(s.timestamp, float(s.equity)) for s in self._states]
